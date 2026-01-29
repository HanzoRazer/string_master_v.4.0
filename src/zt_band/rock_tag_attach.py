"""
Rock tag attachment layer.

Distributes bar-level technique tags onto individual NoteEvents using
deterministic heuristics. Provides two modes:

Mode A (sidecar): Returns parallel tag lists aligned 1:1 with events.
    No schema change to NoteEvent required.

Mode B (wrapped): Returns TaggedNoteEvent with embedded tags.
    Useful for transporting tags through the pipeline.

The tag selection per bar is driven by rock_articulations.sample_tags_for_bar()
and the distribution onto events uses deterministic heuristics:

- Lead expressive tags (bends/vibrato/slides) favor:
    * longer notes
    * later notes in the bar/phrase
    * higher velocity notes (more "sung")
- Right-hand drive tags (palm_mute/rake/tremolo/pick_slide) favor:
    * shorter notes
    * repeated pitches
    * attacks after rests (rake)
- Let-ring favors:
    * the longest note(s) or last note in bar
- Ghost/percussive favors:
    * short duration + low velocity notes

Usage:
    from zt_band.rock_tag_attach import (
        attach_tags_sidecar,
        attach_tags_wrapped,
        TaggedNoteEvent,
        write_technique_sidecar_json,
    )

    # Mode A - sidecar (recommended)
    comp_tags, bass_tags = attach_tags_sidecar(
        comp_events, bass_events,
        beats_per_bar=4.0,
        difficulty=Difficulty.INTERMEDIATE,
        style=RockStyle.ZEPPELIN,
        density=0.65,
        style_energy=0.8,
        leadness=0.7,
        seed=42,
    )
    # comp_tags[i] belongs to comp_events[i]
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Sequence

from .midi_out import NoteEvent
from .rock_articulations import (
    Difficulty,
    RockStyle,
    STYLE_ENERGY_TAGS,
    LEADNESS_TAGS,
    sample_tags_for_bar,
)


# =============================================================================
# TAGGED NOTE EVENT (Mode B wrapper)
# =============================================================================

@dataclass(frozen=True)
class TaggedNoteEvent:
    """Wrapper that carries technique tags alongside the original NoteEvent."""
    event: NoteEvent
    technique_tags: tuple[str, ...] = field(default_factory=tuple)


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _bar_index(start_beats: float, beats_per_bar: float) -> int:
    return int(start_beats // beats_per_bar)


def _group_by_bar(events: Sequence[NoteEvent], beats_per_bar: float) -> list[list[int]]:
    """
    Returns list of lists of indices, grouped by bar.
    """
    if not events:
        return []
    max_bar = max(_bar_index(e.start_beats, beats_per_bar) for e in events)
    groups: list[list[int]] = [[] for _ in range(max_bar + 1)]
    for i, e in enumerate(events):
        groups[_bar_index(e.start_beats, beats_per_bar)].append(i)
    return groups


def _normalize(values: list[float]) -> list[float]:
    """Normalize values to [0, 1] range within the list."""
    if not values:
        return values
    mn, mx = min(values), max(values)
    if mx - mn < 1e-9:
        return [0.5 for _ in values]
    return [(v - mn) / (mx - mn) for v in values]


def _event_features(events: Sequence[NoteEvent], idxs: list[int]) -> dict[int, dict[str, float]]:
    """
    Compute simple per-event features used for tag placement.
    Features are normalized within the bar for fair comparison.
    """
    durs = [events[i].duration_beats for i in idxs]
    vels = [events[i].velocity for i in idxs]
    starts = [events[i].start_beats for i in idxs]
    notes = [events[i].midi_note for i in idxs]

    ndurs = _normalize(durs)
    nvels = _normalize(vels)
    npos = _normalize(starts)  # within bar order-ish

    # Repetition: count occurrences of same pitch in this bar
    counts: dict[int, int] = {}
    for n in notes:
        counts[n] = counts.get(n, 0) + 1
    rep = [_normalize([counts[n] for n in notes])[k] for k in range(len(notes))]

    feats: dict[int, dict[str, float]] = {}
    for k, i in enumerate(idxs):
        feats[i] = {
            "dur": ndurs[k],     # longer -> closer to 1
            "vel": nvels[k],     # louder -> closer to 1
            "pos": npos[k],      # later -> closer to 1
            "rep": rep[k],       # more repeated pitch -> closer to 1
        }
    return feats


def _argmax_by_score(scores: dict[int, float], used: set[int]) -> int | None:
    """Find index with highest score that hasn't been used."""
    best_i = None
    best_s = -1e9
    for i, s in scores.items():
        if i in used:
            continue
        if s > best_s:
            best_s = s
            best_i = i
    return best_i


