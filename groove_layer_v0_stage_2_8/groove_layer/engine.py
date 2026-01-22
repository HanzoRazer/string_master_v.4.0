from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List


@dataclass
class GrooveStateV0:
    """Minimal state container for Stage 2.8.

    Adds Vector 08: Tempo drift detection and correction.

    Vectors included:
    - Vector 01: Stable baseline
    - Vector 02: Hard instability corrective mode
    - Vector 03: Recovery / hysteresis
    - Vector 04: Missing engine context freeze
    - Vector 05: Probing + revert
    - Vector 06: Probe scheduling + cooldown decay
    - Vector 07: Probe success scoring + persist outcomes
    - Vector 08: Tempo drift detection + correction

    Persistence in v0 is *in-memory only* (state object). Higher layers can store state.
    """
    last_loop_policy: str = "none"
    last_density: str = "medium"
    stable_windows: int = 0  # consecutive stable windows

    # Probing state
    probe_active: bool = False
    probe_kind: str = ""           # e.g., "density"
    probe_variant: str = ""        # e.g., "dense"
    probe_windows: int = 0         # consecutive windows in current probe
    probe_baseline_density: str = "medium"
    probe_cooldown_windows: int = 0  # blocks re-probing for a while after revert

    # Probe scheduling (v0 deterministic)
    next_probe_in_windows: int = 0  # counts down; when hits 0 and stable, we may probe
    probe_interval_windows: int = 3 # schedule next probe this many stable windows later

    # Probe outcomes (Vector 07)
    probe_last_score: float = 0.0
    probe_last_outcome: str = "unknown"  # success | fail | unknown
    probe_history: List[Dict[str, Any]] = field(default_factory=list)

    # Tempo drift tracking (Vector 08)
    last_tempo_bpm: Optional[float] = None
    drift_accum: float = 0.0  # accumulated drift percentage


def _avg_conf(events) -> float:
    if not events:
        return 0.0
    return sum(e.get("confidence", 0.0) for e in events) / len(events)


def _avg_strength(events) -> float:
    if not events:
        return 0.0
    return sum(float(e.get("strength", 0.0)) for e in events) / len(events)


def _is_stable(event_count: int, avg_conf: float) -> bool:
    return event_count >= 8 and avg_conf >= 0.90


def _seed_from_prior_hint(state: GrooveStateV0, prior: Dict[str, Any]) -> None:
    state.last_loop_policy = prior.get("last_loop_policy", state.last_loop_policy)
    state.last_density = prior.get("last_density", state.last_density)
    state.stable_windows = prior.get("stable_windows", state.stable_windows)

    state.probe_active = prior.get("probe_active", state.probe_active)
    state.probe_kind = prior.get("probe_kind", state.probe_kind)
    state.probe_variant = prior.get("probe_variant", state.probe_variant)
    state.probe_windows = prior.get("probe_windows", state.probe_windows)
    state.probe_baseline_density = prior.get("probe_baseline_density", state.probe_baseline_density)
    state.probe_cooldown_windows = prior.get("probe_cooldown_windows", state.probe_cooldown_windows)

    state.next_probe_in_windows = prior.get("next_probe_in_windows", state.next_probe_in_windows)
    state.probe_interval_windows = prior.get("probe_interval_windows", state.probe_interval_windows)

    state.probe_last_score = prior.get("probe_last_score", state.probe_last_score)
    state.probe_last_outcome = prior.get("probe_last_outcome", state.probe_last_outcome)

    # Vector 08 state
    state.last_tempo_bpm = prior.get("last_tempo_bpm", state.last_tempo_bpm)
    state.drift_accum = prior.get("drift_accum", state.drift_accum)


