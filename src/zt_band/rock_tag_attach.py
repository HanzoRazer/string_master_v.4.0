"""
Rock tag attachment layer.

Distributes bar-level technique tags onto individual NoteEvents using
deterministic heuristics. Provides two modes:

Mode A (sidecar): Returns parallel tag lists aligned 1:1 with events.
    No schema change to NoteEvent required.

Mode B (wrapped): Returns TaggedNoteEvent with embedded tags.
    Useful for transporting tags through the pipeline.

Usage:
    from zt_band.rock_tag_attach import (
        attach_tags_sidecar,
        attach_tags_wrapped,
        TaggedNoteEvent,
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

    # Mode B - wrapped events
    comp_wrapped, bass_wrapped = attach_tags_wrapped(...)
"""
from __future__ import annotations

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

@dataclass
class TaggedNoteEvent:
    """Wrapper that carries technique tags alongside the original NoteEvent."""
    event: NoteEvent
    technique_tags: tuple[str, ...] = field(default_factory=tuple)


# =============================================================================
# TAG CATEGORY SETS
# =============================================================================

# Lead expressive tags - prefer long + late + loud notes
LEAD_EXPRESSIVE_TAGS = {
    "articulation.left_hand.bend_quarter",
    "articulation.left_hand.bend_half",
    "articulation.left_hand.bend_whole",
    "articulation.left_hand.bend_release",
    "articulation.modulation.vibrato_finger",
    "articulation.modulation.vibrato_wide",
    "articulation.modulation.vibrato_bar",
    "articulation.left_hand.slide_legato",
    "articulation.left_hand.slide_up",
    "articulation.left_hand.slide_down",
}

# Right-hand drive tags - distribution varies by tag
RIGHT_HAND_DRIVE_TAGS = {
    "articulation.right_hand.palm_mute",
    "articulation.right_hand.rake",
    "articulation.right_hand.tremolo_pick",
    "articulation.right_hand.pick_slide",
}

# Sustain tags - prefer longest/last note
SUSTAIN_TAGS = {
    "articulation.sustain.let_ring",
}

# Percussive tags - prefer short + low velocity
PERCUSSIVE_TAGS = {
    "articulation.dynamics.ghost_note",
    "articulation.dynamics.percussive_tone",
}

# Legato connection tags - prefer adjacent notes
LEGATO_TAGS = {
    "articulation.left_hand.hammer_on",
    "articulation.left_hand.pull_off",
}

# Max tags per single event (prevents tag spiral)
MAX_TAGS_PER_EVENT = 2


# =============================================================================
# BAR GROUPING
# =============================================================================

def _group_events_by_bar(
    events: Sequence[NoteEvent],
    beats_per_bar: float = 4.0,
) -> list[list[tuple[int, NoteEvent]]]:
    """
    Group events into bars. Returns list of bars, each bar is list of (original_index, event).
    """
    if not events:
        return []

    # Find total duration
    max_beat = max(e.start_beats + e.duration_beats for e in events)
    num_bars = int(max_beat / beats_per_bar) + 1

    bars: list[list[tuple[int, NoteEvent]]] = [[] for _ in range(num_bars)]

    for idx, event in enumerate(events):
        bar_idx = int(event.start_beats / beats_per_bar)
        bar_idx = min(bar_idx, num_bars - 1)  # Clamp to last bar
        bars[bar_idx].append((idx, event))

    return bars


# =============================================================================
# DISTRIBUTION HEURISTICS
# =============================================================================

def _score_for_lead(event: NoteEvent, bar_events: list[tuple[int, NoteEvent]]) -> float:
    """
    Score event for lead expressive tags (bends, vibrato, slides).
    Prefer: long + late + loud.
    """
    if not bar_events:
        return 0.0

    # Normalize within bar
    max_dur = max(e.duration_beats for _, e in bar_events) or 1.0
    max_vel = max(e.velocity for _, e in bar_events) or 1
    max_start = max(e.start_beats for _, e in bar_events)
    min_start = min(e.start_beats for _, e in bar_events)
    start_range = max_start - min_start or 1.0

    dur_score = event.duration_beats / max_dur
    vel_score = event.velocity / max_vel
    late_score = (event.start_beats - min_start) / start_range if start_range > 0 else 0.5

    return 0.4 * dur_score + 0.3 * late_score + 0.3 * vel_score


def _score_for_palm_mute(
    event: NoteEvent,
    bar_events: list[tuple[int, NoteEvent]],
    pitch_counts: dict[int, int],
) -> float:
    """
    Score event for palm_mute. Prefer: short + repeated pitch (riff feel).
    """
    if not bar_events:
        return 0.0

    max_dur = max(e.duration_beats for _, e in bar_events) or 1.0

    # Shorter is better for palm mute
    short_score = 1.0 - (event.duration_beats / max_dur)

    # Repeated pitch bonus
    repeat_score = min(pitch_counts.get(event.midi_note, 1) / 3.0, 1.0)

    return 0.5 * short_score + 0.5 * repeat_score


