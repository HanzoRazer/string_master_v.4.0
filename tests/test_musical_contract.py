"""
Tests for musical contract enforcement in production engine.

Verifies the stability guarantees from musical_contract.py:
- Determinism enforcement for probabilistic operations
- Event validation (non-negative start, positive duration, valid MIDI ranges)
- Expressive layer preserves contract
"""

from __future__ import annotations

import pytest

from zt_band.musical_contract import (
    ContractViolation,
    MusicalContract,
    enforce_determinism_inputs,
    validate_note_events,
)
from zt_band.expressive_layer import apply_velocity_profile
from zt_band.midi_out import NoteEvent


def test_enforce_determinism_requires_seed_for_probabilistic():
    """Probabilistic mode without seed should raise ContractViolation."""
    with pytest.raises(ContractViolation, match="probabilistic requires tritone_seed"):
        enforce_determinism_inputs(
            tritone_mode="probabilistic",
            tritone_seed=None,
        )


def test_enforce_determinism_allows_none_mode_without_seed():
    """Non-probabilistic modes should not require seed."""
    # Should not raise
    enforce_determinism_inputs(tritone_mode="none", tritone_seed=None)
    enforce_determinism_inputs(tritone_mode="all_doms", tritone_seed=None)


def test_validate_note_events_catches_negative_start():
    """Events with negative start_beats should be rejected."""
    bad_event = NoteEvent(
        start_beats=-1.0,
        duration_beats=1.0,
        midi_note=60,
        velocity=80,
        channel=0,
    )
    with pytest.raises(ContractViolation, match="start_beats < 0"):
        validate_note_events([bad_event])


def test_validate_note_events_catches_nonpositive_duration():
    """Events with duration_beats <= 0 should be rejected."""
    bad_event = NoteEvent(
        start_beats=0.0,
        duration_beats=0.0,  # Invalid: must be positive
        midi_note=60,
        velocity=80,
        channel=0,
    )
    with pytest.raises(ContractViolation, match="duration_beats <= 0"):
        validate_note_events([bad_event])


def test_validate_note_events_catches_velocity_zero():
    """Events with velocity = 0 should be rejected (forbid_velocity_zero)."""
    bad_event = NoteEvent(
        start_beats=0.0,
        duration_beats=1.0,
        midi_note=60,
        velocity=0,  # Invalid: velocity must be > 0
        channel=0,
    )
    with pytest.raises(ContractViolation, match="velocity must be > 0"):
        validate_note_events([bad_event])


def test_validate_note_events_catches_midi_note_out_of_range():
    """Events with midi_note outside 0-127 should be rejected."""
    bad_event = NoteEvent(
        start_beats=0.0,
        duration_beats=1.0,
        midi_note=128,  # Invalid: max is 127
        velocity=80,
        channel=0,
    )
    with pytest.raises(ContractViolation, match="midi_note out of range"):
        validate_note_events([bad_event])


def test_validate_note_events_catches_channel_out_of_range():
    """Events with channel outside 0-15 should be rejected."""
    bad_event = NoteEvent(
        start_beats=0.0,
        duration_beats=1.0,
        midi_note=60,
        velocity=80,
        channel=16,  # Invalid: max is 15
    )
    with pytest.raises(ContractViolation, match="channel out of range"):
        validate_note_events([bad_event])


def test_validate_note_events_accepts_valid_events():
    """Valid events should pass validation."""
    good_events = [
        NoteEvent(0.0, 1.0, 60, 80, 0),
        NoteEvent(1.0, 2.0, 64, 90, 1),
        NoteEvent(3.0, 0.25, 67, 70, 0),
    ]
    # Should not raise
    validate_note_events(good_events)


def test_expressive_layer_preserves_contract():
    """Expressive layer should produce events that still satisfy contract."""
    events = [
        NoteEvent(0.0, 1.0, 60, 80, 0),   # downbeat
        NoteEvent(0.5, 0.5, 62, 80, 0),   # offbeat
        NoteEvent(2.0, 1.0, 64, 80, 0),   # beat 3
    ]
    
    # Apply expressive layer
    shaped_events = apply_velocity_profile(events)
    
    # Should still pass validation
    validate_note_events(shaped_events)
    
    # Verify velocities were adjusted
    assert shaped_events[0].velocity != 80  # downbeat boosted
    assert shaped_events[1].velocity != 80  # offbeat cut
    assert shaped_events[2].velocity != 80  # beat 3 boosted


def test_expressive_layer_clamps_velocity():
    """Expressive layer should clamp velocities to min/max."""
    events = [
        NoteEvent(0.0, 1.0, 60, 1, 0),    # Very low velocity
        NoteEvent(2.0, 1.0, 64, 127, 0),  # Max velocity
    ]
    
    shaped_events = apply_velocity_profile(events)
    
    # Should be clamped to [min_vel, max_vel] from profile
    for e in shaped_events:
        assert 20 <= e.velocity <= 120  # Default profile range
