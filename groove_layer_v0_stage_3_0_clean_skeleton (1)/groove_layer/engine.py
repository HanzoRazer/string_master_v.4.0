from __future__ import annotations
from typing import Dict, Any, Optional
from .event_model import GrooveEventV0
from .state import GrooveStateV0
from .policy import decide_controls

def compute_groove_layer_control(payload: Dict[str, Any], state: Optional[GrooveStateV0] = None, *, debug: bool = False) -> Dict[str, Any]:
    if state is None:
        state = GrooveStateV0.from_prior_hint(payload.get("prior_state_hint"))

    engine_context = payload.get("engine_context") or {}
    events_raw = payload.get("events") or []
    events = [GrooveEventV0.from_dict(e) for e in events_raw]

    controls, dbg = decide_controls(engine_context, events, state)

    out = {
        "schema_id": "groove_layer_control",
        "schema_version": "v0",
        "controls": controls,
        "state_hint": state.to_hint(),
    }
    if debug:
        out["debug"] = dbg
    return out
