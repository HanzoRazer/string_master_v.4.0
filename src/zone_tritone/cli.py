from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from .pc import pc_from_name, name_from_pc
from .gravity import gravity_chain
from .corpus import chord_sequence_to_roots
from .markov import build_transition_counts, normalize_transition_matrix
from .zones import (
    zone_name,
    is_same_zone,
    is_zone_cross,
    is_half_step,
    is_whole_step,
    interval,
)
from .tritones import tritone_axis
from .types import PitchClass


def _parse_chord_string(chord_str: str) -> List[str]:
    """
    Parse a simple chord string like:
        "Dm7 G7 Cmaj7 A7 Dm7"
    into a list of chord symbols.
    """
    return [tok for tok in chord_str.strip().split() if tok]


def cmd_gravity(args: argparse.Namespace) -> int:
    """
    Handle the 'gravity' subcommand.
    """
    try:
        root_pc: PitchClass = pc_from_name(args.root)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    steps = args.steps
    chain = gravity_chain(root_pc, steps)

    print(f"# Gravity chain starting from {args.root} (steps={steps})")
    print("# (cycle of fourths, Zone–Tritone gravity view)")
    print()

    for idx, pc in enumerate(chain):
        name = name_from_pc(pc)
        zname = zone_name(pc)
        print(f"{idx:2d}: {name:3s}  (pc={pc:2d}, {zname})")

    return 0


def _load_chords_from_file(path: Path) -> List[str]:
    """
    Load a chord sequence from a text file.

    Simple convention:
    - Each line may contain space-separated chord symbols.
    - All lines are concatenated into one long sequence.
    """
    chords: List[str] = []
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        chords.extend(_parse_chord_string(line))
    return chords


def cmd_analyze(args: argparse.Namespace) -> int:
    """
    Handle the 'analyze' subcommand.

    Either --chords "Dm7 G7 Cmaj7 ..." or --file path/to/chords.txt must be
    provided.
    """
    if not args.chords and not args.file:
        print("error: either --chords or --file must be provided", file=sys.stderr)
        return 1

    chords: List[str]
    if args.chords:
        chords = _parse_chord_string(args.chords)
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        chords = _load_chords_from_file(path)

    if not chords:
        print("error: no chords found to analyze", file=sys.stderr)
        return 1

    roots = chord_sequence_to_roots(chords)
    counts = build_transition_counts(roots)
    matrix = normalize_transition_matrix(counts, smoothing=args.smoothing)

    print("# Zone–Tritone Gravity Analysis")
    print("# Chord sequence:")
    print("  " + " ".join(chords))
    print()

    print("# Root sequence (pc / name):")
    root_line = "  " + " ".join(f"{r:2d}:{name_from_pc(r)}" for r in roots)
    print(root_line)
    print()

    # Basic stats: count descending fourth transitions
    total_transitions = 0
    fourths_transitions = 0
    same_root = 0

    prev = roots[0]
    for r in roots[1:]:
        total_transitions += 1
        if (r - prev) % 12 == 0:
            same_root += 1
        if (r - prev) % 12 == 7:  # up a 5th == down a 4th
            fourths_transitions += 1
        prev = r

    print("# Transition statistics:")
    if total_transitions > 0:
        pct_fourths = fourths_transitions / total_transitions * 100.0
    else:
        pct_fourths = 0.0
    print(f"  Total transitions      : {total_transitions}")
    print(f"  Descending 4th motion  : {fourths_transitions} ({pct_fourths:.1f}%)")
    print(f"  Same-root transitions  : {same_root}")
    print()

    if args.show_matrix:
        print("# Transition probability matrix (rows = from, cols = to)")
        header = "     " + " ".join(f"{i:4d}" for i in range(12))
        print(header)
        for i, row in enumerate(matrix):
            row_str = " ".join(f"{p:4.2f}" for p in row)
            print(f"{i:2d}: {row_str}")

    return 0


