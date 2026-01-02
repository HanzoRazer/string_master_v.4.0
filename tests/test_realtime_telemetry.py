"""
Tests for realtime_telemetry.py — Bar boundary CC emission.
"""
import pytest

from zt_band.realtime_telemetry import (
    MIDO_AVAILABLE,
    _clamp_cc_value,
    make_bar_cc_messages,
)


class TestClampCcValue:
    def test_clamp_within_range(self):
        assert _clamp_cc_value(64) == 64

    def test_clamp_at_zero(self):
        assert _clamp_cc_value(0) == 0

    def test_clamp_at_max(self):
        assert _clamp_cc_value(127) == 127

    def test_clamp_below_zero(self):
        assert _clamp_cc_value(-10) == 0

    def test_clamp_above_max(self):
        assert _clamp_cc_value(200) == 127

    def test_clamp_converts_to_int(self):
        result = _clamp_cc_value(64)
        assert isinstance(result, int)


@pytest.mark.skipif(not MIDO_AVAILABLE, reason="mido not installed")
class TestMakeBarCcMessages:
    def test_returns_two_messages(self):
        msgs = make_bar_cc_messages(
            channel=0,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=8,
            bar_index=1,
        )
        assert len(msgs) == 2

    def test_countdown_message(self):
        msgs = make_bar_cc_messages(
            channel=0,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=8,
            bar_index=1,
        )
        countdown_msg = msgs[0]
        assert countdown_msg.type == "control_change"
        assert countdown_msg.channel == 0
        assert countdown_msg.control == 20
        assert countdown_msg.value == 8

    def test_index_message(self):
        msgs = make_bar_cc_messages(
            channel=0,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=8,
            bar_index=5,
        )
        index_msg = msgs[1]
        assert index_msg.type == "control_change"
        assert index_msg.channel == 0
        assert index_msg.control == 21
        assert index_msg.value == 5

    def test_channel_wrapping(self):
        msgs = make_bar_cc_messages(
            channel=20,  # > 15, should wrap
            cc_countdown=20,
            cc_index=21,
            bars_remaining=1,
            bar_index=1,
        )
        # Channel 20 % 16 = 4
        assert msgs[0].channel == 4
        assert msgs[1].channel == 4

    def test_cc_number_wrapping(self):
        msgs = make_bar_cc_messages(
            channel=0,
            cc_countdown=150,  # > 127, should wrap
            cc_index=200,      # > 127, should wrap
            bars_remaining=1,
            bar_index=1,
        )
        # CC 150 % 128 = 22, CC 200 % 128 = 72
        assert msgs[0].control == 22
        assert msgs[1].control == 72

    def test_value_clamping(self):
        msgs = make_bar_cc_messages(
            channel=0,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=200,  # > 127
            bar_index=300,       # > 127
        )
        assert msgs[0].value == 127  # clamped
        assert msgs[1].value == 127  # clamped

    def test_zero_values(self):
        msgs = make_bar_cc_messages(
            channel=0,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=0,
            bar_index=0,
        )
        assert msgs[0].value == 0
        assert msgs[1].value == 0

    def test_negative_values_clamped(self):
        msgs = make_bar_cc_messages(
            channel=0,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=-5,
            bar_index=-10,
        )
        assert msgs[0].value == 0  # clamped
        assert msgs[1].value == 0  # clamped


class TestMakeBarCcMessagesWithoutMido:
    def test_returns_empty_when_mido_unavailable(self):
        # This test verifies the fallback behavior
        # If mido is not available, the function should return []
        if not MIDO_AVAILABLE:
            msgs = make_bar_cc_messages(
                channel=0,
                cc_countdown=20,
                cc_index=21,
                bars_remaining=8,
                bar_index=1,
            )
            assert msgs == []
