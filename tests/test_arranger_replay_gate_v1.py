# tests/test_arranger_replay_gate_v1.py
"""
Pytest hook for arranger golden vector replay.

Ensures all vectors in fixtures/golden/arranger_vectors/ replay deterministically.
"""
from __future__ import annotations

from pathlib import Path

from zt_band.adapters.arranger_replay_gate_v1 import replay_all


def test_arranger_vectors_replay():
    """Replay all arranger vectors and fail if any mismatch."""
    root = Path(__file__).resolve().parents[1] / "fixtures" / "golden" / "arranger_vectors"
    changelog_path = root / "CHANGELOG.md"

    res = replay_all(
        root,
        update_golden=False,
        changelog_path=changelog_path,
        bump_changelog_reason=None,
    )
    assert res.ok, res.message