def _score_for_rake(event: NoteEvent, bar_events: list[tuple[int, NoteEvent]]) -> float:
    """
    Score event for rake. Prefer: loud + later attack.
    """
    if not bar_events:
        return 0.0

    max_vel = max(e.velocity for _, e in bar_events) or 1
    max_start = max(e.start_beats for _, e in bar_events)
    min_start = min(e.start_beats for _, e in bar_events)
    start_range = max_start - min_start or 1.0

    vel_score = event.velocity / max_vel
    late_score = (event.start_beats - min_start) / start_range if start_range > 0 else 0.5

    return 0.6 * vel_score + 0.4 * late_score


def _score_for_tremolo(event: NoteEvent, bar_events: list[tuple[int, NoteEvent]]) -> float:
    """
    Score event for tremolo_pick. Prefer: medium-short duration, loud.
    """
    if not bar_events:
        return 0.0

    max_dur = max(e.duration_beats for _, e in bar_events) or 1.0
    max_vel = max(e.velocity for _, e in bar_events) or 1

    # Medium duration is ideal (not too short, not too long)
    dur_ratio = event.duration_beats / max_dur
    dur_score = 1.0 - abs(dur_ratio - 0.4) * 2  # Peak at 40% of max
    dur_score = max(0.0, dur_score)

    vel_score = event.velocity / max_vel

    return 0.5 * dur_score + 0.5 * vel_score


def _score_for_pick_slide(event: NoteEvent, bar_events: list[tuple[int, NoteEvent]]) -> float:
    """
    Score event for pick_slide. Prefer: last loud attack in bar.
    """
    if not bar_events:
        return 0.0

    max_vel = max(e.velocity for _, e in bar_events) or 1
    max_start = max(e.start_beats for _, e in bar_events)
    min_start = min(e.start_beats for _, e in bar_events)
    start_range = max_start - min_start or 1.0

    vel_score = event.velocity / max_vel
    # Strongly prefer last event
    late_score = ((event.start_beats - min_start) / start_range) ** 2 if start_range > 0 else 0.5

    return 0.4 * vel_score + 0.6 * late_score


def _score_for_sustain(event: NoteEvent, bar_events: list[tuple[int, NoteEvent]]) -> float:
    """
    Score event for let_ring. Prefer: longest + last note.
    """
    if not bar_events:
        return 0.0

    max_dur = max(e.duration_beats for _, e in bar_events) or 1.0
    max_start = max(e.start_beats for _, e in bar_events)
    min_start = min(e.start_beats for _, e in bar_events)
    start_range = max_start - min_start or 1.0

    dur_score = event.duration_beats / max_dur
    late_score = (event.start_beats - min_start) / start_range if start_range > 0 else 0.5

    return 0.6 * dur_score + 0.4 * late_score


def _score_for_ghost(event: NoteEvent, bar_events: list[tuple[int, NoteEvent]]) -> float:
    """
    Score event for ghost_note / percussive_tone. Prefer: short + low velocity.
    """
    if not bar_events:
        return 0.0

    max_dur = max(e.duration_beats for _, e in bar_events) or 1.0
    max_vel = max(e.velocity for _, e in bar_events) or 1

    # Short and quiet
    short_score = 1.0 - (event.duration_beats / max_dur)
    quiet_score = 1.0 - (event.velocity / max_vel)

    return 0.5 * short_score + 0.5 * quiet_score


# =============================================================================
# TAG DISTRIBUTION
# =============================================================================

