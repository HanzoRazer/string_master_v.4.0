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
from .gravity_bridge import annotate_progression, compute_transitions
from shared.zone_tritone.pc import name_from_pc


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

    # ---- annotate subcommand ----
    p_annot = subparsers.add_parser(
        "annotate",
        help="Print Zone–Tritone annotations and gravity diagnostics for a progression.",
    )
    p_annot.add_argument(
        "--chords",
        type=str,
        help='Inline chord string, e.g. "Cmaj7 Dm7 G7 Cmaj7".',
    )
    p_annot.add_argument(
        "--file",
        type=str,
        help="Path to a text file containing chord symbols.",
    )
    p_annot.set_defaults(func=cmd_annotate)

    return parser


def _load_chords_from_args(args: argparse.Namespace) -> List[str]:
    """Load chord symbols from --chords or --file argument."""
    if not args.chords and not args.file:
        print("error: either --chords or --file must be provided", file=sys.stderr)
        sys.exit(1)

    if args.chords:
        chords = _parse_chord_string(args.chords)
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
        chords = _parse_chord_string(text)

    if not chords:
        print("error: no chords found", file=sys.stderr)
        sys.exit(1)

    return chords


def cmd_create(args: argparse.Namespace) -> int:
    """Generate a backing track."""
    chords = _load_chords_from_args(args)

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


def cmd_annotate(args: argparse.Namespace) -> int:
    """Print Zone–Tritone annotations and gravity diagnostics."""
    chords = _load_chords_from_args(args)

    annotated = annotate_progression(chords)
    transitions = compute_transitions(annotated)

    if not annotated:
        print("No chords to annotate.")
        return 0

    print("Chord annotations:")
    print("idx | chord    | root | pc | zone     | tritone axis | gravity→ | on_chain")
    print("----+----------+------+----+----------+--------------+----------+---------")

    for idx, ac in enumerate(annotated):
        root_name = name_from_pc(ac.root_pc)
        axis_a, axis_b = ac.axis
        axis_str = f"{name_from_pc(axis_a)}–{name_from_pc(axis_b)}"
        grav_str = "-"
        if ac.gravity_target is not None:
            grav_str = name_from_pc(ac.gravity_target)
        print(
            f"{idx:>3} | {ac.chord.symbol:<8} | {root_name:<4} | {ac.root_pc:>2} "
            f"| {ac.zone:<8} | {axis_str:<12} | {grav_str:<8} | {str(ac.is_on_chain):<7}"
        )

    if transitions:
        print("\nStepwise transitions:")
        print("from→to | int(st) | zones                 | tags")
        print("--------+---------+-----------------------+--------------------------")
        for tr in transitions:
            from_name = name_from_pc(tr.from_root)
            to_name = name_from_pc(tr.to_root)
            zone_pair = f"{tr.from_zone} → {tr.to_zone}"

            tags: List[str] = []
            if tr.is_desc_fourth:
                tags.append("↓4")
            if tr.is_asc_fourth:
                tags.append("↑4")
            if tr.is_half_step:
                tags.append("±1")
            if tr.is_whole_step:
                tags.append("±2")

            tag_str = ", ".join(tags) if tags else "-"
            print(
                f"{from_name:>3}→{to_name:<3} | {tr.interval_semitones:>3}     "
                f"| {zone_pair:<21} | {tag_str}"
            )

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return args.func(args)  # type: ignore[arg-type]


if __name__ == "__main__":
    raise SystemExit(main())