def _explain_transition(a: PitchClass, b: PitchClass) -> str:
    """
    Return a human-readable explanation of the motion from root a to root b,
    using Zone–Tritone terminology.
    """
    d = interval(a, b)  # in semitones mod 12
    same = (d == 0)
    desc_fourth = (d == 7)  # up a fifth == down a fourth
    asc_fourth = (d == 5)   # down a fifth == up a fourth
    hs = is_half_step(a, b)
    ws = is_whole_step(a, b)
    cross = is_zone_cross(a, b)

    if same:
        return "prolongation (same root, same gravity center)"

    if desc_fourth:
        return "functional resolution (root moves by descending 4th)"

    if asc_fourth:
        return "reverse 4th motion (preparation / back-cycle movement)"

    if hs and cross:
        return "chromatic neighbor (semitone, zone-cross; strong directional pull)"

    if ws and not cross:
        return "modal / diatonic whole-step (in-zone color motion)"

    return "non-standard motion (outside primary gravity patterns)"


# -------- TEXT RENDERING --------

def _print_explain_text(chords: List[str], roots: List[PitchClass]) -> None:
    """
    Original plain-text explain output.
    """
    print("# Zone–Tritone EXPLAIN")
    print("# Chord progression:")
    print("  " + " ".join(chords))
    print()

    # Per-chord: root, zone, implied tritone axis (3rd & 7th).
    print("# Per-chord gravity anchors:")
    print("(index)  chord   root  pc  zone      tritone axis (3,7)")
    print("---------------------------------------------------------")

    for idx, (ch, r) in enumerate(zip(chords, roots)):
        root_name = name_from_pc(r)
        zname = zone_name(r)
        # Classical 3rd and 7th for a dominant built on this root
        third_pc = (r + 4) % 12
        axis = tritone_axis(third_pc)
        a, b = axis
        axis_str = f"{name_from_pc(a)}–{name_from_pc(b)}"
        print(f"{idx:3d}:  {ch:6s} {root_name:4s} {r:2d}  {zname:7s}  {axis_str}")

    print()
    if len(roots) < 2:
        print("# (Only one chord provided; no transitions to explain.)")
        return

    # Step-by-step explanation of transitions.
    print("# Step-by-step transitions:")
    print("(from -> to)   interval  zone-relation                     explanation")
    print("--------------------------------------------------------------------------")

    prev_root = roots[0]
    prev_name = name_from_pc(prev_root)
    prev_zone = zone_name(prev_root)

    for idx, cur_root in enumerate(roots[1:], start=1):
        cur_name = name_from_pc(cur_root)
        cur_zone = zone_name(cur_root)
        d = interval(prev_root, cur_root)
        cross = is_zone_cross(prev_root, cur_root)
        same_zone = is_same_zone(prev_root, cur_root)
        desc_fourth = (d == 7)
        asc_fourth = (d == 5)
        hs = is_half_step(prev_root, cur_root)
        ws = is_whole_step(prev_root, cur_root)

        if cross:
            zone_relation = f"{prev_zone} -> {cur_zone} (zone-cross)"
        elif same_zone:
            zone_relation = f"{prev_zone} -> {cur_zone} (in-zone)"
        else:
            zone_relation = f"{prev_zone} -> {cur_zone}"

        motion_tags = []
        if desc_fourth:
            motion_tags.append("↓4")
        if asc_fourth:
            motion_tags.append("↑4")
        if hs:
            motion_tags.append("±1")
        if ws:
            motion_tags.append("±2")

        motion_str = f"{d:2d} st"  # semitones
        if motion_tags:
            motion_str += " [" + ",".join(motion_tags) + "]"

        explanation = _explain_transition(prev_root, cur_root)

        print(
            f"{prev_name:3s} -> {cur_name:3s}   {motion_str:10s}  "
            f"{zone_relation:32s}  {explanation}"
        )

        prev_root = cur_root
        prev_name = cur_name
        prev_zone = cur_zone

    # Show the ideal gravity chain vs actual progression
    print()
    print("# Gravity comparison:")
    start_root = roots[0]
    chain = gravity_chain(start_root, len(roots) - 1)
    chain_names = [name_from_pc(r) for r in chain]
    actual_names = [name_from_pc(r) for r in roots]

    print("  Theoretical gravity chain (descending 4ths):")
    print("   " + " -> ".join(chain_names))
    print("  Actual progression:")
    print("   " + " -> ".join(actual_names))

    print()
    print("# Reading guide:")
    print("  • Descending 4th (↓4) steps align with pure functional gravity.")
    print("  • Semitone (±1) steps are chromatic zone-crossings (strong direction).")
    print("  • Whole-step (±2) in-zone steps are modal / color motion.")
    print("  • Everything else is a deliberate tension against the gravity grid.")
    print()
    print("  Use this to see how the tune rides, follows, or fights the gravity field.")


