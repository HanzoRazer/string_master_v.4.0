from __future__ import annotations

from pathlib import Path

from zt_band.e2e.e2e_replay_gate_v1 import replay_all


def test_e2e_vectors_replay():
    root = Path(__file__).resolve().parents[1] / "fixtures" / "golden" / "e2e_vectors"
    res = replay_all(root, update_golden=False, changelog_path=(root / "CHANGELOG.md"), bump_changelog_reason=None)
    assert res.ok, res.message
