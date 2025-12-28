"""
zt_band CLI - Command-line interface for the accompaniment engine.

Usage:
    zt-band play --chords "Dm7 G7 Cmaj7" --tempo 120
    zt-band generate --progression "ii-V-I" --key C
"""

from __future__ import annotations

import argparse
import sys


def cmd_play(args: argparse.Namespace) -> int:
    """Play accompaniment for a chord progression."""
    print("🎸 zt-band: Play mode")
    print(f"   Chords: {args.chords}")
    print(f"   Tempo: {args.tempo} BPM")
    print("   (MIDI engine not yet implemented)")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate a backing track."""
    print("🎸 zt-band: Generate mode")
    print(f"   Progression: {args.progression}")
    print(f"   Key: {args.key}")
    print("   (Generator not yet implemented)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zt-band",
        description="Zone-Tritone Band: Real-time accompaniment engine for guitarists.",
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # play subcommand
    p_play = subparsers.add_parser("play", help="Play accompaniment for a chord progression")
    p_play.add_argument("--chords", required=True, help='Chord string, e.g. "Dm7 G7 Cmaj7"')
    p_play.add_argument("--tempo", type=int, default=120, help="Tempo in BPM (default: 120)")
    p_play.set_defaults(func=cmd_play)
    
    # generate subcommand
    p_gen = subparsers.add_parser("generate", help="Generate a backing track")
    p_gen.add_argument("--progression", required=True, help='Progression type, e.g. "ii-V-I"')
    p_gen.add_argument("--key", default="C", help="Key (default: C)")
    p_gen.set_defaults(func=cmd_generate)
    
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
