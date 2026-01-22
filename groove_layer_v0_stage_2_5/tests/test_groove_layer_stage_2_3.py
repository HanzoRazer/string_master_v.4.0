import json
from groove_layer.engine import compute_groove_layer_control, GrooveStateV0

def load(p):
    with open(p) as f:
        return json.load(f)

def test_vector_01():
    payload = load("fixtures/vectors/01_stable_follow_player.json")
    out = compute_groove_layer_control(payload)
    assert out["controls"]["tempo"]["policy"] == "follow_player"

def test_vector_02():
    payload = load("fixtures/vectors/02_unstable_reduce_density_micro_loop.json")
    out = compute_groove_layer_control(payload)
    assert out["controls"]["loop"]["policy"] == "micro_loop"
    assert out["controls"]["arrangement"]["density_target"] == "sparse"

def test_vector_03_recovery_first_window_deescalates_to_loop_section():
    payload = load("fixtures/vectors/03_recovery_exit_loop.json")
    state = GrooveStateV0(last_loop_policy="micro_loop", last_density="sparse", stable_windows=0)
    out = compute_groove_layer_control(payload, state=state)
    assert out["controls"]["loop"]["policy"] == "loop_section"
    assert out["controls"]["arrangement"]["density_target"] == "medium"

def test_vector_03_recovery_second_window_exits_loop():
    payload = load("fixtures/vectors/03_recovery_exit_loop.json")
    state = GrooveStateV0(last_loop_policy="micro_loop", last_density="sparse", stable_windows=1)
    out = compute_groove_layer_control(payload, state=state)
    assert out["controls"]["loop"]["policy"] == "none"

def test_vector_04():
    payload = load("fixtures/vectors/04_missing_tempo_freeze_conservative.json")
    out = compute_groove_layer_control(payload)
    assert out["controls"]["tempo"]["max_delta_pct_per_min"] == 0

def test_vector_05a_probe_start_density():
    payload = load("fixtures/vectors/05a_probe_start_density.json")
    state = GrooveStateV0(stable_windows=1, probe_cooldown_windows=0)
    out = compute_groove_layer_control(payload, state=state)
    assert out["controls"]["arrangement"]["density_target"] == "dense"

def test_vector_05b_probe_revert_on_instability():
    payload = load("fixtures/vectors/05b_probe_revert_on_instability.json")
    state = GrooveStateV0(probe_active=True, probe_kind="density", probe_variant="dense", probe_baseline_density="medium", last_density="dense", stable_windows=2)
    out = compute_groove_layer_control(payload, state=state)
    # Revert triggers and we end up in the instability safety mode
    assert out["controls"]["loop"]["policy"] == "micro_loop"
    assert out["debug"]["reason"] == "probe_revert_then_unstable_gate"
