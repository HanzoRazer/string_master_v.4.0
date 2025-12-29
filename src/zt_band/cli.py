from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path
from typing import List, Literal

from .engine import generate_accompaniment
from .gravity_bridge import annotate_progression, compute_transitions
from .patterns import STYLE_REGISTRY
from shared.zone_tritone.pc import name_from_pc


OutputFormat = Literal["text", "markdown", "json"]


def _parse_chord_string(chord_str: str) -> List[str]:
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
        help="Accompaniment style name (see: zt-band styles).",
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
    p_annot.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="Output format: text (default), markdown, or json.",
    )
    p_annot.add_argument(
        "--save",
        type=str,
        default=None,
        help="Optional path to save the annotation output (instead of or in addition to printing).",
    )
    p_annot.set_defaults(func=cmd_annotate)

    # ---- styles subcommand ----
    p_styles = subparsers.add_parser(
        "styles",
        help="List available accompaniment styles.",
    )
    p_styles.set_defaults(func=cmd_styles)

    return parser


def _load_chords_from_args(args: argparse.Namespace) -> List[str]:
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


# ------------------------
# create command
# ------------------------


def cmd_create(args: argparse.Namespace) -> int:
    chords = _load_chords_from_args(args)

    if args.style not in STYLE_REGISTRY:
        print(
            f"error: unknown style '{args.style}'. "
            "Use 'zt-band styles' to list available styles.",
            file=sys.stderr,
        )
        return 1

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

    print(f"Created backing track: {args.outfile}")
    return 0


# ------------------------
# annotate command
# ------------------------


def _format_annotations_text(annotated, transitions) -> str:
    lines: List[str] = []
    lines.append("Chord annotations:")
    lines.append("idx | chord    | root | pc | zone     | tritone axis | gravity→ | on_chain")
    lines.append("----+----------+------+----+----------+-------------+----------+---------")

    for idx, ac in enumerate(annotated):
        root_name = name_from_pc(ac.root_pc)
        axis_a, axis_b = ac.axis
        axis_str = f"{name_from_pc(axis_a)}–{name_from_pc(axis_b)}"
        grav_str = "-"
        if ac.gravity_target is not None:
            grav_str = name_from_pc(ac.gravity_target)
        lines.append(
            f"{idx:>3} | {ac.chord.symbol:<8} | {root_name:<4} | {ac.root_pc:>2} "
            f"| {ac.zone:<8} | {axis_str:<11} | {grav_str:<8} | {str(ac.is_on_chain):<7}"
        )

    if transitions:
        lines.append("")
        lines.append("Stepwise transitions:")
        lines.append("from→to | int(st) | zones                 | tags")
        lines.append("--------+---------+-----------------------+--------------------------")
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
            lines.append(
                f"{from_name:>3}→{to_name:<3} | {tr.interval_semitones:>3}     "
                f"| {zone_pair:<21} | {tag_str}"
            )

    return "\n".join(lines)


def _format_annotations_markdown(annotated, transitions) -> str:
    lines: List[str] = []

    # Chord table
    lines.append("### Chord Annotations")
    lines.append("")
    lines.append("| # | Chord | Root | PC | Zone | Tritone Axis | Gravity -> | On Chain |")
    lines.append("|---|-------|------|----|------|--------------|------------|----------|")

    for idx, ac in enumerate(annotated):
        root_name = name_from_pc(ac.root_pc)
        axis_a, axis_b = ac.axis
        axis_str = f"{name_from_pc(axis_a)}–{name_from_pc(axis_b)}"
        grav_str = "-"
        if ac.gravity_target is not None:
            grav_str = name_from_pc(ac.gravity_target)
        lines.append(
            f"| {idx} | {ac.chord.symbol} | {root_name} | {ac.root_pc} | "
            f"{ac.zone} | {axis_str} | {grav_str} | {ac.is_on_chain} |"
        )

    # Transition table
    if transitions:
        lines.append("")
        lines.append("### Stepwise Transitions")
        lines.append("")
        lines.append("| From -> To | Interval (semitones) | Zones | Tags |")
        lines.append("|------------|----------------------|-------|------|")
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
            lines.append(
                f"| {from_name} -> {to_name} | {tr.interval_semitones} | "
                f"{zone_pair} | {tag_str} |"
            )

    return "\n".join(lines)


def _format_annotations_json(annotated, transitions) -> str:
    chord_blob = []
    for idx, ac in enumerate(annotated):
        axis_a, axis_b = ac.axis
        gravity_target_pc = ac.gravity_target
        chord_blob.append(
            {
                "index": idx,
                "symbol": ac.chord.symbol,
                "root_pc": ac.root_pc,
                "root_name": name_from_pc(ac.root_pc),
                "zone": ac.zone,
                "tritone_axis": [
                    name_from_pc(axis_a),
                    name_from_pc(axis_b),
                ],
                "gravity_target_pc": gravity_target_pc,
                "gravity_target_name": (
                    name_from_pc(gravity_target_pc)
                    if gravity_target_pc is not None
                    else None
                ),
                "is_on_chain": ac.is_on_chain,
            }
        )

    trans_blob = []
    for tr in transitions:
        trans_blob.append(
            {
                "from_index": tr.index_from,
                "to_index": tr.index_from + 1,
                "from_root_pc": tr.from_root,
                "from_root_name": name_from_pc(tr.from_root),
                "to_root_pc": tr.to_root,
                "to_root_name": name_from_pc(tr.to_root),
                "interval_semitones": tr.interval_semitones,
                "from_zone": tr.from_zone,
                "to_zone": tr.to_zone,
                "is_desc_fourth": tr.is_desc_fourth,
                "is_asc_fourth": tr.is_asc_fourth,
                "is_half_step": tr.is_half_step,
                "is_whole_step": tr.is_whole_step,
            }
        )

    payload = {
        "chords": chord_blob,
        "transitions": trans_blob,
    }
    return json.dumps(payload, indent=2, sort_keys=False)


def cmd_annotate(args: argparse.Namespace) -> int:
    chords = _load_chords_from_args(args)
    fmt: OutputFormat = args.format

    annotated = annotate_progression(chords)
    transitions = compute_transitions(annotated)

    if not annotated:
        print("No chords to annotate.")
        return 0

    if fmt == "text":
        out = _format_annotations_text(annotated, transitions)
    elif fmt == "markdown":
        out = _format_annotations_markdown(annotated, transitions)
    elif fmt == "json":
        out = _format_annotations_json(annotated, transitions)
    else:
        out = _format_annotations_text(annotated, transitions)

    # print to stdout
    print(out)

    # optional save-to-file
    if args.save:
        path = Path(args.save)
        path.write_text(out, encoding="utf-8")
        print(f"\nSaved annotation to: {path}")

    return 0


# ------------------------
# styles command
# ------------------------


def cmd_styles(args: argparse.Namespace) -> int:
    print("Available accompaniment styles:\n")
    print("name          | description")
    print("--------------+---------------------------------------------")
    for key, style in STYLE_REGISTRY.items():
        print(f"{key:<12} | {style.description}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return args.func(args)  # type: ignore[arg-type]


if __name__ == "__main__":
    raise SystemExit(main())
