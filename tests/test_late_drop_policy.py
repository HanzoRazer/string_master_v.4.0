"""Unit tests for LateDropPolicy ornament classification."""
from __future__ import annotations

import mido
import pytest

from zt_band.realtime import LateDropPolicy


class TestIsOrnament:
    """Tests for is_ornament method."""

    def test_low_velocity_note_on_is_ornament(self) -> None:
        policy = LateDropPolicy()
        msg = mido.Message("note_on", note=60, velocity=15)
        assert policy.is_ornament(msg) is True

    def test_high_velocity_note_on_is_not_ornament(self) -> None:
        policy = LateDropPolicy()
        msg = mido.Message("note_on", note=60, velocity=90)
        assert policy.is_ornament(msg) is False

    def test_note_off_is_never_ornament(self) -> None:
        policy = LateDropPolicy()
        msg = mido.Message("note_off", note=60, velocity=64)
        assert policy.is_ornament(msg) is False

    def test_note_on_velocity_zero_is_not_ornament(self) -> None:
        """note_on with vel=0 is really note-off, must not drop."""
        policy = LateDropPolicy()
        msg = mido.Message("note_on", note=60, velocity=0)
        assert policy.is_ornament(msg) is False

    def test_control_change_is_never_ornament(self) -> None:
        policy = LateDropPolicy()
        msg = mido.Message("control_change", control=64, value=0)
        assert policy.is_ornament(msg) is False


class TestShouldDrop:
    """Tests for should_drop method."""

    def test_drop_ornament_when_late(self) -> None:
        policy = LateDropPolicy(enabled=True, late_drop_ms=35, ghost_note_on_max_vel=22)
        msg = mido.Message("note_on", note=60, velocity=15)  # ghost ornament
        # 50ms late > 35ms threshold
        assert policy.should_drop(due_s=0.0, now_s=0.050, msg=msg) is True

    def test_never_drop_structural_note(self) -> None:
        """High velocity note must survive even when late."""
        policy = LateDropPolicy(enabled=True, late_drop_ms=35, ghost_note_on_max_vel=22)
        msg = mido.Message("note_on", note=60, velocity=90)  # structural
        # 100ms late, but still structural = no drop
        assert policy.should_drop(due_s=0.0, now_s=0.100, msg=msg) is False

    def test_no_drop_when_not_late(self) -> None:
        policy = LateDropPolicy(enabled=True, late_drop_ms=35)
        msg = mido.Message("note_on", note=60, velocity=15)
        # Only 20ms late < 35ms threshold
        assert policy.should_drop(due_s=0.0, now_s=0.020, msg=msg) is False

    def test_no_drop_when_disabled(self) -> None:
        policy = LateDropPolicy(enabled=False, late_drop_ms=35)
        msg = mido.Message("note_on", note=60, velocity=15)
        # Would drop if enabled, but policy is disabled
        assert policy.should_drop(due_s=0.0, now_s=0.100, msg=msg) is False

    def test_never_drop_note_off(self) -> None:
        """note_off must never be dropped regardless of lateness."""
        policy = LateDropPolicy(enabled=True, late_drop_ms=35)
        msg = mido.Message("note_off", note=60, velocity=64)
        assert policy.should_drop(due_s=0.0, now_s=1.0, msg=msg) is False

    def test_never_drop_control_change(self) -> None:
        """control_change must never be dropped regardless of lateness."""
        policy = LateDropPolicy(enabled=True, late_drop_ms=35)
        msg = mido.Message("control_change", control=64, value=0)
        assert policy.should_drop(due_s=0.0, now_s=1.0, msg=msg) is False