# -------- HTML / MARKDOWN RENDERING --------

def _print_explain_html(chords: List[str], roots: List[PitchClass]) -> None:
    """
    HTML/Markdown-style explain output suitable for SaaS/docs.

    This is valid HTML but also mostly Markdown-friendly if pasted as-is.
    """
    # Header
    print("<article class='zt-explain'>")
    print("  <h1>Zone&ndash;Tritone EXPLAIN</h1>")
    print("  <h2>Chord progression</h2>")
    prog = " ".join(chords)
    print(f"  <p><code>{prog}</code></p>")

    # Per-chord anchors table
    print("  <h2>Per-chord gravity anchors</h2>")
    print("  <table>")
    print("    <thead>")
    print("      <tr>")
    print("        <th>#</th><th>Chord</th><th>Root</th><th>pc</th><th>Zone</th><th>Tritone axis (3,7)</th>")
    print("      </tr>")
    print("    </thead>")
    print("    <tbody>")

    for idx, (ch, r) in enumerate(zip(chords, roots)):
        root_name = name_from_pc(r)
        zname = zone_name(r)
        third_pc = (r + 4) % 12
        axis = tritone_axis(third_pc)
        a, b = axis
        axis_str = f"{name_from_pc(a)}&ndash;{name_from_pc(b)}"
        print("      <tr>")
        print(f"        <td>{idx}</td><td><code>{ch}</code></td>"
              f"<td>{root_name}</td><td>{r}</td><td>{zname}</td><td>{axis_str}</td>")
        print("      </tr>")

    print("    </tbody>")
    print("  </table>")

    if len(roots) < 2:
        print("  <p><em>Only one chord provided; no transitions to explain.</em></p>")
        print("</article>")
        return

    # Step-by-step transitions table
    print("  <h2>Step-by-step transitions</h2>")
    print("  <table>")
    print("    <thead>")
    print("      <tr>")
    print("        <th>From</th><th>To</th><th>Interval</th><th>Zone relation</th><th>Explanation</th>")
    print("      </tr>")
    print("    </thead>")
    print("    <tbody>")

    prev_root = roots[0]
    prev_name = name_from_pc(prev_root)
    prev_zone = zone_name(prev_root)

    for cur_root in roots[1:]:
        cur_name = name_from_pc(cur_root)
        cur_zone = zone_name(cur_root)
        d = interval(prev_root, cur_root)
        cross = is_zone_cross(prev_root, cur_root)
        same_zone = is_same_zone(prev_root, cur_root)
        desc_fourth = (d == 7)
        asc_fourth = (d == 5)
        hs = is_half_step(prev_root, cur_root)
        ws = is_whole_step(prev_root, cur_root)

        if cross:
            zone_relation = f"{prev_zone} → {cur_zone} (zone-cross)"
        elif same_zone:
            zone_relation = f"{prev_zone} → {cur_zone} (in-zone)"
        else:
            zone_relation = f"{prev_zone} → {cur_zone}"

        motion_tags = []
        if desc_fourth:
            motion_tags.append("↓4")
        if asc_fourth:
            motion_tags.append("↑4")
        if hs:
            motion_tags.append("±1")
        if ws:
            motion_tags.append("±2")

        motion_str = f"{d} st"
        if motion_tags:
            motion_str += " [" + ",".join(motion_tags) + "]"

        explanation = _explain_transition(prev_root, cur_root)

        print("      <tr>")
        print(f"        <td>{prev_name}</td>"
              f"<td>{cur_name}</td>"
              f"<td>{motion_str}</td>"
              f"<td>{zone_relation}</td>"
              f"<td>{explanation}</td>")
        print("      </tr>")

        prev_root = cur_root
        prev_name = cur_name
        prev_zone = cur_zone

    print("    </tbody>")
    print("  </table>")

    # Gravity comparison
    start_root = roots[0]
    chain = gravity_chain(start_root, len(roots) - 1)
    chain_names = [name_from_pc(r) for r in chain]
    actual_names = [name_from_pc(r) for r in roots]

    grav_chain_html = " &rarr; ".join(chain_names)
    actual_html = " &rarr; ".join(actual_names)

    print("  <h2>Gravity comparison</h2>")
    print("  <p><strong>Theoretical gravity chain (descending 4ths):</strong><br>")
    print(f"     <code>{grav_chain_html}</code></p>")
    print("  <p><strong>Actual progression:</strong><br>")
    print(f"     <code>{actual_html}</code></p>")

    # Reading guide
    print("  <h2>Reading guide</h2>")
    print("  <ul>")
    print("    <li><strong>Descending 4th (↓4)</strong> steps align with pure functional gravity.</li>")
    print("    <li><strong>Semitone (±1)</strong> steps are chromatic zone-crossings (strong directional pull).</li>")
    print("    <li><strong>Whole-step (±2)</strong> in-zone steps are modal / color motion.</li>")
    print("    <li>Other moves are deliberate tension against the gravity grid.</li>")
    print("  </ul>")
    print("  <p>Use this to see how the tune rides, follows, or pushes against the gravity field.</p>")
    print("</article>")


