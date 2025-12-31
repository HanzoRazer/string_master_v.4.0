from __future__ import annotations

import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import List, Literal

from .engine import generate_accompaniment
from .gravity_bridge import annotate_progression, compute_transitions
from .patterns import STYLE_REGISTRY
from .config import load_program_config
from .programs import discover_programs
from .playlist import load_playlist, render_playlist_to_midi
from .exercises import load_exercise_config, run_exercise
from .daw_export import export_for_daw
from .expressive_swing import ExpressiveSpec
from .realtime import RtSpec, rt_play_cycle, practice_lock_to_clave, list_midi_ports
from .rt_bridge import RtRenderSpec, note_events_to_step_messages, gm_program_changes_at_start, truncate_events_to_cycle
from shared.zone_tritone.pc import name_from_pc


OutputFormat = Literal["text", "markdown", "json"]


# ---------------------------------------------------------------------
# Preset resolver + .ztprog loader helpers
# ---------------------------------------------------------------------


def _resolve_ztprog_program(name: str, programs_dir: str = "programs") -> str:
    """
    Resolve a program name to a .ztprog path.

    Accepts:
      - "salsa_minor_Dm"
      - "salsa_minor_Dm.ztprog"
      - "programs/salsa_minor_Dm.ztprog"

    Resolution order:
      1) If name is an existing file path, use it.
      2) Look in programs_dir for exact match (case-insensitive) with/without extension.
    """
    p = Path(name)
    if p.exists() and p.is_file():
        return str(p)

    base = name
    if base.lower().endswith(".ztprog"):
        base = base[:-7]

    root = Path(programs_dir)
    if not root.exists():
        raise SystemExit(f"Programs dir not found: {root}")

    # index all .ztprog
    files = list(root.glob("*.ztprog"))
    if not files:
        raise SystemExit(f"No .ztprog files found in: {root}")

    # case-insensitive map
    idx = {f.stem.lower(): f for f in files}
    hit = idx.get(base.lower())
    if hit:
        return str(hit)

    # allow raw filename match
    idx2 = {f.name.lower(): f for f in files}
    hit2 = idx2.get(name.lower())
    if hit2:
        return str(hit2)

    raise SystemExit(f"Program not found: {name} (searched {root}/*.ztprog)")


def _load_ztprog_yaml(path_str: str) -> dict:
    """
    Minimal, strict .ztprog loader for CLI use (tempo/chords/style/bars_per_chord).
    """
    p = Path(path_str)
    if not p.exists():
        raise SystemExit(f".ztprog not found: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid .ztprog YAML (expected mapping): {p}")
    return data


def _ztprog_get_style_comp(z: dict) -> str | None:
    """
    Supports:
      style: salsa_clave_2_3
      style: { comp: salsa_clave_2_3, bass: tumbao_major }
    """
    style = z.get("style")
    if isinstance(style, str):
        return style
    if isinstance(style, dict):
        comp = style.get("comp")
        if isinstance(comp, str):
            return comp
    return None


def _infer_clave_from_style_comp(comp: str | None) -> str | None:
    """
    Map style names to clave defaults when possible.
    We keep it heuristic + non-invasive.
    """
    if not comp:
        return None
    s = comp.lower()
    if "3_2" in s:
        return "son_3_2"
    if "2_3" in s:
        return "son_2_3"
    return None


def _infer_strict_from_style_comp(comp: str | None) -> bool:
    """Heuristic: salsa/clave styles benefit from strict lock by default."""
    if not comp:
        return False
    s = comp.lower()
    return ("salsa" in s) or ("clave" in s)