def _distribute_tags_in_bar(
    bar_events: list[tuple[int, NoteEvent]],
    bar_tags: list[str],
) -> dict[int, list[str]]:
    """
    Distribute bar-level tags onto specific events in the bar.
    Returns mapping of original_index -> list of tags for that event.
    """
    if not bar_events or not bar_tags:
        return {}

    # Track tags per event (keyed by original index)
    event_tags: dict[int, list[str]] = {idx: [] for idx, _ in bar_events}

    # Build pitch frequency map for palm_mute scoring
    pitch_counts: dict[int, int] = {}
    for _, evt in bar_events:
        pitch_counts[evt.midi_note] = pitch_counts.get(evt.midi_note, 0) + 1

    # Process each tag
    for tag in bar_tags:
        # Find best event for this tag
        best_idx: int | None = None
        best_score = -1.0

        for orig_idx, evt in bar_events:
            # Skip if event already has max tags
            if len(event_tags[orig_idx]) >= MAX_TAGS_PER_EVENT:
                continue

            # Score based on tag category
            if tag in LEAD_EXPRESSIVE_TAGS or tag in LEADNESS_TAGS:
                score = _score_for_lead(evt, bar_events)
            elif tag == "articulation.right_hand.palm_mute":
                score = _score_for_palm_mute(evt, bar_events, pitch_counts)
            elif tag == "articulation.right_hand.rake":
                score = _score_for_rake(evt, bar_events)
            elif tag == "articulation.right_hand.tremolo_pick":
                score = _score_for_tremolo(evt, bar_events)
            elif tag == "articulation.right_hand.pick_slide":
                score = _score_for_pick_slide(evt, bar_events)
            elif tag in SUSTAIN_TAGS:
                score = _score_for_sustain(evt, bar_events)
            elif tag in PERCUSSIVE_TAGS:
                score = _score_for_ghost(evt, bar_events)
            elif tag in LEGATO_TAGS:
                # Legato tags: prefer middle events (not first, not last)
                bar_positions = [i for i, _ in enumerate(bar_events)]
                pos = [i for i, (oi, _) in enumerate(bar_events) if oi == orig_idx][0]
                if len(bar_positions) > 2 and 0 < pos < len(bar_positions) - 1:
                    score = 0.8
                else:
                    score = 0.3
            else:
                # Default: prefer louder events
                max_vel = max(e.velocity for _, e in bar_events) or 1
                score = evt.velocity / max_vel

            if score > best_score:
                best_score = score
                best_idx = orig_idx

        # Assign tag to best event
        if best_idx is not None:
            event_tags[best_idx].append(tag)

    # Filter out empty entries
    return {k: v for k, v in event_tags.items() if v}


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
) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    """
    Attach technique tags to events using sidecar mode.

    Returns parallel tag tuples aligned 1:1 with input events:
        comp_tags[i] belongs to comp_events[i]
        bass_tags[i] belongs to bass_events[i]

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
    (comp_tags, bass_tags) : tuple[list[tuple[str, ...]], list[tuple[str, ...]]]
        Parallel tag lists for each track.
    """
    # Initialize output with empty tuples
    comp_tags: list[tuple[str, ...]] = [() for _ in comp_events]
    bass_tags: list[tuple[str, ...]] = [() for _ in bass_events]

    # Process comp track
    comp_bars = _group_events_by_bar(list(comp_events), beats_per_bar)
    for bar_idx, bar_events in enumerate(comp_bars):
        if not bar_events:
            continue

        # Sample tags for this bar
        bar_seed = (seed * 1000 + bar_idx) if seed is not None else None
        tags = sample_tags_for_bar(
            note_count=len(bar_events),
            difficulty=difficulty,
            style=style,
            density=density,
            aggression=aggression,
            legato_bias=legato_bias,
            style_energy=style_energy,
            leadness=leadness,
            seed=bar_seed,
        )

        # Distribute tags onto events
        distributed = _distribute_tags_in_bar(bar_events, tags)
        for orig_idx, event_tag_list in distributed.items():
            comp_tags[orig_idx] = tuple(event_tag_list)

    # Process bass track (typically fewer articulations)
    bass_bars = _group_events_by_bar(list(bass_events), beats_per_bar)
    for bar_idx, bar_events in enumerate(bass_bars):
        if not bar_events:
            continue

        # Bass gets reduced articulation density
        bar_seed = (seed * 2000 + bar_idx) if seed is not None else None
        tags = sample_tags_for_bar(
            note_count=len(bar_events),
            difficulty=difficulty,
            style=style,
            density=density * 0.3,  # Bass is more sparse
            aggression=aggression * 0.5,
            legato_bias=legato_bias,
            style_energy=style_energy * 0.4,
            leadness=leadness * 0.2,
            seed=bar_seed,
        )

        distributed = _distribute_tags_in_bar(bar_events, tags)
        for orig_idx, event_tag_list in distributed.items():
            bass_tags[orig_idx] = tuple(event_tag_list)

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
    Attach technique tags to events using wrapped mode.

    Returns TaggedNoteEvent wrappers with embedded tags.

    Parameters
    ----------
    (Same as attach_tags_sidecar)

    Returns
    -------
    (comp_wrapped, bass_wrapped) : tuple[list[TaggedNoteEvent], list[TaggedNoteEvent]]
        Wrapped events with technique_tags field.
    """
    comp_tags, bass_tags = attach_tags_sidecar(
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

    comp_wrapped = [
        TaggedNoteEvent(event=evt, technique_tags=tags)
        for evt, tags in zip(comp_events, comp_tags)
    ]

    bass_wrapped = [
        TaggedNoteEvent(event=evt, technique_tags=tags)
        for evt, tags in zip(bass_events, bass_tags)
    ]

    return comp_wrapped, bass_wrapped


# =============================================================================
# CONVENIENCE: EXPORT TO ANNOTATION DICT
# =============================================================================

def tags_to_annotation_list(
    events: Sequence[NoteEvent],
    tags: Sequence[tuple[str, ...]],
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
    for evt, tag_tuple in zip(events, tags):
        if tag_tuple:
            annotations.append({
                "start_beats": evt.start_beats,
                "duration_beats": evt.duration_beats,
                "midi_note": evt.midi_note,
                "technique_tags": list(tag_tuple),
            })
    return annotations
