#!/usr/bin/env python3
"""
CLI wrapper for Zone-Tritone etude generator.

Usage:
    python zt_generate.py blues_C.mid
    python zt_generate.py blues_G.mid --key G --tempo 110 --swing 0.33
    python zt_generate.py etude.mid --key Bb --mode tag --style bluesy --difficulty hard
"""
from __future__ import annotations

import argparse
import sys

from src.shared.zone_tritone.generator import generate_etude_midi, etude_summary
from src.shared.zone_tritone.types import BackdoorMode, Difficulty, StyleMode

# Key name to pitch class mapping
KEY_MAP = {
    "c": 0, "db": 1, "c#": 1, "d": 2, "eb": 3, "d#": 3,
    "e": 4, "f": 5, "gb": 6, "f#": 6, "g": 7, "ab": 8,
    "g#": 8, "a": 9, "bb": 10, "a#": 10, "b": 11,
}


def parse_key(s: str) -> int:
    """Parse key name to pitch class."""
    k = s.strip().lower()
    if k in KEY_MAP:
        return KEY_MAP[k]
    # Try as integer
    try:
        pc = int(k)
        if 0 <= pc <= 11:
            return pc
    except ValueError:
        pass
    raise ValueError(f"Unknown key: {s}. Use C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B or 0-11")


def parse_mode(s: str) -> BackdoorMode:
    """Parse backdoor mode."""
    m = s.strip().lower()
    if m in ("turnaround", "turn"):
        return BackdoorMode.TURNAROUND
    if m in ("cadence", "cad"):
        return BackdoorMode.CADENCE
    if m == "tag":
        return BackdoorMode.TAG
    raise ValueError(f"Unknown mode: {s}. Use turnaround, cadence, or tag")


def parse_style(s: str) -> StyleMode:
    """Parse resolution style."""
    st = s.strip().lower()
    if st == "hidden":
        return StyleMode.HIDDEN
    if st == "bluesy":
        return StyleMode.BLUESY
    raise ValueError(f"Unknown style: {s}. Use hidden or bluesy")


def parse_difficulty(s: str) -> Difficulty:
    """Parse difficulty level."""
    d = s.strip().lower()
    if d == "easy":
        return Difficulty.EASY
    if d in ("medium", "med"):
        return Difficulty.MEDIUM
    if d == "hard":
        return Difficulty.HARD
    raise ValueError(f"Unknown difficulty: {s}. Use easy, medium, or hard")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Zone-Tritone 12-bar blues etudes as MIDI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python zt_generate.py output.mid
  python zt_generate.py blues_G.mid --key G --tempo 110
  python zt_generate.py jazz_Bb.mid --key Bb --mode tag --swing 0.4
  python zt_generate.py hard_F.mid --key F --difficulty hard --style bluesy
        """,
    )

    parser.add_argument("outfile", help="Output MIDI file path")
    parser.add_argument("--key", "-k", default="C", help="Key (C, Db, D, ... B or 0-11). Default: C")
    parser.add_argument("--mode", "-m", default="turnaround",
                        help="Backdoor mode: turnaround, cadence, tag. Default: turnaround")
    parser.add_argument("--style", "-s", default="hidden",
                        help="Resolution style: hidden, bluesy. Default: hidden")
    parser.add_argument("--difficulty", "-d", default="medium",
                        help="Difficulty: easy, medium, hard. Default: medium")
    parser.add_argument("--tempo", "-t", type=int, default=120,
                        help="Tempo BPM. Default: 120")
    parser.add_argument("--swing", type=float, default=0.0,
                        help="Swing ratio 0.0-0.5 (0=straight, 0.33=light, 0.5=hard). Default: 0")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress output")

    args = parser.parse_args()

    try:
        key = parse_key(args.key)
        mode = parse_mode(args.mode)
        style = parse_style(args.style)
        difficulty = parse_difficulty(args.difficulty)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    etude = generate_etude_midi(
        outfile=args.outfile,
        key=key,
        mode=mode,
        style=style,
        difficulty=difficulty,
        tempo_bpm=args.tempo,
        swing_ratio=args.swing,
        seed=args.seed,
    )

    if not args.quiet:
        print(f"Created: {args.outfile}")
        print(etude_summary(etude))
        print(f"Tempo: {args.tempo} BPM, Swing: {args.swing}")


if __name__ == "__main__":
    main()