def _parse_chord_string(chord_str: str) -> List[str]:
    return [tok for tok in chord_str.strip().split() if tok]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zt-band",
        description=(
            "Smart Guitar / Zone–Tritone backing band prototype.\n"
            "Works with inline chords, chord files, .ztprog presets, and .ztplay playlists."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- create subcommand ----
    p_create = subparsers.add_parser(
        "create",
        help="Generate a backing track from a chord progression or .ztprog config.",
    )
    p_create.add_argument(
        "--config",
        type=str,
        help=(
            "Path to a .ztprog JSON/YAML config file defining chords, style, tempo, etc. "
            "When provided, --chords/--file/--style/--tempo/... are ignored."
        ),
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
        help="Tempo in BPM (default: 120). Ignored if --config is used.",
    )
    p_create.add_argument(
        "--bars-per-chord",
        type=int,
        default=1,
        help="Number of 4/4 bars each chord lasts (default: 1). Ignored if --config is used.",
    )
    p_create.add_argument(
        "--outfile",
        type=str,
        default="backing.mid",
        help="Output MIDI filename (default: backing.mid). Ignored if --config is used.",
    )
    p_create.add_argument(
        "--tritone-mode",
        choices=["none", "all_doms", "probabilistic"],
        default="none",
        help=(
            "Tritone substitution behavior for dominant chords: "
            "'none' (default), 'all_doms' (always sub), or 'probabilistic'. "
            "Ignored if --config is used."
        ),
    )
    p_create.add_argument(
        "--tritone-strength",
        type=float,
        default=1.0,
        help=(
            "Probability [0.0, 1.0] for applying tritone subs when "
            "tritone-mode=probabilistic (default: 1.0 → always). "
            "Ignored if --config is used."
        ),
    )
    p_create.add_argument(
        "--tritone-seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible tritone-sub patterns. Ignored if --config is used.",
    )
    p_create.add_argument(
        "--swing",
        type=float,
        default=0.0,
        help="Swing amount 0..1 for 8th-note offbeats (default: 0 = OFF). Ignored if --config is used.",
    )
    p_create.add_argument(
        "--humanize-ms",
        type=float,
        default=0.0,
        help="Timing jitter in milliseconds (default: 0 = OFF). Ignored if --config is used.",
    )
    p_create.add_argument(
        "--humanize-vel",
        type=int,
        default=0,
        help="Velocity jitter +/- (default: 0 = OFF). Ignored if --config is used.",
    )
    p_create.add_argument(
        "--humanize-seed",
        type=int,
        default=None,
        help="Seed for reproducible humanization. Ignored if --config is used.",
    )
    p_create.set_defaults(func=cmd_create)

    # ---- annotate subcommand ----
    p_annot = subparsers.add_parser(
        "annotate",
        help=("Print Zone–Tritone annotations and gravity diagnostics "
              "for a progression or for a .ztprog config's chords."),
    )
    p_annot.add_argument(
        "--config",
        type=str,
        help=(
            "Path to a .ztprog JSON/YAML program file. "
            "When provided, chords are taken from the config and "
            "--chords/--file are ignored."
        ),
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
        help="Optional path to save the annotation output.",
    )
    p_annot.set_defaults(func=cmd_annotate)

    # ---- styles subcommand ----
    p_styles = subparsers.add_parser(
        "styles",
        help="List available accompaniment styles.",
    )
    p_styles.set_defaults(func=cmd_styles)

    # ---- programs subcommand ----
    p_programs = subparsers.add_parser(
        "programs",
        help="List .ztprog presets in a directory (default: ./programs).",
    )
    p_programs.add_argument(
        "--dir",
        type=str,
        default="programs",
        help="Directory to scan for .ztprog files (default: programs).",
    )
    p_programs.set_defaults(func=cmd_programs)

    # ---- play subcommand ----
    p_play = subparsers.add_parser(
        "play",
        help="Render a .ztplay playlist into one long MIDI practice session.",
    )
    p_play.add_argument(
        "--playlist",
        type=str,
        required=True,
        help="Path to a .ztplay (JSON/YAML) playlist file.",
    )
    p_play.add_argument(
        "--outfile",
        type=str,
        default=None,
        help="Optional override for playlist outfile (e.g. session.mid).",
    )
    p_play.set_defaults(func=cmd_play)

    # ---- ex-list subcommand ----
    p_ex_list = subparsers.add_parser(
        "ex-list",
        help="List .ztex exercise definitions in a directory (default: ./exercises).",
    )
    p_ex_list.add_argument(
        "--dir",
        type=str,
        default="exercises",
        help="Directory to scan for .ztex files (default: exercises).",
    )
    p_ex_list.set_defaults(func=cmd_ex_list)

    # ---- ex-run subcommand ----
    p_ex_run = subparsers.add_parser(
        "ex-run",
        help="Run a single .ztex exercise (generate backing + print instructions).",
    )
    p_ex_run.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to a .ztex exercise file.",
    )
    p_ex_run.add_argument(
        "--outfile",
        type=str,
        default=None,
        help="Optional override for the MIDI filename.",
    )
    p_ex_run.set_defaults(func=cmd_ex_run)

    # ---- daw-export subcommand ----
    p_daw = subparsers.add_parser(
        "daw-export",
        help="Copy a generated MIDI into a DAW-friendly export folder with import guide.",
    )
    p_daw.add_argument(
        "--midi",
        type=str,
        required=True,
        help="Path to an existing generated MIDI file.",
    )
    p_daw.add_argument(
        "--export-root",
        type=str,
        default="exports/daw",
        help="Export root folder (default: exports/daw).",
    )
    p_daw.add_argument(
        "--no-gm",
        action="store_true",
        help="Do not inject GM program changes (for DAWs with auto-instrument detection).",
    )
    p_daw.set_defaults(func=cmd_daw_export)

    # ---- midi-ports subcommand ----
    p_ports = subparsers.add_parser(
        "midi-ports",
        help="List available MIDI input and output ports.",
    )
    p_ports.set_defaults(func=cmd_midi_ports)

    # ---- rt-play subcommand ----
    p_rt = subparsers.add_parser(
        "rt-play",
        help="Real-time playback aligned to clave grid (loop until Ctrl+C).",
    )
    p_rt.add_argument(
        "--midi-out",
        type=str,
        required=True,
        help="MIDI output port name (use 'zt-band midi-ports' to list).",
    )
    p_rt.add_argument(
        "--chords",
        type=str,
        default=None,
        help='Optional chord list to generate live accompaniment (e.g. "Dm7 G7 Cmaj7"). If omitted, click-only.',
    )
    p_rt.add_argument(
        "--file",
        type=str,
        default=None,
        help="Optional .ztprog YAML preset path. If provided, overrides --chords.",
    )
    p_rt.add_argument(
        "--style",
        type=str,
        default="salsa_clave_2_3",
        help="Accompaniment style for live generation (default: salsa_clave_2_3).",
    )
    p_rt.add_argument(
        "--bars-per-chord",
        type=int,
        default=1,
        help="Bars per chord for live generation (default: 1).",
    )
    p_rt.add_argument(
        "--rt-quantize",
        type=str,
        choices=["nearest", "down"],
        default="nearest",
        help="Quantize beat->step mapping for RT (default: nearest).",
    )
    p_rt.add_argument(
        "--bpm",
        type=float,
        default=120.0,
        help="Tempo in BPM (default: 120).",
    )
    p_rt.add_argument(
        "--grid",
        type=int,
        choices=[8, 16],
        default=16,
        help="Grid resolution: 8 (8th notes) or 16 (16th notes, default).",
    )
    p_rt.add_argument(
        "--clave",
        choices=["son_2_3", "son_3_2"],
        default="son_2_3",
        help="Clave pattern: son_2_3 (default) or son_3_2.",
    )
    p_rt.add_argument(
        "--click/--no-click",
        dest="click",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable clave click (default: enabled).",
    )
    p_rt.add_argument(
        "--program",
        type=str,
        default=None,
        help="Program name (resolves programs/*.ztprog). Example: salsa_minor_Dm",
    )
    p_rt.add_argument(
        "--programs-dir",
        type=str,
        default="programs",
        help="Directory to search for .ztprog programs (default: programs).",
    )
    p_rt.add_argument(
        "--playlist",
        type=str,
        default=None,
        help="Path to .ztplay playlist file for live rotation of programs.",
    )
    p_rt.add_argument(
        "--bar-cc",
        action="store_true",
        help="Emit MIDI CC at each bar boundary (telemetry for UI/DAW mapping).",
    )
    p_rt.add_argument(
        "--bar-cc-channel",
        type=int,
        default=15,
        help="0-15 MIDI channel for bar CC (default: 15).",
    )
    p_rt.add_argument(
        "--bar-cc-countdown",
        type=int,
        default=20,
        help="CC number for bars-remaining countdown (default: 20).",
    )
    p_rt.add_argument(
        "--bar-cc-index",
        type=int,
        default=21,
        help="CC number for bar index count-up (default: 21).",
    )
    p_rt.set_defaults(func=cmd_rt_play)

    # ---- practice subcommand ----
    p_prac = subparsers.add_parser(
        "practice",
        help="MIDI IN quantized/locked to clave grid -> MIDI OUT (loop until Ctrl+C).",
    )
    p_prac.add_argument(
        "--midi-in",
        type=str,
        required=True,
        help="MIDI input port name (use 'zt-band midi-ports' to list).",
    )
    p_prac.add_argument(
        "--midi-out",
        type=str,
        required=True,
        help="MIDI output port name.",
    )
    p_prac.add_argument(
        "--bpm",
        type=float,
        default=120.0,
        help="Tempo in BPM (default: 120).",
    )
    p_prac.add_argument(
        "--grid",
        type=int,
        choices=[8, 16],
        default=16,
        help="Grid resolution: 8 (8th notes) or 16 (16th notes, default).",
    )
    p_prac.add_argument(
        "--clave",
        choices=["son_2_3", "son_3_2"],
        default="son_2_3",
        help="Clave pattern: son_2_3 (default) or son_3_2.",
    )
    p_prac.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Strict clave lock: only clave hit-steps allowed.",
    )
    p_prac.add_argument(
        "--loose",
        action="store_true",
        default=False,
        help="Force non-strict practice (overrides any preset heuristics).",
    )
    p_prac.add_argument(
        "--reject-offgrid",
        action="store_true",
        help="In strict mode, drop notes not on allowed steps (default: snap to nearest).",
    )
    p_prac.add_argument(
        "--strict-window-ms",
        type=float,
        default=0.0,
        help="Strict mode tolerance window (ms): notes within ±window of nearest clave hit pass through unchanged (default: 0).",
    )
    p_prac.add_argument(
        "--strict-window-on-ms",
        type=float,
        default=None,
        help="Override strict window for NOTE-ON only (ms). If set, takes precedence over --strict-window-ms.",
    )
    p_prac.add_argument(
        "--strict-window-off-ms",
        type=float,
        default=None,
        help="Override strict window for NOTE-OFF only (ms). If unset, defaults to loose (max(4x base, 80ms)) to prevent choke.",
    )
    p_prac.add_argument(
        "--quantize",
        choices=["nearest", "down", "up"],
        default="nearest",
        help="Quantize mode: nearest (default), down, or up.",
    )
    p_prac.add_argument(
        "--click/--no-click",
        dest="click",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable clave click (default: enabled).",
    )
    p_prac.add_argument(
        "--file",
        type=str,
        default=None,
        help="Optional .ztprog YAML preset path to pull tempo/style defaults.",
    )
    p_prac.add_argument(
        "--program",
        type=str,
        default=None,
        help="Program name (resolves programs/*.ztprog). Example: salsa_minor_Dm",
    )
    p_prac.add_argument(
        "--programs-dir",
        type=str,
        default="programs",
        help="Directory to search for .ztprog programs (default: programs).",
    )
    p_prac.set_defaults(func=cmd_practice)

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
    # Prefer config if provided
    if args.config:
        cfg = load_program_config(args.config)

        if cfg.style not in STYLE_REGISTRY:
            print(
                f"error: style '{cfg.style}' from config is not a known style. "
                "Use 'zt-band styles' to list available styles.",
                file=sys.stderr,
            )
            return 1

        generate_accompaniment(
            chord_symbols=cfg.chords,
            style_name=cfg.style,
            tempo_bpm=cfg.tempo,
            bars_per_chord=cfg.bars_per_chord,
            outfile=cfg.outfile,
            tritone_mode=cfg.tritone_mode,
            tritone_strength=cfg.tritone_strength,
            tritone_seed=cfg.tritone_seed,
        )

        label = cfg.name or args.config
        print(f"Created backing track from config '{label}': {cfg.outfile}")
        return 0

    # Fallback: inline/file chords + CLI flags
    chords = _load_chords_from_args(args)

    if args.style not in STYLE_REGISTRY:
        print(
            f"error: unknown style '{args.style}'. "
            "Use 'zt-band styles' to list available styles.",
            file=sys.stderr,
        )
        return 1

    # Build expressive spec if any parameter is non-zero
    expressive: ExpressiveSpec | None = None
    if args.swing or args.humanize_ms or args.humanize_vel:
        expressive = ExpressiveSpec(
            swing=args.swing,
            humanize_ms=args.humanize_ms,
            humanize_vel=args.humanize_vel,
            seed=args.humanize_seed,
        )

    generate_accompaniment(
        chord_symbols=chords,
        style_name=args.style,
        tempo_bpm=args.tempo,
        bars_per_chord=args.bars_per_chord,
        outfile=args.outfile,
        tritone_mode=args.tritone_mode,
        tritone_strength=args.tritone_strength,
        tritone_seed=args.tritone_seed,
        expressive=expressive,
    )

    print(f"Created backing track: {args.outfile}")
    return 0