def _pick_k(scored: dict[int, float], k: int, rng: random.Random) -> list[int]:
    """
    Pick up to k distinct indices using weighted sampling from scored dict.
    """
    items = [(i, max(1e-9, s)) for i, s in scored.items()]
    chosen: list[int] = []
    for _ in range(k):
        if not items:
            break
        total = sum(w for _, w in items)
        r = rng.random() * total
        acc = 0.0
        pick_i = 0
        for j, (_, w) in enumerate(items):
            acc += w
            if acc >= r:
                pick_i = j
                break
        idx = items[pick_i][0]
        chosen.append(idx)
        items.pop(pick_i)
    return chosen


# =============================================================================
# TAG PLACEMENT HEURISTICS
# =============================================================================

def _place_bar_tags_on_events(
    events: Sequence[NoteEvent],
    idxs: list[int],
    bar_tags: list[str],
    rng: random.Random,
) -> dict[int, list[str]]:
    """
    Given indices for a single bar and the sampled bar-level tags,
    return a mapping: event_index -> list of tags assigned to that event.
    """
    assigned: dict[int, list[str]] = {i: [] for i in idxs}
    if not idxs or not bar_tags:
        return assigned

    feats = _event_features(events, idxs)
    used: set[int] = set()

    # 1) Sustain: let_ring to the longest + latest note (or chord hit)
    if "articulation.sustain.let_ring" in bar_tags:
        scores = {i: 0.65 * feats[i]["dur"] + 0.35 * feats[i]["pos"] for i in idxs}
        i_best = _argmax_by_score(scores, used)
        if i_best is not None:
            assigned[i_best].append("articulation.sustain.let_ring")
            used.add(i_best)

    # 2) Leadness tags: bends/vibrato/slides -> long + late + loud
    lead_tags = [t for t in bar_tags if t in LEADNESS_TAGS]
    for t in lead_tags:
        scores = {i: 0.45 * feats[i]["dur"] + 0.35 * feats[i]["pos"] + 0.20 * feats[i]["vel"] for i in idxs}
        i_best = _argmax_by_score(scores, used)
        if i_best is not None:
            assigned[i_best].append(t)
            used.add(i_best)

    # 3) Style-energy tags: palm mute / rake / tremolo / pick slide
    energy_tags = [t for t in bar_tags if t in STYLE_ENERGY_TAGS]

    # palm mute: short + repeated, apply to up to 2 events
    if "articulation.right_hand.palm_mute" in energy_tags:
        scores = {i: 0.55 * (1.0 - feats[i]["dur"]) + 0.45 * feats[i]["rep"] for i in idxs}
        picks = _pick_k(scores, k=min(2, len(idxs)), rng=rng)
        for i in picks:
            assigned[i].append("articulation.right_hand.palm_mute")
            used.add(i)

    # rake: attacks after gaps (approximate by "not late but accented")
    if "articulation.right_hand.rake" in energy_tags:
        scores = {i: 0.55 * feats[i]["vel"] + 0.45 * feats[i]["pos"] for i in idxs}
        i_best = _argmax_by_score(scores, used)
        if i_best is not None:
            assigned[i_best].append("articulation.right_hand.rake")
            used.add(i_best)

    # tremolo: short-to-medium duration + loud; put on one event
    if "articulation.right_hand.tremolo_pick" in energy_tags:
        scores = {i: 0.50 * feats[i]["vel"] + 0.50 * (1.0 - abs(feats[i]["dur"] - 0.5)) for i in idxs}
        i_best = _argmax_by_score(scores, used)
        if i_best is not None:
            assigned[i_best].append("articulation.right_hand.tremolo_pick")
            used.add(i_best)

    # pick slide: last loud attack (often end of bar)
    if "articulation.right_hand.pick_slide" in energy_tags:
        scores = {i: 0.60 * feats[i]["pos"] + 0.40 * feats[i]["vel"] for i in idxs}
        i_best = _argmax_by_score(scores, used)
        if i_best is not None:
            assigned[i_best].append("articulation.right_hand.pick_slide")
            used.add(i_best)

    # 4) Ghost/percussive: short + low velocity
    if "articulation.percussive.ghost_note" in bar_tags:
        scores = {i: 0.60 * (1.0 - feats[i]["vel"]) + 0.40 * (1.0 - feats[i]["dur"]) for i in idxs}
        i_best = _argmax_by_score(scores, used)
        if i_best is not None:
            assigned[i_best].append("articulation.percussive.ghost_note")
            used.add(i_best)

    if "articulation.percussive.percussive_tone" in bar_tags:
        scores = {i: 0.55 * (1.0 - feats[i]["dur"]) + 0.45 * (1.0 - feats[i]["vel"]) for i in idxs}
        i_best = _argmax_by_score(scores, used)
        if i_best is not None:
            assigned[i_best].append("articulation.percussive.percussive_tone")
            used.add(i_best)

    # 5) Any remaining tags not handled explicitly:
    # Attach them to the "most prominent" note: long+late+loud
    remaining = [t for t in bar_tags if t not in set(lead_tags + energy_tags) and t not in {
        "articulation.sustain.let_ring",
        "articulation.percussive.ghost_note",
        "articulation.percussive.percussive_tone",
    }]
    if remaining:
        scores = {i: 0.45 * feats[i]["dur"] + 0.35 * feats[i]["pos"] + 0.20 * feats[i]["vel"] for i in idxs}
        for t in remaining:
            i_best = _argmax_by_score(scores, used)
            if i_best is None:
                i_best = max(idxs)  # fallback
            assigned[i_best].append(t)
            used.add(i_best)

    # Enforce per-event max tags (keep it sane)
    for i in idxs:
        if len(assigned[i]) > 2:
            assigned[i] = assigned[i][:2]

    return assigned