# -------- MARKDOWN RENDERING --------

def _print_explain_markdown(chords: List[str], roots: List[PitchClass]) -> None:
    """
    Markdown-style explain output (no raw HTML wrapper).
    """
    prog = " ".join(chords)
    print("# Zone–Tritone EXPLAIN")
    print()
    print("## Chord progression")
    print()
    print(f"`{prog}`")
    print()

    # Per-chord anchors table
    print("## Per-chord gravity anchors")
    print()
    print("| # | Chord | Root | pc | Zone   | Tritone axis (3,7) |")
    print("|---|-------|------|----|--------|---------------------|")

    for idx, (ch, r) in enumerate(zip(chords, roots)):
        root_name = name_from_pc(r)
        zname = zone_name(r)
        third_pc = (r + 4) % 12
        axis = tritone_axis(third_pc)
        a, b = axis
        axis_str = f"{name_from_pc(a)}–{name_from_pc(b)}"
        print(f"| {idx} | `{ch}` | {root_name} | {r} | {zname} | {axis_str} |")

    print()
    if len(roots) < 2:
        print("_Only one chord provided; no transitions to explain._")
        return

    # Step-by-step transitions
    print("## Step-by-step transitions")
    print()
    print("| From | To | Interval | Zone relation | Explanation |")
    print("|------|----|----------|---------------|-------------|")

    prev_root = roots[0]
    prev_name = name_from_pc(prev_root)
    prev_zone = zone_name(prev_root)

    for cur_root in roots[1:]:
        cur_name = name_from_pc(cur_root)
        cur_zone = zone_name(cur_root)
        d = interval(prev_root, cur_root)
        cross = is_zone_cross(prev_root, cur_root)
        same_zone = is_same_zone(prev_root, cur_root)
        desc_fourth = (d == 7)
        asc_fourth = (d == 5)
        hs = is_half_step(prev_root, cur_root)
        ws = is_whole_step(prev_root, cur_root)

        if cross:
            zone_relation = f"{prev_zone} → {cur_zone} (zone-cross)"
        elif same_zone:
            zone_relation = f"{prev_zone} → {cur_zone} (in-zone)"
        else:
            zone_relation = f"{prev_zone} → {cur_zone}"

        motion_tags = []
        if desc_fourth:
            motion_tags.append("↓4")
        if asc_fourth:
            motion_tags.append("↑4")
        if hs:
            motion_tags.append("±1")
        if ws:
            motion_tags.append("±2")

        motion_str = f"{d} st"
        if motion_tags:
            motion_str += " [" + ",".join(motion_tags) + "]"

        explanation = _explain_transition(prev_root, cur_root)

        print(f"| {prev_name} | {cur_name} | {motion_str} | {zone_relation} | {explanation} |")

        prev_root = cur_root
        prev_name = cur_name
        prev_zone = cur_zone

    # Gravity comparison
    start_root = roots[0]
    chain = gravity_chain(start_root, len(roots) - 1)
    chain_names = [name_from_pc(r) for r in chain]
    actual_names = [name_from_pc(r) for r in roots]

    grav_chain_md = " → ".join(chain_names)
    actual_md = " → ".join(actual_names)

    print()
    print("## Gravity comparison")
    print()
    print("**Theoretical gravity chain (descending 4ths):**")
    print()
    print(f"`{grav_chain_md}`")
    print()
    print("**Actual progression:**")
    print()
    print(f"`{actual_md}`")
    print()
    print("## Reading guide")
    print()
    print("- **Descending 4th (↓4)** steps align with pure functional gravity.")
    print("- **Semitone (±1)** steps are chromatic zone-crossings (strong directional pull).")
    print("- **Whole-step (±2)** in-zone steps are modal / color motion.")
    print("- Other moves are deliberate tension against the gravity grid.")
    print()
    print("Use this to see how the tune rides, follows, or pushes against the gravity field.")