# ------------------------
# annotate command
# ------------------------


def _format_annotations_text(annotated, transitions) -> str:
    lines: List[str] = []
    lines.append("Chord annotations:")
    lines.append("idx | chord    | root | pc | zone     | tritone axis | gravity-> | on_chain")
    lines.append("----+----------+------+----+----------+--------------+-----------+---------")

    for idx, ac in enumerate(annotated):
        root_name = name_from_pc(ac.root_pc)
        axis_a, axis_b = ac.axis
        axis_str = f"{name_from_pc(axis_a)}–{name_from_pc(axis_b)}"
        grav_str = "-"
        if ac.gravity_target is not None:
            grav_str = name_from_pc(ac.gravity_target)
        lines.append(
            f"{idx:>3} | {ac.chord.symbol:<8} | {root_name:<4} | {ac.root_pc:>2} "
            f"| {ac.zone:<8} | {axis_str:<12} | {grav_str:<9} | {str(ac.is_on_chain):<7}"
        )

    if transitions:
        lines.append("")
        lines.append("Stepwise transitions:")
        lines.append("from->to | int(st) | zones                 | tags")
        lines.append("---------+---------+-----------------------+--------------------------")
        for tr in transitions:
            from_name = name_from_pc(tr.from_root)
            to_name = name_from_pc(tr.to_root)
            zone_pair = f"{tr.from_zone} -> {tr.to_zone}"

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
                f"{from_name:>4}->{to_name:<3} | {tr.interval_semitones:>3}     "
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
            zone_pair = f"{tr.from_zone} -> {tr.to_zone}"

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
    # Prefer config if provided
    if args.config:
        cfg = load_program_config(args.config)
        chords = cfg.chords
    else:
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

    print(out)

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


