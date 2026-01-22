import json
from groove_layer import compute_groove_layer_control

def load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_stage_3_0_smoke_emits_envelope_and_state():
    payload = load("fixtures/vectors/03_0_smoke.json")
    out = compute_groove_layer_control(payload, debug=True)

    assert out["schema_id"] == "groove_layer_control"
    assert out["schema_version"] == "v0"
    assert set(out["controls"].keys()) == {"tempo", "arrangement", "looping"}
    assert "state_hint" in out and "fast" in out["state_hint"] and "slow" in out["state_hint"]
