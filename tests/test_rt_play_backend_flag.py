"""
Tests for rt-play --backend flag.

Verifies CLI parses backend argument correctly without running actual MIDI.
"""
from __future__ import annotations

import argparse

from zt_band.cli import build_arg_parser


def test_rt_play_has_backend_flag():
    """rt-play subcommand accepts --backend argument."""
    parser = build_arg_parser()

    # Default backend is mido
    ns = parser.parse_args(["rt-play", "--midi-out", "TestPort"])
    assert isinstance(ns, argparse.Namespace)
    assert ns.backend == "mido"


def test_rt_play_backend_mido():
    """--backend mido is accepted."""
    parser = build_arg_parser()
    ns = parser.parse_args(["rt-play", "--backend", "mido", "--midi-out", "TestPort"])
    assert ns.backend == "mido"


def test_rt_play_backend_rtmidi():
    """--backend rtmidi is accepted."""
    parser = build_arg_parser()
    ns = parser.parse_args(["rt-play", "--backend", "rtmidi", "--midi-out", "TestPort"])
    assert ns.backend == "rtmidi"


def test_rt_play_panic_flag_default_on():
    """--panic is on by default."""
    parser = build_arg_parser()
    ns = parser.parse_args(["rt-play", "--midi-out", "TestPort"])
    assert ns.panic is True


def test_rt_play_no_panic_flag():
    """--no-panic disables panic cleanup."""
    parser = build_arg_parser()
    ns = parser.parse_args(["rt-play", "--no-panic", "--midi-out", "TestPort"])
    assert ns.panic is False


def test_rt_play_late_drop_ms_default():
    """--late-drop-ms defaults to 35."""
    parser = build_arg_parser()
    ns = parser.parse_args(["rt-play", "--midi-out", "TestPort"])
    assert ns.late_drop_ms == 35


def test_rt_play_late_drop_ms_custom():
    """--late-drop-ms accepts custom value."""
    parser = build_arg_parser()
    ns = parser.parse_args(["rt-play", "--late-drop-ms", "50", "--midi-out", "TestPort"])
    assert ns.late_drop_ms == 50


def test_rt_play_late_drop_ms_zero_disables():
    """--late-drop-ms 0 disables late-drop."""
    parser = build_arg_parser()
    ns = parser.parse_args(["rt-play", "--late-drop-ms", "0", "--midi-out", "TestPort"])
    assert ns.late_drop_ms == 0


def test_rt_play_ghost_vel_max_default():
    """--ghost-vel-max defaults to 22."""
    parser = build_arg_parser()
    ns = parser.parse_args(["rt-play", "--midi-out", "TestPort"])
    assert ns.ghost_vel_max == 22


def test_rt_play_ghost_vel_max_custom():
    """--ghost-vel-max accepts custom value."""
    parser = build_arg_parser()
    ns = parser.parse_args(["rt-play", "--ghost-vel-max", "30", "--midi-out", "TestPort"])
    assert ns.ghost_vel_max == 30
