"""
Accompaniment generation engine with gravity-aware reharmonization.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List, Optional, Tuple

from .chords import parse_chord_symbol, chord_pitches, chord_bass_pitch, Chord
from .patterns import STYLE_REGISTRY, StylePattern
from .midi_out import NoteEvent, write_midi_file
from .gravity_bridge import apply_tritone_substitutions
from .musical_contract import validate_note_events, enforce_determinism_inputs
from .expressive_layer import apply_velocity_profile
from .expressive_swing import ExpressiveSpec, apply_expressive
from .ghost_layer import GhostSpec, add_ghost_hits
from .velocity_contour import VelContour, apply_velocity_contour


# Velocity contour presets (must match validate.py)
_VEL_PRESETS: Dict[str, Dict[str, float]] = {
    "none": {"soft": 1.0, "strong": 1.0, "pickup": 1.0, "ghost": 1.0},
    "brazil_samba": {"soft": 0.82, "strong": 1.08, "pickup": 0.65, "ghost": 0.55},
}


def _apply_style_overrides(base: StylePattern, overrides: Dict[str, Any]) -> StylePattern:
    """
    Return a COPY of base StylePattern with whitelisted overrides applied.
    Never mutates STYLE_REGISTRY objects.

    Supports both nested YAML sugar and flat canonical fields.
    """
    updates: Dict[str, Any] = {}

    # ---- ghost hits (nested sugar) ----
    gh = overrides.get("ghost_hits") or overrides.get("ghost")
    if isinstance(gh, dict):
        if gh.get("enabled", False):
            steps = gh.get("steps")
            if isinstance(steps, (list, tuple)) and all(isinstance(x, int) for x in steps):
                updates["ghost_steps"] = tuple(steps)
            vel = gh.get("vel")
            if vel is None:
                # Default ghost velocity when enabled but not specified
                updates["ghost_vel"] = 14
            elif isinstance(vel, int):
                updates["ghost_vel"] = vel
            glb = gh.get("len_beats")
            if isinstance(glb, (int, float)):
                updates["ghost_len_beats"] = float(glb)

    # ---- ghost hits (flat canonical fields override nested) ----
    if "ghost_steps" in overrides:
        gs = overrides["ghost_steps"]
        if isinstance(gs, (list, tuple)) and all(isinstance(x, int) for x in gs):
            updates["ghost_steps"] = tuple(gs)
    if "ghost_vel" in overrides and isinstance(overrides["ghost_vel"], int):
        updates["ghost_vel"] = overrides["ghost_vel"]
    if "ghost_len_beats" in overrides and isinstance(overrides["ghost_len_beats"], (int, float)):
        updates["ghost_len_beats"] = float(overrides["ghost_len_beats"])

    # ---- velocity contour (nested sugar) ----
    vc = overrides.get("vel_contour")
    if isinstance(vc, dict) and vc.get("enabled", False):
        updates["vel_contour_enabled"] = True
        preset = vc.get("preset")
        if isinstance(preset, str):
            p = _VEL_PRESETS.get(preset.strip().lower())
            if p:
                updates["vel_contour_soft"] = p["soft"]
                updates["vel_contour_strong"] = p["strong"]
                updates["vel_contour_pickup"] = p["pickup"]
                updates["vel_contour_ghost"] = p["ghost"]
        # Explicit numeric overrides in nested dict win over preset
        for src, attr in [("soft", "vel_contour_soft"), ("strong", "vel_contour_strong"),
                          ("pickup", "vel_contour_pickup"), ("ghost", "vel_contour_ghost")]:
            if src in vc and isinstance(vc[src], (int, float)):
                updates[attr] = float(vc[src])

    # ---- velocity contour (flat canonical fields override nested) ----
    if "vel_contour_enabled" in overrides and isinstance(overrides["vel_contour_enabled"], bool):
        updates["vel_contour_enabled"] = overrides["vel_contour_enabled"]
    for k in ("vel_contour_soft", "vel_contour_strong", "vel_contour_pickup", "vel_contour_ghost"):
        if k in overrides and isinstance(overrides[k], (int, float)):
            updates[k] = float(overrides[k])

    # ---- pickup (flat only) ----
    if "pickup_beat" in overrides:
        pb = overrides["pickup_beat"]
        if pb is None or isinstance(pb, (int, float)):
            updates["pickup_beat"] = pb if pb is None else float(pb)
    if "pickup_vel" in overrides and isinstance(overrides["pickup_vel"], int):
        updates["pickup_vel"] = overrides["pickup_vel"]

    # Always return a copy (never mutate registry)
    if updates:
        return replace(base, **updates)
    # Return a copy even with no updates to guarantee immutability
    return replace(base)


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
    style_overrides: Optional[Dict[str, Any]] = None,
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
    style_overrides:
        Optional dict of style knob overrides from .ztprog config.
        Supports nested sugar (ghost_hits, vel_contour) or flat canonical fields.

    Returns
    -------
    (comp_events, bass_events):
        Lists of NoteEvent for comping and bass tracks.
    """
    if style_name not in STYLE_REGISTRY:
        raise ValueError(f"Unknown style: {style_name}")

    style: StylePattern = STYLE_REGISTRY[style_name]

    # Apply style overrides from config (never mutates registry)
    if style_overrides:
        style = _apply_style_overrides(style, style_overrides)

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

            # Apply velocity contour if style has it enabled (Brazilian "breathing")
            if style.vel_contour_enabled:
                contour = VelContour(
                    enabled=True,
                    soft_mul=style.vel_contour_soft,
                    strong_mul=style.vel_contour_strong,
                    pickup_mul=style.vel_contour_pickup,
                    ghost_mul=style.vel_contour_ghost,
                )
                # Calculate pickup and ghost step sets for this bar
                pickup_steps_set = set()
                if style.pickup_beat is not None:
                    # Convert pickup beat to 16th-note step: &4 = 3.5 -> step 14
                    pickup_step = int(style.pickup_beat * 4)
                    pickup_steps_set.add(pickup_step)
                ghost_steps_set = set(style.ghost_steps) if style.ghost_steps else set()

                # Use dispatcher: currently assumes 4/4, but ready for 2/4 styles
                bar_comp_events = apply_velocity_contour(
                    bar_comp_events,
                    meter="4/4",
                    bar_steps=16,
                    contour=contour,
                    pickup_steps=pickup_steps_set,
                    ghost_steps=ghost_steps_set,
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