# =============================================================================
# MODE A: SIDECAR TAGS
# =============================================================================

def attach_tags_sidecar(
    comp_events: Sequence[NoteEvent],
    bass_events: Sequence[NoteEvent],
    beats_per_bar: float = 4.0,
    difficulty: Difficulty = Difficulty.INTERMEDIATE,
    style: RockStyle = RockStyle.NEUTRAL,
    density: float = 0.5,
    aggression: float = 0.5,
    legato_bias: float = 0.5,
    style_energy: float = 0.5,
    leadness: float = 0.5,
    seed: int | None = None,
) -> tuple[list[list[str]], list[list[str]]]:
    """
    Non-breaking attachment: returns sidecar lists of tags aligned 1:1 with events.

    Parameters
    ----------
    comp_events : Sequence[NoteEvent]
        Comping track events.
    bass_events : Sequence[NoteEvent]
        Bass track events.
    beats_per_bar : float
        Beats per bar (default 4.0 for 4/4).
    difficulty : Difficulty
        Difficulty level for articulation gating.
    style : RockStyle
        Rock style for articulation multipliers.
    density : float
        Note density (0..1).
    aggression : float
        Aggression level (0..1).
    legato_bias : float
        Legato vs staccato bias (0..1).
    style_energy : float
        Right-hand drive intensity (0..1).
    leadness : float
        Lead expressive intensity (0..1).
    seed : int | None
        Random seed for reproducibility.

    Returns
    -------
    (comp_tags, bass_tags) : tuple[list[list[str]], list[list[str]]]
        Parallel tag lists for each track.
        comp_tags[i] is a list[str] for comp_events[i]
    """
    rng = random.Random(seed)

    comp_tags: list[list[str]] = [[] for _ in comp_events]
    bass_tags: list[list[str]] = [[] for _ in bass_events]

    # Group by bar
    comp_groups = _group_by_bar(list(comp_events), beats_per_bar)
    bass_groups = _group_by_bar(list(bass_events), beats_per_bar)

    # Process comp bars
    for bar_idx, idxs in enumerate(comp_groups):
        if not idxs:
            continue
        bar_tags = sample_tags_for_bar(
            note_count=len(idxs),
            difficulty=difficulty,
            style=style,
            density=density,
            aggression=aggression,
            legato_bias=legato_bias,
            style_energy=style_energy,
            leadness=leadness,
            seed=None if seed is None else (seed * 10000 + bar_idx * 97 + 1),
        )
        placed = _place_bar_tags_on_events(comp_events, idxs, bar_tags, rng=rng)
        for i in idxs:
            comp_tags[i] = placed.get(i, [])

    # Process bass bars (usually fewer ornaments; scale down a bit)
    for bar_idx, idxs in enumerate(bass_groups):
        if not idxs:
            continue
        bar_tags = sample_tags_for_bar(
            note_count=len(idxs),
            difficulty=difficulty,
            style=style,
            density=max(0.0, density - 0.15),  # bass is typically simpler
            aggression=aggression,
            legato_bias=legato_bias,
            style_energy=style_energy,
            leadness=max(0.0, leadness - 0.20),  # bass less "vocal"
            seed=None if seed is None else (seed * 10000 + bar_idx * 97 + 777),
        )
        placed = _place_bar_tags_on_events(bass_events, idxs, bar_tags, rng=rng)
        for i in idxs:
            bass_tags[i] = placed.get(i, [])

    return comp_tags, bass_tags