def _compute_tempo_drift(events, target_bpm: float, state: GrooveStateV0) -> Dict[str, Any]:
    """Vector 08: Compute tempo drift and determine correction policy.

    Returns tempo control dict with:
    - policy: "follow_player" for small drift, "correct_drift" for large drift
    - nudge_strength: magnitude of correction
    - max_delta_pct_per_min: rate limit

    Algorithm:
    - Estimate player BPM from event inter-onset intervals
    - Compute drift percentage from target
    - Accumulate drift over windows
    - If accumulated drift exceeds threshold (3%), trigger correction
    """
    if len(events) >= 2:
        deltas = []
        for i in range(len(events) - 1):
            t0 = events[i].get("t_onset_ms", 0)
            t1 = events[i + 1].get("t_onset_ms", 0)
            delta = t1 - t0
            if delta > 0:
                deltas.append(delta)

        if deltas:
            avg_ms = sum(deltas) / len(deltas)
            # Convert inter-onset interval to BPM (assuming quarter notes)
            player_bpm = 60000.0 / avg_ms
            # Clamp to reasonable range
            player_bpm = max(40.0, min(240.0, player_bpm))
        else:
            player_bpm = target_bpm
    else:
        player_bpm = target_bpm

    state.last_tempo_bpm = player_bpm

    # Compute drift as percentage of target
    drift_pct = (player_bpm - target_bpm) / target_bpm if target_bpm > 0 else 0.0
    # Clamp individual window drift to ±5%
    drift_pct = max(-0.05, min(0.05, drift_pct))

    # Accumulate drift
    state.drift_accum += drift_pct

    # Threshold for correction: |drift_accum| > 3%
    if abs(state.drift_accum) > 0.03:
        # Large accumulated drift: correct
        policy = "correct_drift"
        # Nudge proportional to accumulated drift, clamped to ±30%
        nudge = max(-0.3, min(0.3, state.drift_accum))
        # Reset accumulator after correction
        state.drift_accum = 0.0
    else:
        # Small drift: follow player
        policy = "follow_player"
        nudge = drift_pct

    return {
        "policy": policy,
        "nudge_strength": round(nudge, 3),
        "max_delta_pct_per_min": 5
    }


def _controls_baseline(engine_context: Dict[str, Any], events, state: GrooveStateV0) -> Dict[str, Any]:
    """Build baseline controls with Vector 08 tempo drift integration."""
    target_bpm = engine_context.get("tempo_bpm_target", 120)
    tempo_control = _compute_tempo_drift(events, target_bpm, state)

    return {
        "tempo": tempo_control,
        "arrangement": {"density_target": "medium", "instrumentation_policy": "keep_layers", "dynamics_follow": "soft_follow"},
        "loop": {"policy": "none", "length_bars": 4, "exit_condition": "manual"},
        "feel": {"feel_policy": engine_context.get("feel", "straight"), "grid": engine_context.get("grid", "eighth"), "click_policy": "subtle"},
        "assist": {"assist_policy": "standard", "ghost_drums": "off", "count_in_bars": 1},
        "change_policy": {"allow_modulation": False, "allow_tempo_change_events": True, "allow_density_probes": True}
    }


def _score_probe_window(events) -> float:
    """v0 scoring heuristic (Vector 07).

    Proxy score in [0,1] from available event fields:
    - confidence (stability proxy)
    - strength (engagement proxy)
    """
    c = _avg_conf(events)
    s = _avg_strength(events)
    score = 0.75 * c + 0.25 * s
    return max(0.0, min(1.0, score))


def _apply_probe_outcome(state: GrooveStateV0, score: float) -> None:
    """Persist outcome and adapt schedule (v0 minimal).

    - success (>=0.90): probe more often (interval -1, min 2)
    - fail    (<0.90): probe less often (interval +1, max 6) and add cooldown (3)
    """
    outcome = "success" if score >= 0.90 else "fail"
    state.probe_last_score = float(score)
    state.probe_last_outcome = outcome
    state.probe_history.append({"outcome": outcome, "score": float(score)})

    if outcome == "success":
        state.probe_interval_windows = max(2, int(state.probe_interval_windows) - 1)
    else:
        state.probe_interval_windows = min(6, int(state.probe_interval_windows) + 1)
        state.probe_cooldown_windows = max(state.probe_cooldown_windows, 3)