# ------------------------
# programs command
# ------------------------


def cmd_programs(args: argparse.Namespace) -> int:
    root = args.dir
    descs = discover_programs(root)

    print(f"Scanning '{root}' for .ztprog files...\n")

    if not descs:
        print("No .ztprog presets found.")
        return 0

    print("path                         | name                     | style        | tempo | status")
    print("-----------------------------+--------------------------+--------------+-------+-------------------------")

    for d in descs:
        rel = d.path
        try:
            rel = d.path.relative_to(Path(root))
        except ValueError:
            rel = d.path

        if d.config is None:
            print(
                f"{str(rel):<29} | {'-':<24} | {'-':<12} | {'-':<5} | ERROR: {d.error}"
            )
            continue

        cfg = d.config
        name = cfg.name or "-"
        print(
            f"{str(rel):<29} | {name:<24} | {cfg.style:<12} | {cfg.tempo:>5} | OK"
        )

    return 0


# ------------------------
# play command
# ------------------------


def cmd_play(args: argparse.Namespace) -> int:
    playlist_path = args.playlist
    pl = load_playlist(playlist_path)

    outfile = args.outfile or pl.outfile or "playlist_session.mid"
    render_playlist_to_midi(pl, outfile=outfile)

    label = pl.name or playlist_path
    print(f"Rendered playlist '{label}' to: {outfile}")
    return 0


