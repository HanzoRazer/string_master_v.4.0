from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class GrooveStateV0:
    """Minimal state container for Stage 2.6.

    Adds probe scheduling + cooldown decay on top of Stage 2.5.

    Concepts:
    - `probe_cooldown_windows`: blocks starting new probes (decays each window).
    - `next_probe_in_windows`: deterministic scheduler so probes don't fire every stable window.
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


def _avg_conf(events) -> float:
    if not events:
        return 0.0
    return sum(e.get("confidence", 0.0) for e in events) / len(events)


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


def _controls_baseline(engine_context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tempo": {"policy": "follow_player", "nudge_strength": 0.2, "max_delta_pct_per_min": 5},
        "arrangement": {"density_target": "medium", "instrumentation_policy": "keep_layers", "dynamics_follow": "soft_follow"},
        "loop": {"policy": "none", "length_bars": 4, "exit_condition": "manual"},
        "feel": {"feel_policy": engine_context.get("feel", "straight"), "grid": engine_context.get("grid", "eighth"), "click_policy": "subtle"},
        "assist": {"assist_policy": "standard", "ghost_drums": "off", "count_in_bars": 1},
        "change_policy": {"allow_modulation": False, "allow_tempo_change_events": True, "allow_density_probes": True}
    }


def compute_groove_layer_control(payload: Dict[str, Any], state: Optional[GrooveStateV0] = None) -> Dict[str, Any]:
    """Compute Groove Layer v0 control intent.

    Stage 2.6 adds Vector 06:
      - Probe cooldown decay (explicit + testable)
      - Probe scheduling (deterministic spacing between probes)
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

    # Scheduler only ticks down on stable windows (avoid "countdown while struggling")
    if stable and state.next_probe_in_windows > 0:
        state.next_probe_in_windows -= 1

    state.stable_windows = state.stable_windows + 1 if stable else 0

    # --- Hard instability corrective mode (Vector 02)
    # If probing and instability is detected, revert immediately + cooldown.
    if (avg_conf < 0.85) or (event_count < 8):
        if state.probe_active:
            state.probe_active = False
            state.probe_kind = ""
            state.probe_variant = ""
            state.probe_windows = 0
            state.probe_cooldown_windows = 8
            state.last_density = state.probe_baseline_density
            state.next_probe_in_windows = state.probe_interval_windows  # push future probes out

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
    # Rules (v0):
    # - Never start a probe if cooldown > 0.
    # - Only start a probe on stable windows, after at least 2 stable windows.
    # - Only start if scheduler counter is 0.
    # - When a probe starts, set next_probe_in_windows = probe_interval_windows.
    if stable and (state.probe_cooldown_windows == 0) and (state.stable_windows >= 2) and (state.next_probe_in_windows == 0) and (not state.probe_active):
        state.probe_active = True
        state.probe_kind = "density"
        state.probe_variant = "dense"
        state.probe_baseline_density = "medium"
        state.last_density = "dense"
        state.probe_windows = 0
        state.next_probe_in_windows = max(1, int(state.probe_interval_windows))

        controls = _controls_baseline(engine_context)
        controls["arrangement"]["density_target"] = "dense"
        return {
            "schema_id": "groove_layer_control",
            "schema_version": "v0",
            "device_id": device_id,
            "session_id": session_id,
            "controls": controls,
            "debug": {"state": asdict(state), "reason": "probe_start_scheduled_density_dense"}
        }

    # Probe active: keep the probed density for 1 window then end probe (v0 minimal)
    if state.probe_active:
        state.probe_windows += 1
        controls = _controls_baseline(engine_context)
        controls["arrangement"]["density_target"] = state.last_density
        if state.probe_windows >= 1:
            state.probe_active = False
            state.probe_kind = ""
            state.probe_variant = ""
            state.probe_windows = 0
        return {
            "schema_id": "groove_layer_control",
            "schema_version": "v0",
            "device_id": device_id,
            "session_id": session_id,
            "controls": controls,
            "debug": {"state": asdict(state), "reason": "probe_active"}
        }

    # --- Stable baseline (Vector 01)
    state.last_density = "medium"
    controls = _controls_baseline(engine_context)
    return {
        "schema_id": "groove_layer_control",
        "schema_version": "v0",
        "device_id": device_id,
        "session_id": session_id,
        "controls": controls,
        "debug": {"state": asdict(state), "reason": "stable_baseline"}
    }
