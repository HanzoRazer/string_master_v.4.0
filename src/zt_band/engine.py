"""
Accompaniment generation engine with gravity-aware reharmonization.
"""
from __future__ import annotations

from typing import List, Tuple

from .chords import parse_chord_symbol, chord_pitches, chord_bass_pitch, Chord
from .patterns import STYLE_REGISTRY, StylePattern
from .midi_out import NoteEvent, write_midi_file
from .gravity_bridge import apply_tritone_substitutions
from .musical_contract import validate_note_events, enforce_determinism_inputs
from .expressive_layer import apply_velocity_profile
from .expressive_swing import ExpressiveSpec, apply_expressive
from .ghost_layer import GhostSpec, add_ghost_hits


def generate_accompaniment(
    chord_symbols: List[str],
    style_name: str = "swing_basic",
    tempo_bpm: int = 120,
    bars_per_chord: int = 1,
    outfile: str | None = None,
    tritone_mode: str = "none",
    tritone_strength: float = 1.0,
    tritone_seed: int | None = None,
    expressive: ExpressiveSpec | None = None,
) -> Tuple[List[NoteEvent], List[NoteEvent]]:
    """
    Generate comping + bass MIDI note events for a simple chord progression.

    Parameters
    ----------
    chord_symbols:
        List of chord symbols (e.g. ["Cmaj7", "Dm7", "G7", "Cmaj7"]).
    style_name:
        Name of the accompaniment style (see STYLE_REGISTRY).
    tempo_bpm:
        Tempo in beats per minute.
    bars_per_chord:
        Number of 4/4 bars each chord lasts.
    outfile:
        Optional path to write a MIDI file. If None, no file is written.
    tritone_mode:
        Tritone substitution behavior:
            - "none":          no substitutions
            - "all_doms":      substitute every dominant chord
            - "probabilistic": substitute dominant chords with given strength
    tritone_strength:
        Probability [0.0, 1.0] for 'probabilistic' mode.
    tritone_seed:
        Optional random seed for reproducible reharmonization patterns.

    Returns
    -------
    (comp_events, bass_events):
        Lists of NoteEvent for comping and bass tracks.
    """
    if style_name not in STYLE_REGISTRY:
        raise ValueError(f"Unknown style: {style_name}")

    style: StylePattern = STYLE_REGISTRY[style_name]

    # Parse initial chord symbols
    base_chords: List[Chord] = [parse_chord_symbol(s) for s in chord_symbols]

    # Optional tritone reharmonization
    if tritone_mode not in ("none", "all_doms", "probabilistic"):
        raise ValueError(f"Invalid tritone_mode: {tritone_mode}")

    if tritone_mode != "none":
        chords = apply_tritone_substitutions(
            base_chords,
            mode=tritone_mode,
            strength=tritone_strength,
            seed=tritone_seed,
        )
    else:
        chords = base_chords

    comp_events: List[NoteEvent] = []
    bass_events: List[NoteEvent] = []

    current_bar = 0

    for chord in chords:
        pitches = chord_pitches(chord, octave=4)
        bass_pitch = chord_bass_pitch(chord, octave=2)

        for bar_offset in range(bars_per_chord):
            bar_start_beats = (current_bar + bar_offset) * 4.0  # assume 4/4

            # Collect bar events before adding ghosts
            bar_comp_events: List[NoteEvent] = []

            # Comping hits: full chord on each hit for now
            for spec in style.comp_hits:
                for p in pitches:
                    bar_comp_events.append(
                        NoteEvent(
                            start_beats=bar_start_beats + spec.beat,
                            duration_beats=spec.length_beats,
                            midi_note=p,
                            velocity=spec.velocity,
                            channel=0,
                        )
                    )

            # Add ghost hits if style has them enabled
            if style.ghost_vel > 0 and style.ghost_steps:
                ghost_spec = GhostSpec(
                    ghost_vel=style.ghost_vel,
                    ghost_steps=style.ghost_steps,
                    ghost_len_beats=style.ghost_len_beats,
                )
                bar_comp_events = add_ghost_hits(
                    bar_comp_events,
                    chord_pitches=pitches,
                    bar_start_beats=bar_start_beats,
                    beats_per_bar=4,
                    ghost_spec=ghost_spec,
                    comp_channel=0,
                )

            comp_events.extend(bar_comp_events)

            # Bass pattern: root on pattern beats
            for beat, length, vel in style.bass_pattern:
                bass_events.append(
                    NoteEvent(
                        start_beats=bar_start_beats + beat,
                        duration_beats=length,
                        midi_note=bass_pitch,
                        velocity=vel,
                        channel=1,
                    )
                )

        current_bar += bars_per_chord

    # ---- Musical Contract Enforcement ----
    # Validate inputs: ensure determinism for probabilistic operations
    enforce_determinism_inputs(
        tritone_mode=tritone_mode,
        tritone_seed=tritone_seed,
    )

    # Validate raw generator output before expressive layer
    validate_note_events(comp_events)
    validate_note_events(bass_events)

    # ---- Expressive Layer (velocity shaping only; stability-first) ----
    comp_events = apply_velocity_profile(comp_events)
    bass_events = apply_velocity_profile(bass_events)

    # Re-validate after shaping to ensure contract still satisfied
    validate_note_events(comp_events)
    validate_note_events(bass_events)

    if outfile:
        # Apply optional expressive layer (swing/humanize) before writing
        if expressive is not None:
            comp_events = apply_expressive(comp_events, spec=expressive, tempo_bpm=tempo_bpm)
            bass_events = apply_expressive(bass_events, spec=expressive, tempo_bpm=tempo_bpm)
        write_midi_file(comp_events, bass_events, tempo_bpm=tempo_bpm, outfile=outfile)

    return comp_events, bass_events
