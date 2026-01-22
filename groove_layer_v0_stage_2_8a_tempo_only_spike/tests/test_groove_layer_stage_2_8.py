
import json
from groove_layer.engine import compute_groove_layer_control, GrooveStateV0

def load(p):
    with open(p) as f:
        return json.load(f)

def test_small_drift_follow():
    state = GrooveStateV0()
    out = compute_groove_layer_control(load("fixtures/vectors/08a_small_drift_follow.json"), state)
    assert out["controls"]["tempo"]["policy"] == "follow_player"

def test_large_drift_correct():
    state = GrooveStateV0()
    out = compute_groove_layer_control(load("fixtures/vectors/08b_large_drift_correct.json"), state)
    assert out["controls"]["tempo"]["policy"] == "correct_drift"