# -------- EXPLAIN COMMAND DISPATCH --------


def cmd_explain(args: argparse.Namespace) -> int:
    """
    Handle the 'explain' subcommand.

    This is a teaching-oriented walkthrough of a single chord progression,
    showing zones, tritone axes, and how each step relates to gravity.

    --format controls output style: text, html, or markdown.
    --html is kept as a shorthand for --format html.
    """
    if not args.chords and not args.file:
        print("error: either --chords or --file must be provided", file=sys.stderr)
        return 1

    chords: List[str]
    if args.chords:
        chords = _parse_chord_string(args.chords)
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        chords = _load_chords_from_file(path)

    if not chords:
        print("error: no chords found to explain", file=sys.stderr)
        return 1

    roots = chord_sequence_to_roots(chords)

    # Determine format, honoring legacy --html flag if present.
    fmt = args.format
    if getattr(args, "html", False):
        fmt = "html"

    if fmt == "html":
        _print_explain_html(chords, roots)
    elif fmt == "markdown":
        _print_explain_markdown(chords, roots)
    else:
        _print_explain_text(chords, roots)

    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zt-gravity",
        description="Zone–Tritone System CLI: gravity chains and chord analysis.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # gravity subcommand
    p_grav = subparsers.add_parser(
        "gravity",
        help="Print a gravity chain (cycle of fourths) from a given root.",
    )
    p_grav.add_argument(
        "--root",
        required=True,
        help="Root note name (e.g. C, F#, Bb).",
    )
    p_grav.add_argument(
        "--steps",
        type=int,
        default=7,
        help="Number of steps to generate (default: 7).",
    )
    p_grav.set_defaults(func=cmd_gravity)

    # analyze subcommand
    p_an = subparsers.add_parser(
        "analyze",
        help="Analyze a chord sequence or file using the gravity model.",
    )
    p_an.add_argument(
        "--chords",
        type=str,
        help='Inline chord string, e.g. "Dm7 G7 Cmaj7 A7 Dm7".',
    )
    p_an.add_argument(
        "--file",
        type=str,
        help="Path to a text file containing chord symbols.",
    )
    p_an.add_argument(
        "--smoothing",
        type=float,
        default=0.1,
        help="Laplace smoothing value for transition probabilities (default: 0.1).",
    )
    p_an.add_argument(
        "--show-matrix",
        action="store_true",
        help="Print the 12x12 transition probability matrix.",
    )
    p_an.set_defaults(func=cmd_analyze)

    # explain subcommand (teaching-focused)
    p_ex = subparsers.add_parser(
        "explain",
        help="Verbose, teaching-oriented analysis of a single progression.",
    )
    p_ex.add_argument(
        "--chords",
        type=str,
        help='Inline chord string, e.g. "Dm7 G7 Cmaj7 A7 Dm7".',
    )
    p_ex.add_argument(
        "--file",
        type=str,
        help="Path to a text file containing chord symbols.",
    )
    p_ex.add_argument(
        "--format",
        choices=["text", "html", "markdown"],
        default="text",
        help="Output format: text (default), html, or markdown.",
    )
    # Legacy convenience flag: equivalent to --format html
    p_ex.add_argument(
        "--html",
        action="store_true",
        help="Shortcut for --format html (kept for convenience).",
    )
    p_ex.set_defaults(func=cmd_explain)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return args.func(args)  # type: ignore[arg-type]


if __name__ == "__main__":
    raise SystemExit(main())
