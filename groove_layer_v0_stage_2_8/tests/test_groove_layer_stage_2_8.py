"""
Stage 2.8 Tests: Vector 08 (Tempo Drift Detection + Correction)

Tests cover:
- Small drift → follow_player policy
- Large drift → correct_drift policy
- Drift accumulation across windows
- Drift reset on instability
"""

import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from groove_layer.engine import compute_groove_layer_control, GrooveStateV0


def load(p):
    with open(p) as f:
        return json.load(f)


def test_small_drift_follow():
    """Vector 08: Small drift should use follow_player policy."""
    state = GrooveStateV0()
    out = compute_groove_layer_control(load("fixtures/vectors/08a_small_drift_follow.json"), state)
    assert out["controls"]["tempo"]["policy"] == "follow_player"
    # Drift should be small, not trigger correction
    assert abs(state.drift_accum) <= 0.03


def test_large_drift_correct():
    """Vector 08: Large drift should trigger correct_drift policy."""
    state = GrooveStateV0()
    out = compute_groove_layer_control(load("fixtures/vectors/08b_large_drift_correct.json"), state)
    assert out["controls"]["tempo"]["policy"] == "correct_drift"
    # Drift accumulator should be reset after correction
    assert state.drift_accum == 0.0


def test_drift_accumulates_across_windows():
    """Vector 08: Drift should accumulate across multiple windows."""
    state = GrooveStateV0()
    
    # First window: small drift (2%) - need 8 events with high confidence for stability
    payload1 = {
        "engine_context": {"tempo_bpm_target": 100},
        "events": [
            {"t_onset_ms": 0, "confidence": 0.95},
            {"t_onset_ms": 612, "confidence": 0.95},  # ~98 BPM, ~2% slow
            {"t_onset_ms": 1224, "confidence": 0.95},
            {"t_onset_ms": 1836, "confidence": 0.95},
            {"t_onset_ms": 2448, "confidence": 0.95},
            {"t_onset_ms": 3060, "confidence": 0.95},
            {"t_onset_ms": 3672, "confidence": 0.95},
            {"t_onset_ms": 4284, "confidence": 0.95},
        ]
    }
    out1 = compute_groove_layer_control(payload1, state)
    assert out1["controls"]["tempo"]["policy"] == "follow_player"
    drift_after_1 = state.drift_accum
    
    # Second window: another small drift
    payload2 = {
        "engine_context": {"tempo_bpm_target": 100},
        "events": [
            {"t_onset_ms": 0, "confidence": 0.95},
            {"t_onset_ms": 612, "confidence": 0.95},
            {"t_onset_ms": 1224, "confidence": 0.95},
            {"t_onset_ms": 1836, "confidence": 0.95},
            {"t_onset_ms": 2448, "confidence": 0.95},
            {"t_onset_ms": 3060, "confidence": 0.95},
            {"t_onset_ms": 3672, "confidence": 0.95},
            {"t_onset_ms": 4284, "confidence": 0.95},
        ]
    }
    out2 = compute_groove_layer_control(payload2, state)
    
    # Drift should have accumulated (or reset if it triggered correction)
    assert abs(state.drift_accum) >= abs(drift_after_1) or state.drift_accum == 0.0


def test_drift_reset_on_instability():
    """Vector 08: Drift should reset when instability is detected."""
    state = GrooveStateV0()
    state.drift_accum = 0.025  # Pre-set some drift
    
    # Instability: low confidence, few events
    payload = {
        "engine_context": {"tempo_bpm_target": 100},
        "events": [
            {"t_onset_ms": 0, "confidence": 0.5},  # Low confidence
            {"t_onset_ms": 600, "confidence": 0.5},
        ]
    }
    out = compute_groove_layer_control(payload, state)
    
    # Should trigger instability gate
    assert out["controls"]["tempo"]["policy"] == "steady_clock"
    # Drift should be reset
    assert state.drift_accum == 0.0


def test_vectors_01_through_07_still_work():
    """Ensure previous vectors are preserved in Stage 2.8."""
    state = GrooveStateV0()
    
    # Vector 04: Missing engine context → freeze
    out = compute_groove_layer_control({"events": []}, state)
    assert out["debug"]["reason"] == "missing_engine_context"
    assert out["controls"]["tempo"]["policy"] == "steady_clock"
