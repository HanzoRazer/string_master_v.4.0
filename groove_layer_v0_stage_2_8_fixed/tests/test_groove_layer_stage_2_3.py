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
    assert out["controls"]["loop"]["policy"] == "micro_loop"
    assert out["debug"]["reason"] == "probe_revert_then_unstable_gate"

def test_vector_06a_cooldown_blocks_probe():
    payload = load("fixtures/vectors/06a_cooldown_blocks_probe.json")
    state = GrooveStateV0(stable_windows=2, probe_cooldown_windows=2, next_probe_in_windows=0)
    out = compute_groove_layer_control(payload, state=state)
    assert out["controls"]["arrangement"]["density_target"] == "medium"

def test_vector_06b_cooldown_expired_probe_starts():
    payload = load("fixtures/vectors/06b_cooldown_expired_probe_starts.json")
    state = GrooveStateV0(stable_windows=1, probe_cooldown_windows=1, next_probe_in_windows=0)
    out = compute_groove_layer_control(payload, state=state)
    assert out["controls"]["arrangement"]["density_target"] == "dense"

def test_vector_06c_scheduler_blocks_until_zero():
    payload = load("fixtures/vectors/06c_scheduler_blocks_until_zero.json")
    # next_probe_in_windows=2: ticks to 1 this window, should NOT start probe yet
    state = GrooveStateV0(stable_windows=2, probe_cooldown_windows=0, next_probe_in_windows=2)
    out = compute_groove_layer_control(payload, state=state)
    assert out["controls"]["arrangement"]["density_target"] == "medium"


def test_vector_07a_probe_success_decreases_interval():
    payload = load("fixtures/vectors/07a_probe_success_decreases_interval.json")
    state = GrooveStateV0(probe_active=True, last_density="dense", probe_interval_windows=3)
    out = compute_groove_layer_control(payload, state=state)
    assert out["debug"]["reason"] == "probe_complete_scored"
    assert out["debug"]["state"]["probe_last_outcome"] == "success"
    assert out["debug"]["state"]["probe_interval_windows"] == 2

def test_vector_07b_probe_fail_increases_interval_sets_cooldown():
    payload = load("fixtures/vectors/07b_probe_fail_increases_interval_sets_cooldown.json")
    state = GrooveStateV0(probe_active=True, last_density="dense", probe_interval_windows=3)
    out = compute_groove_layer_control(payload, state=state)
    assert out["debug"]["reason"] == "probe_complete_scored"
    assert out["debug"]["state"]["probe_last_outcome"] == "fail"
    assert out["debug"]["state"]["probe_interval_windows"] == 4
    assert out["debug"]["state"]["probe_cooldown_windows"] >= 2


def test_vector_08a_small_drift_follow_player():
    payload = load("fixtures/vectors/08a_small_drift_follow_player.json")
    state = GrooveStateV0()
    out = compute_groove_layer_control(payload, state=state)
    assert out["controls"]["tempo"]["policy"] == "follow_player"
    assert abs(out["controls"]["tempo"]["nudge_strength"]) <= 0.05

def test_vector_08b_accumulated_drift_triggers_correct():
    payload = load("fixtures/vectors/08b_accumulated_drift_triggers_correct.json")
    state = GrooveStateV0()
    out = compute_groove_layer_control(payload, state=state)
    assert out["controls"]["tempo"]["policy"] == "correct_drift"
    # correction should be stronger than single-window clamp in some cases, but still bounded
    assert abs(out["controls"]["tempo"]["nudge_strength"]) <= 0.30
