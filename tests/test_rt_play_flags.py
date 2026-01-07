from zt_band.cli import build_arg_parser
import pytest


def test_rt_play_parses_panic_and_late_drop_ms():
    p = build_arg_parser()

    ns = p.parse_args(["rt-play", "--midi-out", "X"])
    assert ns.panic is True
    assert ns.late_drop_ms == 35
    assert ns.ghost_vel_max == 22

    ns2 = p.parse_args(["rt-play", "--no-panic", "--late-drop-ms", "60", "--midi-out", "X"])
    assert ns2.panic is False
    assert ns2.late_drop_ms == 60
    assert ns2.ghost_vel_max == 22

    ns3 = p.parse_args(
        ["rt-play", "--ghost-vel-max", "30", "--late-drop-ms", "50", "--midi-out", "X"]
    )
    assert ns3.ghost_vel_max == 30
    assert ns3.late_drop_ms == 50


def test_rt_play_flag_range_validation_errors_are_clean():
    p = build_arg_parser()

    with pytest.raises(SystemExit):
        p.parse_args(["rt-play", "--midi-out", "X", "--late-drop-ms", "-1"])

    with pytest.raises(SystemExit):
        p.parse_args(["rt-play", "--midi-out", "X", "--late-drop-ms", "999"])

    with pytest.raises(SystemExit):
        p.parse_args(["rt-play", "--midi-out", "X", "--ghost-vel-max", "0"])

    with pytest.raises(SystemExit):
        p.parse_args(["rt-play", "--midi-out", "X", "--ghost-vel-max", "200"])
