from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class GrooveStateV0:
    """Minimal state container for Stage 2.5.

    Adds probing + revert on top of Stage 2.4 recovery/hysteresis.

    - No learning/latents yet.
    - Probing is conservative: only when already stable, and always reversible.
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


def _avg_conf(events) -> float:
    if not events:
        return 0.0
    return sum(e.get("confidence", 0.0) for e in events) / len(events)


def _is_stable(event_count: int, avg_conf: float) -> bool:
    # Stability heuristic:
    return event_count >= 8 and avg_conf >= 0.90


def _seed_from_prior_hint(state: GrooveStateV0, prior: Dict[str, Any]) -> None:
    # Allow fixtures to seed prior corrective/probe mode without persistence.
    state.last_loop_policy = prior.get("last_loop_policy", state.last_loop_policy)
    state.last_density = prior.get("last_density", state.last_density)
    state.stable_windows = prior.get("stable_windows", state.stable_windows)

    state.probe_active = prior.get("probe_active", state.probe_active)
    state.probe_kind = prior.get("probe_kind", state.probe_kind)
    state.probe_variant = prior.get("probe_variant", state.probe_variant)
    state.probe_windows = prior.get("probe_windows", state.probe_windows)
    state.probe_baseline_density = prior.get("probe_baseline_density", state.probe_baseline_density)
    state.probe_cooldown_windows = prior.get("probe_cooldown_windows", state.probe_cooldown_windows)


def compute_groove_layer_control(payload: Dict[str, Any], state: Optional[GrooveStateV0] = None) -> Dict[str, Any]:
    """Compute Groove Layer v0 control intent.

    Stage 2.5 adds:
      - Vector 05 probing + revert
      - Conservative probe gating and cooldown
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

    # Cooldown ticks down on every window when context exists
    if state.probe_cooldown_windows > 0:
        state.probe_cooldown_windows -= 1

    state.stable_windows = state.stable_windows + 1 if stable else 0

    # --- Hard instability corrective mode (Vector 02)
    # If we are probing and instability is detected, revert immediately.
    if (avg_conf < 0.85) or (event_count < 8):
        if state.probe_active:
            # Revert probe immediately
            state.probe_active = False
            state.probe_kind = ""
            state.probe_variant = ""
            state.probe_windows = 0
            state.probe_cooldown_windows = 8  # blocks re-probing for ~2 minutes in v0 terms
            state.last_density = state.probe_baseline_density

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

    # --- Probing (Vector 05)
    # Probe definition (v0):
    # - Only when already stable for >=2 windows
    # - Only when not in cooldown
    # - Probe changes ONE thing (density), for 1 window, then stops (v0 minimal)
    allow_probes = True
    if state.probe_cooldown_windows > 0:
        allow_probes = False

    if stable and allow_probes:
        # If probe is active, continue it for 1 window; otherwise start a new one occasionally.
        if state.probe_active:
            state.probe_windows += 1
            # v0: end probe after 1 window; keep whatever was chosen (future versions evaluate success)
            if state.probe_windows >= 1:
                state.probe_active = False
                state.probe_kind = ""
                state.probe_variant = ""
                state.probe_windows = 0
            # Output stays on the probed density for this window
            return {
                "schema_id": "groove_layer_control",
                "schema_version": "v0",
                "device_id": device_id,
                "session_id": session_id,
                "controls": {
                    "tempo": {"policy": "follow_player", "nudge_strength": 0.2, "max_delta_pct_per_min": 5},
                    "arrangement": {"density_target": state.last_density, "instrumentation_policy": "keep_layers", "dynamics_follow": "soft_follow"},
                    "loop": {"policy": "none", "length_bars": 4, "exit_condition": "manual"},
                    "feel": {"feel_policy": engine_context.get("feel", "straight"), "grid": engine_context.get("grid", "eighth"), "click_policy": "subtle"},
                    "assist": {"assist_policy": "standard", "ghost_drums": "off", "count_in_bars": 1},
                    "change_policy": {"allow_modulation": False, "allow_tempo_change_events": True, "allow_density_probes": True}
                },
                "debug": {"state": asdict(state), "reason": "probe_active"}
            }

        # Start a probe only when stable_windows == 2 (deterministic trigger for fixtures)
        if state.stable_windows >= 2 and state.stable_windows % 2 == 0:
            state.probe_active = True
            state.probe_kind = "density"
            state.probe_variant = "dense"
            state.probe_baseline_density = "medium"
            state.last_density = "dense"
            state.probe_windows = 0

            return {
                "schema_id": "groove_layer_control",
                "schema_version": "v0",
                "device_id": device_id,
                "session_id": session_id,
                "controls": {
                    "tempo": {"policy": "follow_player", "nudge_strength": 0.2, "max_delta_pct_per_min": 5},
                    "arrangement": {"density_target": "dense", "instrumentation_policy": "keep_layers", "dynamics_follow": "soft_follow"},
                    "loop": {"policy": "none", "length_bars": 4, "exit_condition": "manual"},
                    "feel": {"feel_policy": engine_context.get("feel", "straight"), "grid": engine_context.get("grid", "eighth"), "click_policy": "subtle"},
                    "assist": {"assist_policy": "standard", "ghost_drums": "off", "count_in_bars": 1},
                    "change_policy": {"allow_modulation": False, "allow_tempo_change_events": True, "allow_density_probes": True}
                },
                "debug": {"state": asdict(state), "reason": "probe_start_density_dense"}
            }

    # --- Stable baseline (Vector 01)
    state.last_density = "medium"
    return {
        "schema_id": "groove_layer_control",
        "schema_version": "v0",
        "device_id": device_id,
        "session_id": session_id,
        "controls": {
            "tempo": {"policy": "follow_player", "nudge_strength": 0.2, "max_delta_pct_per_min": 5},
            "arrangement": {"density_target": "medium", "instrumentation_policy": "keep_layers", "dynamics_follow": "soft_follow"},
            "loop": {"policy": "none", "length_bars": 4, "exit_condition": "manual"},
            "feel": {"feel_policy": engine_context.get("feel", "straight"), "grid": engine_context.get("grid", "eighth"), "click_policy": "subtle"},
            "assist": {"assist_policy": "standard", "ghost_drums": "off", "count_in_bars": 1},
            "change_policy": {"allow_modulation": False, "allow_tempo_change_events": True, "allow_density_probes": True}
        },
        "debug": {"state": asdict(state), "reason": "stable_baseline"}
    }
