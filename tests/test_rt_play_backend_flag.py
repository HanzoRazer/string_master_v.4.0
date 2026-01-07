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
