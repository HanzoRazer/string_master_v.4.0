from __future__ import annotations
from typing import Dict, List, Any, Tuple
from .event_model import GrooveEventV0
from .state import GrooveStateV0

def summarize_window(events: List[GrooveEventV0]) -> Dict[str, Any]:
    if not events:
        return {"event_count": 0, "avg_conf": 0.0}
    avg_conf = sum(e.confidence for e in events) / len(events)
    return {"event_count": len(events), "avg_conf": float(avg_conf)}

def stability_gate(summary: Dict[str, Any]) -> bool:
    return summary["event_count"] >= 6 and summary["avg_conf"] >= 0.90

def tempo_drift_control(state: GrooveStateV0, events: List[GrooveEventV0], target_bpm: float) -> Dict[str, Any]:
    # Placeholder; Stage 3.2 will reintroduce Vector 08 cleanly
    return {"policy": "follow_player", "nudge_strength": 0.0, "max_delta_pct_per_min": 5}

def density_control(state: GrooveStateV0, stable: bool, tempo_policy: str) -> Dict[str, Any]:
    if (not stable) or (tempo_policy == "correct_drift") or (state.fast.last_loop_policy == "micro_loop"):
        return {"density_target": state.slow.preferred_density, "mode": "hold"}
    return {"density_target": state.slow.preferred_density, "mode": "hold"}

def loop_control(state: GrooveStateV0, stable: bool) -> Dict[str, Any]:
    policy = "free_play" if stable else "micro_loop"
    state.fast.last_loop_policy = policy
    return {"policy": policy}

def decide_controls(engine_context: Dict[str, Any], events: List[GrooveEventV0], state: GrooveStateV0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    summary = summarize_window(events)
    stable = stability_gate(summary)

    if stable:
        state.fast.stable_windows += 1
        state.fast.unstable_windows = 0
    else:
        state.fast.unstable_windows += 1
        state.fast.stable_windows = 0

    target_bpm = float(engine_context.get("tempo_bpm_target", 120.0))
    tempo = tempo_drift_control(state, events, target_bpm)
    arrangement = density_control(state, stable=stable, tempo_policy=tempo["policy"])
    looping = loop_control(state, stable=stable)

    controls = {"tempo": tempo, "arrangement": arrangement, "looping": looping}
    debug = {"stable": stable, "summary": summary}
    return controls, debug
