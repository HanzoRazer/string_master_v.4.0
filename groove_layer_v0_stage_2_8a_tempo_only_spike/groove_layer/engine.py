
from typing import Dict, Any

class GrooveStateV0:
    def __init__(self):
        self.last_tempo_bpm = None
        self.drift_accum = 0.0

def compute_groove_layer_control(payload: Dict[str, Any], state: GrooveStateV0 | None = None) -> Dict[str, Any]:
    if state is None:
        state = GrooveStateV0()

    engine_context = payload.get("engine_context") or {}
    events = payload.get("events", [])
    target_bpm = engine_context.get("tempo_bpm_target", 120)

    if len(events) >= 2:
        deltas = [events[i+1]["t_onset_ms"] - events[i]["t_onset_ms"] for i in range(len(events)-1)]
        avg_ms = sum(deltas) / len(deltas)
        player_bpm = max(40, min(240, 60000 / avg_ms))
    else:
        player_bpm = target_bpm

    drift_pct = (player_bpm - target_bpm) / target_bpm
    drift_pct = max(-0.05, min(0.05, drift_pct))
    state.drift_accum += drift_pct

    if abs(state.drift_accum) > 0.03:
        tempo_policy = "correct_drift"
        nudge = max(-0.3, min(0.3, state.drift_accum))
        state.drift_accum = 0.0
    else:
        tempo_policy = "follow_player"
        nudge = drift_pct

    return {
        "schema_id": "groove_layer_control",
        "schema_version": "v0",
        "controls": {
            "tempo": {
                "policy": tempo_policy,
                "nudge_strength": round(nudge, 3),
                "max_delta_pct_per_min": 5
            }
        }
    }