def compute_groove_layer_control(payload: Dict[str, Any], state: Optional[GrooveStateV0] = None) -> Dict[str, Any]:
    """Compute Groove Layer v0 control intent.

    Stage 2.8 adds Vector 08:
      - Tempo drift detection from player event timing
      - Accumulated drift tracking across windows
      - Automatic correction when drift exceeds threshold

    Previous vectors:
      - Vector 01: Stable baseline
      - Vector 02: Hard instability corrective mode
      - Vector 03: Recovery / hysteresis
      - Vector 04: Missing engine context freeze
      - Vector 05: Probing + revert
      - Vector 06: Probe scheduling + cooldown decay
      - Vector 07: Probe success scoring + persist outcomes
    """
    if state is None:
        state = GrooveStateV0()

    engine_context = payload.get("engine_context")
    events = payload.get("events", [])
    device_id = payload.get("device_id")
    session_id = payload.get("session_id")

    prior = payload.get("prior_state_hint") or {}
    if prior:
        _seed_from_prior_hint(state, prior)

    # --- Missing engine context → conservative freeze (Vector 04)
    if engine_context is None:
        state.stable_windows = 0
        state.last_loop_policy = "none"
        state.last_density = "medium"
        state.probe_active = False
        state.probe_kind = ""
        state.probe_variant = ""
        state.probe_windows = 0
        state.drift_accum = 0.0
        return {
            "schema_id": "groove_layer_control",
            "schema_version": "v0",
            "device_id": device_id,
            "session_id": session_id,
            "controls": {
                "tempo": {"policy": "steady_clock", "nudge_strength": 0.0, "max_delta_pct_per_min": 0},
                "arrangement": {"density_target": "medium", "instrumentation_policy": "keep_layers", "dynamics_follow": "fixed"},
                "loop": {"policy": "none", "length_bars": 4, "exit_condition": "manual"},
                "feel": {"feel_policy": "straight", "grid": "quarter", "click_policy": "off"},
                "assist": {"assist_policy": "minimal", "ghost_drums": "off", "count_in_bars": 0},
                "change_policy": {"allow_modulation": False, "allow_tempo_change_events": False, "allow_density_probes": False}
            },
            "debug": {"state": asdict(state), "reason": "missing_engine_context"}
        }

    event_count = len(events)
    avg_conf = _avg_conf(events)
    stable = _is_stable(event_count, avg_conf)

    # --- Decay timers (Vector 06)
    if state.probe_cooldown_windows > 0:
        state.probe_cooldown_windows -= 1

    # Scheduler only ticks down on stable windows
    if stable and state.next_probe_in_windows > 0:
        state.next_probe_in_windows -= 1

    state.stable_windows = state.stable_windows + 1 if stable else 0

    # --- Hard instability corrective mode (Vector 02)
    if (avg_conf < 0.85) or (event_count < 8):
        if state.probe_active:
            # Probe is active but instability hit: revert and DO NOT score (probe invalidated)
            state.probe_active = False
            state.probe_kind = ""
            state.probe_variant = ""
            state.probe_windows = 0
            state.probe_cooldown_windows = 8
            state.last_density = state.probe_baseline_density
            state.next_probe_in_windows = state.probe_interval_windows
            state.drift_accum = 0.0  # Reset drift on instability

            return {
                "schema_id": "groove_layer_control",
                "schema_version": "v0",
                "device_id": device_id,
                "session_id": session_id,
                "controls": {
                    "tempo": {"policy": "steady_clock", "nudge_strength": 0.4, "max_delta_pct_per_min": 3},
                    "arrangement": {"density_target": "sparse", "instrumentation_policy": "reduce_layers", "dynamics_follow": "fixed"},
                    "loop": {"policy": "micro_loop", "length_bars": 4, "exit_condition": "stability_recovered"},
                    "feel": {"feel_policy": "straight", "grid": engine_context.get("grid", "eighth"), "click_policy": "prominent"},
                    "assist": {"assist_policy": "supportive", "ghost_drums": "light", "count_in_bars": 2},
                    "change_policy": {"allow_modulation": False, "allow_tempo_change_events": False, "allow_density_probes": False}
                },
                "debug": {"state": asdict(state), "reason": "probe_revert_then_unstable_gate"}
            }

        state.last_loop_policy = "micro_loop"
        state.last_density = "sparse"
        state.drift_accum = 0.0  # Reset drift on instability
        return {
            "schema_id": "groove_layer_control",
            "schema_version": "v0",
            "device_id": device_id,
            "session_id": session_id,
            "controls": {
                "tempo": {"policy": "steady_clock", "nudge_strength": 0.4, "max_delta_pct_per_min": 3},
                "arrangement": {"density_target": "sparse", "instrumentation_policy": "reduce_layers", "dynamics_follow": "fixed"},
                "loop": {"policy": "micro_loop", "length_bars": 4, "exit_condition": "stability_recovered"},
                "feel": {"feel_policy": "straight", "grid": engine_context.get("grid", "eighth"), "click_policy": "prominent"},
                "assist": {"assist_policy": "supportive", "ghost_drums": "light", "count_in_bars": 2},
                "change_policy": {"allow_modulation": False, "allow_tempo_change_events": False, "allow_density_probes": False}
            },
            "debug": {"state": asdict(state), "reason": "unstable_gate"}
        }

    # --- Recovery / hysteresis (Vector 03)
    if state.last_loop_policy == "micro_loop":
        if state.stable_windows < 2:
            state.last_loop_policy = "loop_section"
            state.last_density = "medium"
            return {
                "schema_id": "groove_layer_control",
                "schema_version": "v0",
                "device_id": device_id,
                "session_id": session_id,
                "controls": {
                    "tempo": {"policy": "follow_player", "nudge_strength": 0.25, "max_delta_pct_per_min": 5},
                    "arrangement": {"density_target": "medium", "instrumentation_policy": "keep_layers", "dynamics_follow": "soft_follow"},
                    "loop": {"policy": "loop_section", "length_bars": 4, "exit_condition": "stability_recovered"},
                    "feel": {"feel_policy": engine_context.get("feel", "straight"), "grid": engine_context.get("grid", "eighth"), "click_policy": "subtle"},
                    "assist": {"assist_policy": "standard", "ghost_drums": "off", "count_in_bars": 0},
                    "change_policy": {"allow_modulation": False, "allow_tempo_change_events": True, "allow_density_probes": True}
                },
                "debug": {"state": asdict(state), "reason": "recovery_deescalate"}
            }
        state.last_loop_policy = "none"
        state.last_density = "medium"

    # --- Probing + scheduling (Vector 06)
    if stable and (state.probe_cooldown_windows == 0) and (state.stable_windows >= 2) and (state.next_probe_in_windows == 0) and (not state.probe_active):
        state.probe_active = True
        state.probe_kind = "density"
        state.probe_variant = "dense"
        state.probe_baseline_density = "medium"
        state.last_density = "dense"
        state.probe_windows = 0
        state.next_probe_in_windows = max(1, int(state.probe_interval_windows))

        controls = _controls_baseline(engine_context, events, state)
        controls["arrangement"]["density_target"] = "dense"
        return {
            "schema_id": "groove_layer_control",
            "schema_version": "v0",
            "device_id": device_id,
            "session_id": session_id,
            "controls": controls,
            "debug": {"state": asdict(state), "reason": "probe_start_scheduled_density_dense"}
        }

    # --- Probe active (Vector 05) + score on completion (Vector 07)
    if state.probe_active:
        state.probe_windows += 1
        controls = _controls_baseline(engine_context, events, state)
        controls["arrangement"]["density_target"] = state.last_density

        # v0: probe lasts for exactly one window; score on completion
        if state.probe_windows >= 1:
            score = _score_probe_window(events)
            _apply_probe_outcome(state, score)

            state.probe_active = False
            state.probe_kind = ""
            state.probe_variant = ""
            state.probe_windows = 0
            state.last_density = "medium"

            return {
                "schema_id": "groove_layer_control",
                "schema_version": "v0",
                "device_id": device_id,
                "session_id": session_id,
                "controls": controls,
                "debug": {"state": asdict(state), "reason": "probe_complete_scored"}
            }

        return {
            "schema_id": "groove_layer_control",
            "schema_version": "v0",
            "device_id": device_id,
            "session_id": session_id,
            "controls": controls,
            "debug": {"state": asdict(state), "reason": "probe_active"}
        }

    # --- Stable baseline with tempo drift detection (Vector 01 + Vector 08)
    state.last_density = "medium"
    controls = _controls_baseline(engine_context, events, state)
    return {
        "schema_id": "groove_layer_control",
        "schema_version": "v0",
        "device_id": device_id,
        "session_id": session_id,
        "controls": controls,
        "debug": {"state": asdict(state), "reason": "stable_baseline"}
    }
