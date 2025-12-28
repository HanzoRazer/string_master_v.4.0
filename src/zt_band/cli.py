"""
zt_band CLI - Command-line interface for the accompaniment engine.

Usage:
    zt-band create --chords "Dm7 G7 Cmaj7" --tempo 120 --outfile backing.mid
    zt-band create --chords "Dm7 G7 Cmaj7" --tritone-mode all_doms
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from .engine import generate_accompaniment


def _parse_chord_string(chord_str: str) -> List[str]:
    """Parse a space-separated chord string into a list."""
    return [tok for tok in chord_str.strip().split() if tok]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zt-band",
        description="Smart Guitar / Zone–Tritone backing band prototype.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- create subcommand ----
    p_create = subparsers.add_parser(
        "create",
        help="Generate a backing track from a chord progression.",
    )
    p_create.add_argument(
        "--chords",
        type=str,
        help='Inline chord string, e.g. "Cmaj7 Dm7 G7 Cmaj7".',
    )
    p_create.add_argument(
        "--file",
        type=str,
        help="Path to a text file containing chord symbols.",
    )
    p_create.add_argument(
        "--style",
        type=str,
        default="swing_basic",
        help="Accompaniment style (default: swing_basic).",
    )
    p_create.add_argument(
        "--tempo",
        type=int,
        default=120,
        help="Tempo in BPM (default: 120).",
    )
    p_create.add_argument(
        "--bars-per-chord",
        type=int,
        default=1,
        help="Number of 4/4 bars each chord lasts (default: 1).",
    )
    p_create.add_argument(
        "--outfile",
        type=str,
        default="backing.mid",
        help="Output MIDI filename (default: backing.mid).",
    )
    p_create.add_argument(
        "--tritone-mode",
        choices=["none", "all_doms", "probabilistic"],
        default="none",
        help=(
            "Tritone substitution behavior for dominant chords: "
            "'none' (default), 'all_doms' (always sub), or 'probabilistic'."
        ),
    )
    p_create.add_argument(
        "--tritone-strength",
        type=float,
        default=1.0,
        help=(
            "Probability [0.0, 1.0] for applying tritone subs when "
            "tritone-mode=probabilistic (default: 1.0 → always)."
        ),
    )
    p_create.add_argument(
        "--tritone-seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible tritone-sub patterns.",
    )
    p_create.set_defaults(func=cmd_create)

    return parser


def cmd_create(args: argparse.Namespace) -> int:
    """Generate a backing track."""
    if not args.chords and not args.file:
        print("error: either --chords or --file must be provided", file=sys.stderr)
        return 1

    if args.chords:
        chords = _parse_chord_string(args.chords)
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        text = path.read_text(encoding="utf-8")
        chords = _parse_chord_string(text)

    if not chords:
        print("error: no chords found", file=sys.stderr)
        return 1

    try:
        generate_accompaniment(
            chord_symbols=chords,
            style_name=args.style,
            tempo_bpm=args.tempo,
            bars_per_chord=args.bars_per_chord,
            outfile=args.outfile,
            tritone_mode=args.tritone_mode,
            tritone_strength=args.tritone_strength,
            tritone_seed=args.tritone_seed,
        )
        print(f"✅ Created backing track: {args.outfile}")
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return args.func(args)  # type: ignore[arg-type]


if __name__ == "__main__":
    raise SystemExit(main())