# ------------------------
# ex-list / ex-run commands
# ------------------------


def cmd_ex_list(args: argparse.Namespace) -> int:
    root = Path(args.dir)
    print(f"Scanning '{root}' for .ztex exercises...\n")

    if not root.exists() or not root.is_dir():
        print("No exercises directory found.")
        return 0

    files = sorted(root.glob("*.ztex"))
    if not files:
        print("No .ztex exercise files found.")
        return 0

    print("file                         | name                          | type")
    print("-----------------------------+-------------------------------+---------------------")

    for path in files:
        try:
            ex = load_exercise_config(path)
            rel = path.relative_to(root)
            print(f"{str(rel):<29} | {ex.name:<29} | {ex.exercise_type:<19}")
        except Exception as exc:  # noqa: BLE001
            print(f"{path.name:<29} | ERROR: {exc}")

    return 0


def cmd_ex_run(args: argparse.Namespace) -> int:
    ex_path = args.file
    outfile = args.outfile

    ex = load_exercise_config(ex_path)
    midi_out = run_exercise(ex, outfile=outfile)

    print(f"\nExercise complete. MIDI written to: {midi_out}")
    return 0


# ------------------------
# daw-export command
# ------------------------


def cmd_daw_export(args: argparse.Namespace) -> int:
    res = export_for_daw(
        source_midi_path=args.midi,
        export_root=args.export_root,
        title="ZT-Band DAW Export",
        inject_gm=not args.no_gm,
    )
    print("OK: DAW export written")
    print(f"  dir:  {res.export_dir}")
    print(f"  midi: {res.midi_path}")
    print(f"  doc:  {res.guide_path}")
    return 0


