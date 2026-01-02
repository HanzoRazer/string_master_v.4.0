"""
Tests for bar-countdown MIDI CC telemetry feature.
"""


class TestMakeBarCcMessages:
    """Unit tests for make_bar_cc_messages helper."""

    def test_returns_two_messages(self):
        from zt_band.realtime_telemetry import make_bar_cc_messages

        msgs = make_bar_cc_messages(
            channel=15,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=7,
            bar_index=3,
        )
        assert len(msgs) == 2

    def test_countdown_cc_value(self):
        from zt_band.realtime_telemetry import make_bar_cc_messages

        msgs = make_bar_cc_messages(
            channel=15,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=42,
            bar_index=10,
        )
        # First message is countdown CC
        assert msgs[0].type == "control_change"
        assert msgs[0].channel == 15
        assert msgs[0].control == 20
        assert msgs[0].value == 42

    def test_index_cc_value(self):
        from zt_band.realtime_telemetry import make_bar_cc_messages

        msgs = make_bar_cc_messages(
            channel=15,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=5,
            bar_index=99,
        )
        # Second message is index CC
        assert msgs[1].type == "control_change"
        assert msgs[1].channel == 15
        assert msgs[1].control == 21
        assert msgs[1].value == 99

    def test_clamps_countdown_to_127(self):
        from zt_band.realtime_telemetry import make_bar_cc_messages

        msgs = make_bar_cc_messages(
            channel=10,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=200,  # > 127
            bar_index=5,
        )
        # Countdown should be clamped to 127
        assert msgs[0].value == 127

    def test_clamps_index_to_127(self):
        from zt_band.realtime_telemetry import make_bar_cc_messages

        msgs = make_bar_cc_messages(
            channel=10,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=10,
            bar_index=500,  # > 127
        )
        # Index should be clamped to 127
        assert msgs[1].value == 127

    def test_clamps_negative_to_zero(self):
        from zt_band.realtime_telemetry import make_bar_cc_messages

        msgs = make_bar_cc_messages(
            channel=0,
            cc_countdown=20,
            cc_index=21,
            bars_remaining=-5,  # negative
            bar_index=-1,  # negative
        )
        # Both should be clamped to 0
        assert msgs[0].value == 0
        assert msgs[1].value == 0

    def test_different_channel(self):
        from zt_band.realtime_telemetry import make_bar_cc_messages

        msgs = make_bar_cc_messages(
            channel=5,
            cc_countdown=30,
            cc_index=31,
            bars_remaining=10,
            bar_index=3,
        )
        assert msgs[0].channel == 5
        assert msgs[0].control == 30
        assert msgs[1].channel == 5
        assert msgs[1].control == 31


class TestRtSpecBarCcFields:
    """Tests for bar CC fields in RtSpec."""

    def test_bar_cc_defaults(self):
        from zt_band.realtime import RtSpec

        spec = RtSpec(midi_out="test")

        assert not spec.bar_cc_enabled
        assert spec.bar_cc_channel == 15
        assert spec.bar_cc_countdown == 20
        assert spec.bar_cc_index == 21
        assert spec.bar_cc_section == 22
        assert spec.bars_limit is None

    def test_bar_cc_custom_values(self):
        from zt_band.realtime import RtSpec

        spec = RtSpec(
            midi_out="test",
            bar_cc_enabled=True,
            bar_cc_channel=10,
            bar_cc_countdown=50,
            bar_cc_index=51,
            bar_cc_section=52,
            bars_limit=16,
        )

        assert spec.bar_cc_enabled
        assert spec.bar_cc_channel == 10
        assert spec.bar_cc_countdown == 50
        assert spec.bar_cc_index == 51
        assert spec.bar_cc_section == 52
        assert spec.bars_limit == 16


class TestCliBarCcFlags:
    """Tests for CLI flag parsing for bar CC."""

    def test_bar_cc_flag_parsed(self):
        from zt_band.cli import build_arg_parser

        parser = build_arg_parser()
        args = parser.parse_args([
            "rt-play",
            "--midi-out", "test_port",
            "--bar-cc",
        ])

        assert args.bar_cc

    def test_bar_cc_channel_flag_parsed(self):
        from zt_band.cli import build_arg_parser

        parser = build_arg_parser()
        args = parser.parse_args([
            "rt-play",
            "--midi-out", "test_port",
            "--bar-cc-channel", "10",
        ])

        assert args.bar_cc_channel == 10

    def test_bar_cc_countdown_flag_parsed(self):
        from zt_band.cli import build_arg_parser

        parser = build_arg_parser()
        args = parser.parse_args([
            "rt-play",
            "--midi-out", "test_port",
            "--bar-cc-countdown", "30",
        ])

        assert args.bar_cc_countdown == 30

    def test_bar_cc_index_flag_parsed(self):
        from zt_band.cli import build_arg_parser

        parser = build_arg_parser()
        args = parser.parse_args([
            "rt-play",
            "--midi-out", "test_port",
            "--bar-cc-index", "31",
        ])

        assert args.bar_cc_index == 31

    def test_all_bar_cc_flags_together(self):
        from zt_band.cli import build_arg_parser

        parser = build_arg_parser()
        args = parser.parse_args([
            "rt-play",
            "--midi-out", "test_port",
            "--bar-cc",
            "--bar-cc-channel", "8",
            "--bar-cc-countdown", "60",
            "--bar-cc-index", "61",
            "--bar-cc-section", "62",
        ])

        assert args.bar_cc
        assert args.bar_cc_channel == 8
        assert args.bar_cc_countdown == 60
        assert args.bar_cc_index == 61
        assert args.bar_cc_section == 62


class TestBarCcSectionMarker:
    """Tests for section marker (CC#22) feature."""

    def test_bar_cc_section_flag_parsed(self):
        from zt_band.cli import build_arg_parser

        parser = build_arg_parser()
        args = parser.parse_args([
            "rt-play",
            "--midi-out", "test_port",
            "--bar-cc-section", "40",
        ])

        assert args.bar_cc_section == 40

    def test_bar_cc_section_default(self):
        from zt_band.cli import build_arg_parser

        parser = build_arg_parser()
        args = parser.parse_args([
            "rt-play",
            "--midi-out", "test_port",
        ])

        assert args.bar_cc_section == 22

    def test_clamp_cc_value_export(self):
        from zt_band.realtime_telemetry import _clamp_cc_value

        assert _clamp_cc_value(50) == 50
        assert _clamp_cc_value(-1) == 0
        assert _clamp_cc_value(200) == 127
