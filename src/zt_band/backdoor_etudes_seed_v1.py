"""
zt_backdoor_etudes_seed.py

Minimal, focused code to generate Etude 1 & Etude 2 seeds in Key of C using:
  Bars 1–4: IV -> bVII7 -> (dominant-function only, engine-chosen) -> I(variation/sustain)
  Etude 1: melody starts on scale-degree 5 (G) on beat 1 of Bar 1 (downbeat)
  Etude 2: same rhythm + same directional contour, but starts on degree 3 (E)

Repeat behavior:
  - Rhythm is frozen
  - Directional contour is preserved (up/down shape)
  - Pitch may vary ONLY via approach tones (chromatic neighbors, enclosures)
  - Articulation tags may vary (slides, grace notes, vibrato) as a sidecar

Bar 3 melodic constraint:
  - Avoid tonic pitch-class (C) entirely in melody events of Bar 3

Register constraint:
  - Soft range guardrail: melody stays within `range_span_semitones` from its chosen starting register.
    Default is 14 semitones (~9th). You can set 16 (~10th) if desired.

Outputs:
  - melody_events: list[NoteEvent]      (channel 0 by default)
  - bass_events:   list[NoteEvent]      (channel 1 by default, simple roots)
  - technique sidecars (parallel arrays): list[list[str]] for melody, bass

Integration:
  - This is intentionally self-contained and does not require changing engine.py.
  - You can call these functions from generate_accompaniment() right before return
    if style_overrides["technique_tags"]["enabled"] is set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import random

# Canonical engine dataclass + articulation/tag utilities
# Prefer relative imports when this file lives inside the package (src/zt_band).
# Fallbacks allow running the module directly in ad-hoc scripts/tests.
try:
    from .midi_out import NoteEvent
    from .rock_articulations import Difficulty, RockStyle
    from .rock_tag_attach import attach_tags_sidecar
except Exception:  # pragma: no cover
    from src.zt_band.midi_out import NoteEvent
    from src.zt_band.rock_articulations import Difficulty, RockStyle
    from src.zt_band.rock_tag_attach import attach_tags_sidecar

# -----------------------------
# Pitch helpers (Key of C)
# -----------------------------

# Scale degrees in C major: 1=C,2=D,3=E,4=F,5=G,6=A,7=B
DEGREE_TO_PC_C_MAJOR = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}  # pitch classes
PC_C = 0

def pc_to_midi(pc: int, octave: int) -> int:
    """pc: 0..11, octave where C4=60 is octave=4."""
    return (octave + 1) * 12 + pc

def midi_to_pc(m: int) -> int:
    return m % 12

def clamp(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x

# -----------------------------
# Harmonic map (Key of C)
# -----------------------------

def backdoor_bars_C(rng: random.Random) -> List[str]:
    """
    Bars 1-4 chord symbols.
      Bar 1: IV     -> F
      Bar 2: bVII7  -> Bb7
      Bar 3: dominant-function only (engine-chosen) -> {G7, D7, A7}
      Bar 4: I      -> C (variation handled downstream)
    """
    bar3 = rng.choice(["G7", "D7", "A7"])
    return ["F", "Bb7", bar3, "C"]

def chord_root_midi_C(symbol: str, octave: int = 2) -> int:
    """
    Minimal chord-root mapping for the bass seed.
    """
    sym = symbol.strip()
    roots = {
        "C": 0, "C6": 0, "Cmaj7": 0,
        "F": 5,
        "Bb7": 10, "Bb": 10,
        "G7": 7, "G": 7,
        "D7": 2, "D": 2,
        "A7": 9, "A": 9,
    }
    pc = roots.get(sym, 0)
    return pc_to_midi(pc, octave)

# -----------------------------
# Rhythm + contour seed
# -----------------------------

def default_rhythm_4bars() -> List[Tuple[float, float]]:
    """
    Fixed rhythm pattern across 4 bars in 4/4.
    Returns (start_beats, duration_beats) in absolute beats.
    Total = 16 beats.
    """
    return [
        # Bar 1
        (0.0, 0.5), (0.5, 0.5), (1.0, 1.0), (2.0, 0.5), (2.5, 0.5), (3.0, 1.0),
        # Bar 2
        (4.0, 0.5), (4.5, 0.5), (5.0, 1.0), (6.0, 0.5), (6.5, 0.5), (7.0, 1.0),
        # Bar 3
        (8.0, 0.5), (8.5, 0.5), (9.0, 1.0), (10.0, 0.5), (10.5, 0.5), (11.0, 1.0),
        # Bar 4
        (12.0, 0.5), (12.5, 0.5), (13.0, 1.0), (14.0, 0.5), (14.5, 0.5), (15.0, 1.0),
    ]

# Fixed melodic DNA: semitone offsets from the opening pitch.
# All variation now comes from approach tones and articulation tags only.
MOTIVIC_OFFSETS_SEMITONES: List[int] = [
    0, +1, 0, +3, +2, +3,      # Bar 1: neighbor, m3 color
    +7, +8, +7, +5, +4, +5,    # Bar 2: call/response
    +4, -2, -3, -2, -3, -2,    # Bar 3: dominant hover
    -3, -4, -3, -5, -3, -3,    # Bar 4: resolution color
]

# -----------------------------
# Melody generation with constraints
# -----------------------------

def choose_start_octave(rng: random.Random) -> int:
    """
    Degree-relative: choose register by octave.
    For guitar-ish mid-register, use octave 4 or 5 for melody (C4=60).
    """
    return rng.choice([4, 5])

def degree_to_midi_C(degree: int, octave: int) -> int:
    pc = DEGREE_TO_PC_C_MAJOR[degree]
    return pc_to_midi(pc, octave)

def nearest_in_range(target: int, lo: int, hi: int) -> int:
    if lo <= target <= hi:
        return target
    best = target
    best_dist = 10**9
    for k in range(-4, 5):
        cand = target + 12 * k
        if lo <= cand <= hi:
            dist = abs(cand - target)
            if dist < best_dist:
                best, best_dist = cand, dist
    return clamp(best, lo, hi)

def build_melody_seed(
    start_degree: int,
    rhythm: List[Tuple[float, float]],
    rng: random.Random,
    range_span_semitones: int = 14,   # ~9th (default)
    avoid_tonic_pc_in_bar3: bool = True,
) -> List[NoteEvent]:
    """
    4-bar seed melody using fixed MOTIVIC_OFFSETS_SEMITONES:
      - downbeat of bar 1 forced to start_degree
      - fixed semitone offsets from opening pitch (no random contour)
      - soft register constraint around the starting pitch
      - bar 3 tonic PC avoidance (C pc=0)
    """
    assert len(rhythm) == len(MOTIVIC_OFFSETS_SEMITONES)

    start_oct = choose_start_octave(rng)
    start_midi = degree_to_midi_C(start_degree, start_oct)

    lo = start_midi - range_span_semitones
    hi = start_midi + range_span_semitones

    events: List[NoteEvent] = []

    for (st, dur), off in zip(rhythm, MOTIVIC_OFFSETS_SEMITONES):
        midi = nearest_in_range(start_midi + off, lo, hi)

        if avoid_tonic_pc_in_bar3 and (8.0 <= st < 12.0) and midi_to_pc(midi) == PC_C:
            midi += 1 if off >= 0 else -1
            midi = nearest_in_range(midi, lo, hi)
            if midi_to_pc(midi) == PC_C:
                midi += 2 if off >= 0 else -2
                midi = nearest_in_range(midi, lo, hi)

        events.append(NoteEvent(
            start_beats=st,
            duration_beats=dur,
            midi_note=midi,
            velocity=86,
            channel=0,
        ))

    return events


def build_melody_seed_pc(
    start_pc: int,
    rhythm: List[Tuple[float, float]],
    rng: random.Random,
    range_span_semitones: int = 14,   # ~9th (default)
    avoid_tonic_pc_in_bar3: bool = True,
    opening_neighbor_on_and_of_1: bool = True,
) -> List[NoteEvent]:
    """
    Like build_melody_seed, but the forced opening pitch is given as a pitch-class (0-11).
    Used for numeric-degree extensions like b7 (Bb=10) without expanding degree maps.
    Uses fixed MOTIVIC_OFFSETS_SEMITONES for melodic DNA.

    opening_neighbor_on_and_of_1:
      - If True, the first non-downbeat event at start_beats=0.5 ("& of 1")
        is nudged to a chromatic neighbor of the opening pitch (conversational feel)
        while keeping the downbeat pitch intact.
    """
    assert len(rhythm) == len(MOTIVIC_OFFSETS_SEMITONES)

    start_oct = choose_start_octave(rng)
    start_midi = pc_to_midi(start_pc % 12, start_oct)

    lo = start_midi - range_span_semitones
    hi = start_midi + range_span_semitones

    events: List[NoteEvent] = []

    for (st, dur), off in zip(rhythm, MOTIVIC_OFFSETS_SEMITONES):
        midi = nearest_in_range(start_midi + off, lo, hi)

        # Optional conversational neighbor on "& of 1" (st == 0.5)
        if opening_neighbor_on_and_of_1 and abs(st - 0.5) < 1e-9:
            midi = nearest_in_range(start_midi + rng.choice([-1, +1]), lo, hi)

        # Bar 3 tonic PC avoidance (C)
        if avoid_tonic_pc_in_bar3 and (8.0 <= st < 12.0) and midi_to_pc(midi) == PC_C:
            midi += 1 if off >= 0 else -1
            midi = nearest_in_range(midi, lo, hi)
            if midi_to_pc(midi) == PC_C:
                midi += 2 if off >= 0 else -2
                midi = nearest_in_range(midi, lo, hi)

        events.append(NoteEvent(
            start_beats=st,
            duration_beats=dur,
            midi_note=midi,
            velocity=86,
            channel=0,
        ))

    return events

# -----------------------------
# Micro-variation (approach tones only) on repeat
# -----------------------------

def add_approach_tones(
    events: List[NoteEvent],
    rng: random.Random,
    prob: float = 0.35,
    max_inserts_per_bar: int = 1,
) -> List[NoteEvent]:
    """
    Insert chromatic neighbor approach notes by splitting a note's duration.
    - Preserves rhythm grid feel; does not change overall contour direction meaningfully.
    - Skips the forced first downbeat note.
    """
    if not events:
        return events

    def bar_of(ev: NoteEvent) -> int:
        return int(ev.start_beats // 4.0)

    inserts_used = {0: 0, 1: 0, 2: 0, 3: 0}
    out: List[NoteEvent] = []

    for ev in events:
        b = bar_of(ev)
        is_forced_start = abs(ev.start_beats - 0.0) < 1e-9

        if (
            not is_forced_start
            and inserts_used.get(b, 0) < max_inserts_per_bar
            and rng.random() < prob
            and ev.duration_beats >= 0.5
        ):
            a_dur = 0.25
            t_dur = ev.duration_beats - a_dur
            if t_dur < 0.25:
                out.append(ev)
                continue

            direction = rng.choice([-1, +1])
            a_note = ev.midi_note + direction

            out.append(NoteEvent(
                start_beats=ev.start_beats,
                duration_beats=a_dur,
                midi_note=a_note,
                velocity=max(40, ev.velocity - 18),
                channel=ev.channel,
            ))
            out.append(NoteEvent(
                start_beats=ev.start_beats + a_dur,
                duration_beats=t_dur,
                midi_note=ev.midi_note,
                velocity=ev.velocity,
                channel=ev.channel,
            ))
            inserts_used[b] = inserts_used.get(b, 0) + 1
        else:
            out.append(ev)

    return out

# -----------------------------
# Bass seed
# -----------------------------

def build_bass_roots(chords: List[str], octave: int = 2) -> List[NoteEvent]:
    """
    Root-per-bar bass seed (4 beats sustain per bar).
    """
    bass: List[NoteEvent] = []
    beat = 0.0
    for sym in chords:
        root = chord_root_midi_C(sym, octave=octave)
        bass.append(NoteEvent(
            start_beats=beat,
            duration_beats=4.0,
            midi_note=root,
            velocity=78,
            channel=1,
        ))
        beat += 4.0
    return bass

# -----------------------------
# Public API: Etude 1 & 2
# -----------------------------

def generate_etude_pair_C_backdoor_seed(
    repeats: int = 2,
    range_span_semitones: int = 14,          # 14 ~ 9th (default), 16 ~ 10th
    technique_tags_enabled: bool = True,
    tag_density: float = 0.55,
    tag_difficulty: Difficulty = Difficulty.INTERMEDIATE,
    tag_style: RockStyle = RockStyle.NEUTRAL,
    tag_aggression: float = 0.25,
    tag_legato_bias: float = 0.70,
    tag_style_energy: float = 0.20,
    tag_leadness: float = 0.85,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Returns:
      {
        "etude_1": {"chords": [...], "melody_events": [...], "bass_events": [...], "melody_tags": [...], "bass_tags": [...]},
        "etude_2": {...}
      }

    Notes:
      - Etude 1 and Etude 2 evolve independently (separate RNG streams)
      - If seed is None, each call is probabilistic (micro-variation per render)
    """
    master = random.Random(seed)

    rhythm = default_rhythm_4bars()

    def _offset_events(evs: List[NoteEvent], offset: float) -> List[NoteEvent]:
        return [
            NoteEvent(
                start_beats=e.start_beats + offset,
                duration_beats=e.duration_beats,
                midi_note=e.midi_note,
                velocity=e.velocity,
                channel=e.channel,
            )
            for e in evs
        ]

    def _one_etude(start_degree: int, rng: random.Random) -> Dict[str, Any]:
        chords = backdoor_bars_C(rng)
        bass_base = build_bass_roots(chords)

        base_seed = build_melody_seed(
            start_degree=start_degree,
            rhythm=rhythm,
            rng=rng,
            range_span_semitones=range_span_semitones,
            avoid_tonic_pc_in_bar3=True,
        )

        melody: List[NoteEvent] = []
        bass: List[NoteEvent] = []

        for r in range(repeats):
            offset = 16.0 * r  # 4 bars * 4 beats
            if r == 0:
                seg = base_seed
            else:
                seg = add_approach_tones(base_seed, rng=rng, prob=0.35, max_inserts_per_bar=1)
            melody.extend(_offset_events(seg, offset))
            bass.extend(_offset_events(bass_base, offset))

        out: Dict[str, Any] = {"chords": chords, "melody_events": melody, "bass_events": bass}

        if technique_tags_enabled:
            comp_tags, bass_tags = attach_tags_sidecar(
                comp_events=melody,
                bass_events=bass,
                beats_per_bar=4.0,
                difficulty=tag_difficulty,
                style=tag_style,
                density=tag_density,
                aggression=tag_aggression,
                legato_bias=tag_legato_bias,
                style_energy=tag_style_energy,
                leadness=tag_leadness,
                seed=None if seed is None else (seed * 10007 + start_degree * 131),
            )
            out["melody_tags"] = comp_tags
            out["bass_tags"] = bass_tags



        return out

    def _one_etude_pc(start_pc: int, rng: random.Random) -> Dict[str, Any]:
        chords = backdoor_bars_C(rng)
        bass_base = build_bass_roots(chords)

        base_seed = build_melody_seed_pc(
            start_pc=start_pc,
            rhythm=rhythm,
            rng=rng,
            range_span_semitones=range_span_semitones,
            avoid_tonic_pc_in_bar3=True,
            opening_neighbor_on_and_of_1=True,  # "approachable" conversational start
        )

        melody: List[NoteEvent] = []
        bass: List[NoteEvent] = []

        for r in range(repeats):
            offset = 16.0 * r
            if r == 0:
                seg = base_seed
            else:
                seg = add_approach_tones(base_seed, rng=rng, prob=0.35, max_inserts_per_bar=1)
            melody.extend(_offset_events(seg, offset))
            bass.extend(_offset_events(bass_base, offset))

        out: Dict[str, Any] = {"chords": chords, "melody_events": melody, "bass_events": bass}

        if technique_tags_enabled:
            comp_tags, bass_tags = attach_tags_sidecar(
                comp_events=melody,
                bass_events=bass,
                beats_per_bar=4.0,
                difficulty=tag_difficulty,
                style=tag_style,
                density=tag_density,
                aggression=tag_aggression,
                legato_bias=tag_legato_bias,
                style_energy=tag_style_energy,
                leadness=tag_leadness,
                seed=None if seed is None else (seed * 10007 + start_pc * 197),
            )
            out["melody_tags"] = comp_tags
            out["bass_tags"] = bass_tags
        return out

    # Independent evolution across etudes:
    e1_rng = random.Random(master.randint(0, 2**31 - 1))
    e2_rng = random.Random(master.randint(0, 2**31 - 1))
    e3_rng = random.Random(master.randint(0, 2**31 - 1))

    return {"etude_1": _one_etude(5, e1_rng), "etude_2": _one_etude(3, e2_rng), "etude_3": _one_etude_pc(10, e3_rng)}