# ------------------------
# midi-ports command
# ------------------------


def cmd_midi_ports(args: argparse.Namespace) -> int:
    inputs, outputs = list_midi_ports()

    print("MIDI Input Ports:")
    if inputs:
        for name in inputs:
            print(f"  {name}")
    else:
        print("  (none found)")

    print("\nMIDI Output Ports:")
    if outputs:
        for name in outputs:
            print(f"  {name}")
    else:
        print("  (none found)")

    return 0


# ------------------------
# rt-play command
# ------------------------


def cmd_rt_play(args: argparse.Namespace) -> int:
    # Handle --playlist mode (live rotation)
    if getattr(args, "playlist", None):
        from .rt_playlist import rt_play_playlist
        
        # Detect explicit CLI bpm
        explicit = getattr(args, "_explicit_args", set())
        bpm_explicit = ("--bpm" in explicit) or any(str(x).startswith("--bpm=") for x in explicit)
        bpm_override = args.bpm if bpm_explicit else None
        
        try:
            rt_play_playlist(
                playlist_file=args.playlist,
                midi_out=args.midi_out,
                bpm_override=bpm_override,
                grid=args.grid,
                clave=args.clave,
                click=args.click,
                rt_quantize=args.rt_quantize,
            )
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        return 0

    # --program resolves to --file
    if getattr(args, "program", None) and not getattr(args, "file", None):
        args.file = _resolve_ztprog_program(str(args.program), programs_dir=str(args.programs_dir))

    # Helper to load .ztprog YAML
    def _load_ztprog(path_str: str) -> dict:
        p = Path(path_str)
        if not p.exists():
            raise SystemExit(f"rt-play --file not found: {p}")
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(f"rt-play --file invalid YAML (expected mapping): {p}")
        return data

    # Resolve source of live program: --file wins over --chords
    live_chords = None
    live_style = str(args.style)
    live_bars_per_chord = int(args.bars_per_chord)
    live_bpm = float(args.bpm)

    if args.file:
        z = _load_ztprog(str(args.file))
        live_chords = z.get("chords", None)
        if not isinstance(live_chords, list) or not all(isinstance(x, str) for x in live_chords):
            raise SystemExit("rt-play --file must contain 'chords: [\"Dm7\", \"G7\", ...]'")
        # Tempo precedence: file tempo unless CLI explicitly set --bpm/--bpm=...
        argv_flags = getattr(args, "_explicit_args", set())
        cli_bpm_explicit = ("--bpm" in argv_flags) or any(str(x).startswith("--bpm=") for x in argv_flags)
        if not cli_bpm_explicit:
            if isinstance(z.get("tempo"), (int, float)):
                live_bpm = float(z["tempo"])
        if isinstance(z.get("bars_per_chord"), int):
            live_bars_per_chord = int(z["bars_per_chord"])
        style_obj = z.get("style", {})
        if isinstance(style_obj, dict) and isinstance(style_obj.get("comp"), str):
            live_style = style_obj["comp"]
        elif isinstance(style_obj, str):
            live_style = style_obj

    elif args.chords:
        live_chords = [c.strip() for c in args.chords.split() if c.strip()]

    # Build RtSpec with resolved bpm
    spec = RtSpec(
        midi_out=args.midi_out,
        bpm=live_bpm,
        grid=args.grid,
        clave=args.clave,
        click=args.click,
        bar_cc_enabled=getattr(args, "bar_cc", False),
        bar_cc_channel=getattr(args, "bar_cc_channel", 15),
        bar_cc_countdown=getattr(args, "bar_cc_countdown", 20),
        bar_cc_index=getattr(args, "bar_cc_index", 21),
    )

    events = []

    # If we have chords (from --file or --chords), generate live accompaniment
    if live_chords:
        chord_symbols = list(live_chords)
        if not chord_symbols:
            print("error: chord list parsed empty", file=sys.stderr)
            return 1

        if live_style not in STYLE_REGISTRY:
            print(f"error: unknown style '{live_style}'", file=sys.stderr)
            return 1

        # Generate comp + bass events using existing engine
        comp_events, bass_events = generate_accompaniment(
            chord_symbols=chord_symbols,
            style_name=live_style,
            tempo_bpm=int(round(spec.bpm)),
            bars_per_chord=live_bars_per_chord,
            outfile=None,  # No file output
            tritone_mode="none",
        )

        # Truncate to 2-bar cycle for looping
        bars_per_cycle = 2
        comp_events = truncate_events_to_cycle(comp_events, bars_per_cycle)
        bass_events = truncate_events_to_cycle(bass_events, bars_per_cycle)

        # Convert NoteEvents to step-indexed RT messages
        steps_per_cycle = int(args.grid) * bars_per_cycle
        rts = RtRenderSpec(
            bpm=spec.bpm,
            grid=args.grid,
            bars_per_cycle=bars_per_cycle,
            quantize=args.rt_quantize,
        )

        events.extend(gm_program_changes_at_start())
        events.extend(note_events_to_step_messages(comp_events, spec=rts, steps_per_cycle=steps_per_cycle))
        events.extend(note_events_to_step_messages(bass_events, spec=rts, steps_per_cycle=steps_per_cycle))

        src = f"file={args.file}" if args.file else "chords=inline"
        print(f"RT Play: live mode")
        print(f"  source: {src}")
        print(f"  chords: {' '.join(chord_symbols)}")
        print(f"  style:  {live_style}")
        print(f"  bpm:    {spec.bpm}")
        print(f"  bars/chord: {live_bars_per_chord}")
        print(f"  events: {len(events)} (comp+bass+GM)")
    else:
        print("RT Play: click-only mode")

    try:
        rt_play_cycle(events=events, spec=spec)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    return 0