# =============================================================================
# MODE B: WRAPPED EVENTS
# =============================================================================

def attach_tags_wrapped(
    comp_events: Sequence[NoteEvent],
    bass_events: Sequence[NoteEvent],
    beats_per_bar: float = 4.0,
    difficulty: Difficulty = Difficulty.INTERMEDIATE,
    style: RockStyle = RockStyle.NEUTRAL,
    density: float = 0.5,
    aggression: float = 0.5,
    legato_bias: float = 0.5,
    style_energy: float = 0.5,
    leadness: float = 0.5,
    seed: int | None = None,
) -> tuple[list[TaggedNoteEvent], list[TaggedNoteEvent]]:
    """
    Wrapper attachment: returns TaggedNoteEvent lists while preserving NoteEvent untouched.

    Parameters
    ----------
    (Same as attach_tags_sidecar)

    Returns
    -------
    (comp_wrapped, bass_wrapped) : tuple[list[TaggedNoteEvent], list[TaggedNoteEvent]]
        Wrapped events with technique_tags field.
    """
    comp_side, bass_side = attach_tags_sidecar(
        comp_events=comp_events,
        bass_events=bass_events,
        beats_per_bar=beats_per_bar,
        difficulty=difficulty,
        style=style,
        density=density,
        aggression=aggression,
        legato_bias=legato_bias,
        style_energy=style_energy,
        leadness=leadness,
        seed=seed,
    )
    comp_wrapped = [TaggedNoteEvent(e, tuple(tags)) for e, tags in zip(comp_events, comp_side)]
    bass_wrapped = [TaggedNoteEvent(e, tuple(tags)) for e, tags in zip(bass_events, bass_side)]
    return comp_wrapped, bass_wrapped


# =============================================================================
# CONVENIENCE: EXPORT TO ANNOTATION DICT
# =============================================================================

def tags_to_annotation_list(
    events: Sequence[NoteEvent],
    tags: Sequence[list[str]],
) -> list[dict]:
    """
    Convert parallel (events, tags) to exportable annotation list.

    Returns list of dicts with only tagged events:
        [
            {"start_beats": 0.0, "technique_tags": ["articulation.right_hand.palm_mute"]},
            {"start_beats": 2.5, "technique_tags": ["articulation.left_hand.bend_half"]},
        ]
    """
    annotations = []
    for evt, tag_list in zip(events, tags):
        if tag_list:
            annotations.append({
                "start_beats": evt.start_beats,
                "duration_beats": evt.duration_beats,
                "midi_note": evt.midi_note,
                "technique_tags": list(tag_list),
            })
    return annotations


# =============================================================================
# SIDECAR JSON WRITER (no dependencies)
# =============================================================================

def sidecar_json_path(outfile: str) -> str:
    """
    Standard sidecar filename next to the MIDI output.

    Example: demo.mid -> demo.mid.technique_tags.json
    """
    return outfile + ".technique_tags.json"


def write_technique_sidecar_json(
    outfile: str,
    comp_tags: Sequence[list[str]],
    bass_tags: Sequence[list[str]],
    beats_per_bar: float = 4.0,
    meter: str = "4/4",
    version: int = 1,
    style_params: dict | None = None,
) -> str:
    """
    Write technique tag sidecar as JSON (no dependencies).

    The sidecar format maintains 1:1 alignment with events:
        comp_tags[i] aligns with comp_events[i]
        bass_tags[i] aligns with bass_events[i]

    Parameters
    ----------
    outfile : str
        Path to the MIDI file (sidecar will be named <outfile>.technique_tags.json)
    comp_tags : Sequence[list[str]]
        Parallel tag lists for comp events.
    bass_tags : Sequence[list[str]]
        Parallel tag lists for bass events.
    beats_per_bar : float
        Beats per bar (default 4.0).
    meter : str
        Time signature string (default "4/4").
    version : int
        Schema version (default 1).
    style_params : dict | None
        Optional style parameters for self-documentation.

    Returns
    -------
    str
        The written sidecar filepath.
    """
    import json
    from datetime import datetime, timezone

    payload: dict = {
        "version": int(version),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meter": meter,
        "beats_per_bar": float(beats_per_bar),
        "comp_tags": [list(t) for t in comp_tags],
        "bass_tags": [list(t) for t in bass_tags],
    }

    if style_params is not None:
        payload["style_params"] = style_params

    path = sidecar_json_path(outfile)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return path