# ------------------------
# practice command
# ------------------------


def cmd_practice(args: argparse.Namespace) -> int:
    # Detect explicit CLI flags for precedence
    explicit = getattr(args, "_explicit_args", set())
    bpm_explicit = ("--bpm" in explicit) or any(str(x).startswith("--bpm=") for x in explicit)
    clave_explicit = ("--clave" in explicit) or any(str(x).startswith("--clave=") for x in explicit)
    strict_explicit = ("--strict" in explicit)
    loose_explicit = ("--loose" in explicit)

    # Resolve --program to file path
    ztprog_path = None
    if getattr(args, "program", None):
        ztprog_path = _resolve_ztprog_program(str(args.program), programs_dir=str(args.programs_dir))
    elif getattr(args, "file", None):
        ztprog_path = str(args.file)

    # Pull defaults from .ztprog if provided
    if ztprog_path:
        z = _load_ztprog_yaml(ztprog_path)

        if not bpm_explicit and isinstance(z.get("tempo"), (int, float)):
            args.bpm = float(z["tempo"])

        if not clave_explicit:
            comp = _ztprog_get_style_comp(z)
            inferred = _infer_clave_from_style_comp(comp)
            if inferred:
                args.clave = inferred

        # Auto-enable strict for salsa/clave styles unless user explicitly chose strict/loose
        if not strict_explicit and not loose_explicit:
            comp = _ztprog_get_style_comp(z)
            if _infer_strict_from_style_comp(comp):
                args.strict = True

    # Loose always wins (belt & suspenders)
    if loose_explicit:
        args.strict = False

    spec = RtSpec(
        midi_out=args.midi_out,
        midi_in=args.midi_in,
        bpm=args.bpm,
        grid=args.grid,
        clave=args.clave,
        practice_strict=args.strict,
        practice_window_ms=args.strict_window_ms,
        practice_window_on_ms=args.strict_window_on_ms,
        practice_window_off_ms=args.strict_window_off_ms,
        practice_reject_offgrid=args.reject_offgrid,
        practice_quantize=args.quantize,
        click=args.click,
    )

    try:
        practice_lock_to_clave(spec)
    except (RuntimeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)
    # Track explicit flags for precedence decisions (belt & suspenders).
    # This is intentionally simple: only used for a few precedence checks.
    args._explicit_args = set(a for a in argv if a.startswith("--"))  # type: ignore[attr-defined]
    return args.func(args)  # type: ignore[arg-type]


if __name__ == "__main__":
    raise SystemExit(main())
