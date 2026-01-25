"""
rt_playlist.py -- Live playlist runner for rt-play --playlist

Orchestrates sequential playback of .ztplay items, switching
programs at bar boundaries without engine rewrite.
"""

import argparse
import importlib.metadata
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .ui.manual_intent import ManualBandControls, build_groove_intent_from_controls
from .groove import IntentContext, ManualIntentProvider, AnalyzerIntentProvider
from .adapters.arranger_intent_adapter import build_arranger_control_plan
from .arranger.performance_controls import derive_controls

from .arranger.runtime import select_pattern_from_intent
from .engine import generate_accompaniment
from .patterns import STYLE_REGISTRY
from .realtime import RtSpec, rt_play_cycle
from .rt_bridge import (
    RtRenderSpec,
    gm_program_changes_at_start,
    note_events_to_step_messages,
    truncate_events_to_cycle,
)


@dataclass
class PlaylistItem:
    """Single item in a .ztplay playlist."""
    name: str
    file: str
    repeats: int = 1


@dataclass
class Playlist:
    """Parsed .ztplay playlist."""
    id: str
    title: str
    items: list[PlaylistItem]
    defaults: dict[str, Any]


def load_ztplay(path: str) -> Playlist:
    """Load and parse a .ztplay YAML file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Playlist not found: {p}")

    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid playlist YAML (expected mapping): {p}")

    items_raw = data.get("items", [])
    if not isinstance(items_raw, list):
        raise ValueError(f"Playlist 'items' must be a list: {p}")

    items = []
    for i, item in enumerate(items_raw):
        if not isinstance(item, dict):
            raise ValueError(f"Playlist item {i} must be a mapping: {p}")
        items.append(PlaylistItem(
            name=item.get("name", f"item_{i}"),
            file=item.get("file", ""),
            repeats=item.get("repeats", 1),
        ))

    return Playlist(
        id=data.get("id", "unknown"),
        title=data.get("title", "Untitled Playlist"),
        items=items,
        defaults=data.get("defaults", {}),
    )


def _load_ztprog(path: str, playlist_dir: Path) -> dict:
    """Load a .ztprog YAML file, resolving relative paths from playlist dir."""
    # Resolve relative to playlist directory
    prog_path = Path(path)
    if not prog_path.is_absolute():
        prog_path = playlist_dir / path

    if not prog_path.exists():
        raise FileNotFoundError(f"Program not found: {prog_path}")

    data = yaml.safe_load(prog_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid .ztprog YAML: {prog_path}")

    return data


def _manual_controls_from_env() -> ManualBandControls:
    """
    Read manual band controls from environment variables.

    All optional: if absent, defaults apply.

    Env vars:
        SG_MODE: follow|assist|stabilize|challenge|recover
        SG_TIGHTNESS: 0.0-1.0
        SG_ASSIST: 0.0-1.0
        SG_EXPRESSION: 0.0-1.0
        SG_HUMANIZE_MS: float (e.g., 7.5)
        SG_BIAS: ahead|behind|neutral
        SG_HORIZON_MS: int (e.g., 2000)
        SG_CONFIDENCE: 0.0-1.0
    """
    mode = os.getenv("SG_MODE", "follow").strip().lower()
    if mode not in ("follow", "assist", "stabilize", "challenge", "recover"):
        mode = "follow"

    def f(name: str, default: float) -> float:
        try:
            return float(os.getenv(name, str(default)))
        except Exception:
            return default

    bias = os.getenv("SG_BIAS", "neutral").strip().lower()
    if bias not in ("ahead", "behind", "neutral"):
        bias = "neutral"

    try:
        horizon = int(float(os.getenv("SG_HORIZON_MS", "2000")))
    except Exception:
        horizon = 2000

    return ManualBandControls(
        mode=mode,  # type: ignore[arg-type]
        tightness=f("SG_TIGHTNESS", 0.6),
        assist=f("SG_ASSIST", 0.6),
        expression=f("SG_EXPRESSION", 0.5),
        humanize_ms=f("SG_HUMANIZE_MS", 7.5),
        anticipation_bias=bias,  # type: ignore[arg-type]
        horizon_ms=horizon,
        confidence=f("SG_CONFIDENCE", 0.85),
    )


# =============================================================================
# PRESETS
# =============================================================================

_PRESETS: dict[str, dict[str, object]] = {
    # A tight practice pocket
    "tight": {
        "mode": "stabilize",
        "tightness": 0.95,
        "expression": 0.30,
        "assist": 0.60,
        "humanize_ms": 2.0,
        "bias": "neutral",
        "confidence": 0.85,
        "horizon_ms": 2000,
    },
    # A looser jam feel
    "loose": {
        "mode": "follow",
        "tightness": 0.45,
        "expression": 0.60,
        "assist": 0.50,
        "humanize_ms": 9.0,
        "bias": "neutral",
        "confidence": 0.85,
        "horizon_ms": 2000,
    },
    # High energy / density
    "challenge": {
        "mode": "challenge",
        "tightness": 0.20,
        "expression": 0.85,
        "assist": 0.95,
        "humanize_ms": 6.0,
        "bias": "neutral",
        "confidence": 0.85,
        "horizon_ms": 2000,
    },
    # Simplify + give space
    "recover": {
        "mode": "recover",
        "tightness": 0.70,
        "expression": 0.20,
        "assist": 0.80,
        "humanize_ms": 4.0,
        "bias": "neutral",
        "confidence": 0.85,
        "horizon_ms": 2000,
    },
}


def _print_presets_and_exit() -> None:
    """Print available presets and exit."""
    print("Available presets:\n")
    for name, cfg in _PRESETS.items():
        print(f"{name}")
        print(f"  mode={cfg.get('mode', '')}")
        print(f"  tightness={cfg.get('tightness', '')}")
        print(f"  expression={cfg.get('expression', '')}")
        print(f"  assist={cfg.get('assist', '')}")
        print(f"  humanize-ms={cfg.get('humanize_ms', '')}")
        print(f"  bias={cfg.get('bias', '')}")
        print()
    print("Usage:")
    print("  zt-band rt-play song.yaml --preset tight")
    print("  zt-band rt-play song.yaml --preset loose --tightness 0.4")
    print()
    print("Explicit flags override presets. See --help for all options.")
    raise SystemExit(0)


def _pkg_version_or_unknown(pkg_name: str = "smart-guitar") -> str:
    """Best-effort package version lookup."""
    try:
        return importlib.metadata.version(pkg_name)
    except Exception:
        return "unknown"


def _print_engine_banner_once() -> None:
    """Print engine version banner once at startup."""
    pkg = _pkg_version_or_unknown()
    print(f"[engine] groove=v1 arranger=v1 pkg={pkg}")


def _dump_json_compact(obj: object) -> str:
    """JSON dump with nice formatting."""
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)


def _print_dry_run(
    *,
    intent: dict | None,
    arranger_plan: object | None,
    perf: object | None,
    chosen_style: str | None,
) -> None:
    """Print resolved intent + derived controls for dry-run mode."""
    print("\n[dry-run] --- resolved ---")

    if chosen_style is not None:
        print(f"[dry-run] chosen_style: {chosen_style}")

    if intent is None:
        print("[dry-run] intent: None (falling back to YAML style)")
    else:
        print("[dry-run] intent:")
        print(_dump_json_compact(intent))

    if arranger_plan is None:
        print("[dry-run] arranger_plan: None")
    else:
        try:
            d = arranger_plan.__dict__
            print("[dry-run] arranger_plan:")
            print(_dump_json_compact(d))
        except Exception:
            print(f"[dry-run] arranger_plan: {arranger_plan!r}")

    if perf is None:
        print("[dry-run] performance_controls: None")
    else:
        try:
            d = perf.__dict__
            print("[dry-run] performance_controls:")
            print(_dump_json_compact(d))
        except Exception:
            print(f"[dry-run] performance_controls: {perf!r}")

    print("[dry-run] exit: ok\n")


def _print_dry_run_banner(*, all_programs: bool, compact: bool = False) -> None:
    """Print dry-run mode banner."""
    if all_programs:
        mode_suffix = " (compact)" if compact else ""
        print(f"\n[dry-run] mode: all-programs{mode_suffix} (no playback)\n")
    else:
        print("\n[dry-run] mode: single-program (no playback)\n")


def _compact_line(
    *,
    idx: int,
    total: int,
    prog_name: str,
    yaml_style: str,
    chosen_style: str,
    ok: bool,
) -> str:
    """Format a one-liner for compact dry-run output."""
    status = "OK" if ok else "FAIL"
    if chosen_style != yaml_style:
        style_part = f"style={yaml_style}→{chosen_style}"
    else:
        style_part = f"style={chosen_style}"
    return f"[dry-run] {idx}/{total} {status} {prog_name}: {style_part}"


def _dry_run_status(
    *,
    yaml_style: str,
    chosen_style: str,
    intent_ok: bool,
    plan_ok: bool,
    perf_ok: bool,
) -> tuple[bool, list[str]]:
    """Determine if dry-run passed and collect any failure reasons."""
    reasons: list[str] = []
    if not intent_ok:
        reasons.append("intent_error")
    if not plan_ok:
        reasons.append("plan_error")
    if not perf_ok:
        reasons.append("perf_error")
    if chosen_style != yaml_style:
        reasons.append("style_overridden")
    ok = len(reasons) == 0
    return ok, reasons


@dataclass
class DryRunStats:
    """Counters for compact dry-run summary."""
    total: int = 0
    ok_count: int = 0
    fail_count: int = 0
    overridden_count: int = 0
    intent_none_count: int = 0
    intent_error_count: int = 0
    plan_error_count: int = 0
    perf_error_count: int = 0

    def record(
        self,
        *,
        ok: bool,
        reasons: list[str],
        intent_is_none: bool,
    ) -> None:
        """Update counters for one program."""
        self.total += 1
        if ok:
            self.ok_count += 1
        else:
            self.fail_count += 1
        if "style_overridden" in reasons:
            self.overridden_count += 1
        if "intent_error" in reasons:
            self.intent_error_count += 1
        if "plan_error" in reasons:
            self.plan_error_count += 1
        if "perf_error" in reasons:
            self.perf_error_count += 1
        if intent_is_none:
            self.intent_none_count += 1

    def summary_line(self) -> str:
        """Format summary line for compact output."""
        return (
            f"[dry-run] summary: programs={self.total} "
            f"ok={self.ok_count} fail={self.fail_count} "
            f"overridden={self.overridden_count} intent_none={self.intent_none_count}"
        )

    @property
    def any_fail(self) -> bool:
        """True if any program failed."""
        return self.fail_count > 0


def _parse_band_control_args(argv=None):
    """
    Tiny CLI layer for manual band controls.
    Unknown args are ignored so existing CLI behavior is preserved.
    """
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("--list-presets", action="store_true", dest="list_presets")
    parser.add_argument("--preset", choices=["tight", "loose", "challenge", "recover"])
    parser.add_argument("--mode", choices=["follow", "assist", "stabilize", "challenge", "recover"])
    parser.add_argument("--tightness", type=float)
    parser.add_argument("--assist", type=float)
    parser.add_argument("--expression", type=float)
    parser.add_argument("--humanize-ms", type=float, dest="humanize_ms")
    parser.add_argument("--bias", choices=["ahead", "behind", "neutral"])
    parser.add_argument("--confidence", type=float)
    parser.add_argument("--horizon-ms", type=int, dest="horizon_ms")
    parser.add_argument("--intent-source", choices=["manual", "analyzer", "none"], default="manual")
    parser.add_argument("--profile-id", default="rt_playlist_manual")
    parser.add_argument("--profile-store-dir", default=".sg_profiles")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print resolved intent + derived plans/controls, then exit (no playback).",
    )
    parser.add_argument(
        "--all-programs",
        action="store_true",
        help="With --dry-run: print resolution for every program in the YAML, then exit.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="With --dry-run --all-programs: print one line per program; expand details only on errors.",
    )

    args, _ = parser.parse_known_args(argv)

    # Constraint: --all-programs requires --dry-run
    if getattr(args, "all_programs", False) and not getattr(args, "dry_run", False):
        raise SystemExit("--all-programs is only valid with --dry-run")

    # Constraint: --compact requires --dry-run --all-programs
    if getattr(args, "compact", False) and not (getattr(args, "dry_run", False) and getattr(args, "all_programs", False)):
        raise SystemExit("--compact is only valid with --dry-run --all-programs")

    return args


def _manual_controls_from_cli(argv=None) -> ManualBandControls:
    """
    Build ManualBandControls from CLI arguments.

    Priority: CLI flag > preset > env var > default

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        ManualBandControls with values merged in priority order
    """
    args = _parse_band_control_args(argv)

    # Handle --list-presets early exit
    if getattr(args, "list_presets", False):
        _print_presets_and_exit()

    env_controls = _manual_controls_from_env()

    # Start with preset if specified
    base: dict[str, object] = {}
    if getattr(args, "preset", None):
        base = dict(_PRESETS[args.preset])

    def pick(cli_name: str, env_val):
        # CLI flag overrides preset; preset overrides env
        cli_val = getattr(args, cli_name, None)
        if cli_val is not None:
            return cli_val
        if cli_name in base:
            return base[cli_name]
        return env_val

    return ManualBandControls(
        mode=pick("mode", env_controls.mode),  # type: ignore[arg-type]
        tightness=float(pick("tightness", env_controls.tightness)),
        assist=float(pick("assist", env_controls.assist)),
        expression=float(pick("expression", env_controls.expression)),
        humanize_ms=float(pick("humanize_ms", env_controls.humanize_ms)),
        anticipation_bias=pick("bias", env_controls.anticipation_bias),  # type: ignore[arg-type]
        horizon_ms=int(pick("horizon_ms", env_controls.horizon_ms)),
        confidence=float(pick("confidence", env_controls.confidence)),
    )


def _maybe_override_style_with_intent(
    *,
    prog_style: str,
    intent: dict | None,
) -> str:
    """
    If an intent is available, use arranger selection to override style.
    Otherwise, return prog_style unchanged.

    Never raises — falls back silently on any error to avoid breaking playback.
    """
    if not intent:
        return prog_style
    try:
        chosen = select_pattern_from_intent(
            intent,
            patterns=list(STYLE_REGISTRY.values()),
            seed=str(intent.get("profile_id", "default")),
        )
        chosen_id = getattr(chosen, "id", None)
        if isinstance(chosen_id, str) and chosen_id in STYLE_REGISTRY:
            return chosen_id
    except Exception as e:
        # Never break playback
        print(f"[rt_playlist] arranger selection failed; using '{prog_style}' ({e})")
    return prog_style


def rt_play_playlist(
    playlist_file: str,
    midi_out: str,
    bpm_override: float | None = None,
    grid: int = 16,
    clave: str = "son_2_3",
    click: bool = True,
    rt_quantize: str = "nearest",
    bar_cc_enabled: bool = False,
    bar_cc_channel: int = 15,
    bar_cc_countdown: int = 20,
    bar_cc_index: int = 21,
    bar_cc_section: int = 22,
) -> None:
    """
    Play a .ztplay playlist live, rotating through items at bar boundaries.

    Each item is played for its specified repeats before moving to the next.
    The rt_play_cycle is called per-item, so switching happens cleanly.

    If bar_cc_enabled, emits:
    - CC#section at start of each item (item index 0, 1, 2, ...)
    - CC#countdown/index at each bar boundary
    """
    # Print engine banner once at startup
    _print_engine_banner_once()

    playlist = load_ztplay(playlist_file)
    playlist_dir = Path(playlist_file).parent.resolve()

    # Get defaults from playlist
    defaults = playlist.defaults
    default_bpm = defaults.get("tempo", 120.0)
    default_bars_per_chord = defaults.get("bars_per_chord", 2)
    default_style = defaults.get("style", "swing_basic")

    print(f"RT Playlist: {playlist.title}")
    print(f"  items: {len(playlist.items)}")
    print(f"  output: {midi_out}")
    if bar_cc_enabled:
        print(f"  bar CC: ch={bar_cc_channel}, countdown=CC#{bar_cc_countdown}, index=CC#{bar_cc_index}, section=CC#{bar_cc_section}")
    print()

    # Open MIDI port for section markers (reused per item)
    try:
        import mido
        section_port = mido.open_output(midi_out) if bar_cc_enabled else None
    except Exception:
        section_port = None

    # Dry-run stats (compact mode)
    dry_run_stats = DryRunStats()

    try:
        for item_idx, item in enumerate(playlist.items):
            if not item.file:
                print(f"  [{item_idx + 1}] {item.name}: skipped (no file)")
                continue

            # Load the program
            try:
                prog = _load_ztprog(item.file, playlist_dir)
            except (FileNotFoundError, ValueError) as e:
                print(f"  [{item_idx + 1}] {item.name}: error loading - {e}")
                continue

            # Extract program settings
            prog_name = prog.get("name", item.name)
            prog_chords = prog.get("chords", [])
            prog_tempo = prog.get("tempo", default_bpm)
            prog_bars_per_chord = prog.get("bars_per_chord", default_bars_per_chord)

            # Style extraction
            style_obj = prog.get("style", default_style)
            if isinstance(style_obj, dict):
                prog_style = style_obj.get("comp", default_style)
            else:
                prog_style = str(style_obj)

            # Apply overrides
            effective_bpm = bpm_override if bpm_override else prog_tempo

            # Validate
            if not prog_chords or not isinstance(prog_chords, list):
                print(f"  [{item_idx + 1}] {prog_name}: skipped (no chords)")
                continue

            if prog_style not in STYLE_REGISTRY:
                print(f"  [{item_idx + 1}] {prog_name}: unknown style '{prog_style}', using swing_basic")
                prog_style = "swing_basic"

            # --- Intent-driven style selection (governed) ---
            # Build intent from provider (manual, analyzer, or none)
            controls = _manual_controls_from_cli()
            band_args = _parse_band_control_args()

            # Capture YAML style before any override
            yaml_style = prog_style
            
            # Build provider based on --intent-source
            provider = None
            if band_args.intent_source == "manual":
                provider = ManualIntentProvider(
                    controls=controls,
                    profile_id=band_args.profile_id,
                )
            elif band_args.intent_source == "analyzer":
                provider = AnalyzerIntentProvider(
                    profile_store_dir=Path(band_args.profile_store_dir),
                )
            # else: intent_source == "none", provider stays None
            
            # Produce intent from provider, track success
            intent = None
            intent_ok = True
            if provider is not None:
                try:
                    ctx = IntentContext(
                        profile_id=band_args.profile_id,
                        bpm=float(effective_bpm),
                        program_name=prog_name,
                        item_idx=item_idx,
                    )
                    intent = provider.get_intent(ctx)
                except Exception:
                    intent_ok = False
                    intent = None
            
            prog_style = _maybe_override_style_with_intent(
                prog_style=prog_style,
                intent=intent,
            )
            chosen_style = prog_style

            # --- Derive arranger + performance controls ---
            arranger_plan = None
            perf = None
            plan_ok = True
            perf_ok = True
            if intent is not None:
                try:
                    arranger_plan = build_arranger_control_plan(intent)
                except Exception:
                    plan_ok = False
                    arranger_plan = None

                if arranger_plan is not None:
                    try:
                        perf = derive_controls(
                            tightness=float(getattr(arranger_plan, "tightness", 0.6)),
                            expression_window=float(getattr(arranger_plan, "expression_window", 0.5)),
                            assist_gain=float(getattr(arranger_plan, "assist_gain", 0.6)),
                            anticipation_bias=str(getattr(arranger_plan, "anticipation_bias", "neutral")),
                        )
                    except Exception:
                        perf_ok = False
                        perf = None

            # --- Dry-run exit hook ---
            if getattr(band_args, "dry_run", False):
                is_all = getattr(band_args, "all_programs", False)
                is_compact = getattr(band_args, "compact", False)
                total_programs = len(playlist.items)

                # Print banner on first program
                if item_idx == 0:
                    _print_dry_run_banner(all_programs=is_all, compact=is_compact)

                if is_all and is_compact:
                    # Compact mode: one-liner per program, expand on error
                    ok, reasons = _dry_run_status(
                        yaml_style=yaml_style,
                        chosen_style=chosen_style,
                        intent_ok=intent_ok,
                        plan_ok=plan_ok,
                        perf_ok=perf_ok,
                    )
                    # Record stats for summary
                    dry_run_stats.record(
                        ok=ok,
                        reasons=reasons,
                        intent_is_none=(intent is None),
                    )
                    line = _compact_line(
                        idx=item_idx + 1,
                        total=total_programs,
                        prog_name=prog_name,
                        yaml_style=yaml_style,
                        chosen_style=chosen_style,
                        ok=ok,
                    )
                    if ok:
                        print(line)
                    else:
                        print(line + f" reasons={reasons}")
                        _print_dry_run(
                            intent=intent,
                            arranger_plan=arranger_plan,
                            perf=perf,
                            chosen_style=chosen_style,
                        )
                    continue  # next program, no playback

                elif is_all:
                    # Multi-program verbose mode: print and continue to next
                    print(f"[dry-run] program: {prog_name} (index={item_idx + 1}/{total_programs})")
                    _print_dry_run(
                        intent=intent,
                        arranger_plan=arranger_plan,
                        perf=perf,
                        chosen_style=chosen_style,
                    )
                    continue  # next program, no playback
                else:
                    # Single-program mode: print and exit
                    _print_dry_run(
                        intent=intent,
                        arranger_plan=arranger_plan,
                        perf=perf,
                        chosen_style=chosen_style,
                    )
                    raise SystemExit(0)

            # Generate events for this program
            comp_events, bass_events = generate_accompaniment(
                chord_symbols=prog_chords,
                style_name=prog_style,
                tempo_bpm=int(round(effective_bpm)),
                bars_per_chord=prog_bars_per_chord,
                outfile=None,
                tritone_mode="none",
            )

            # Truncate to 2-bar cycle
            bars_per_cycle = 2
            comp_events = truncate_events_to_cycle(comp_events, bars_per_cycle)
            bass_events = truncate_events_to_cycle(bass_events, bars_per_cycle)

            # Convert to step messages
            steps_per_cycle = grid * bars_per_cycle
            rts = RtRenderSpec(
                bpm=effective_bpm,
                grid=grid,
                bars_per_cycle=bars_per_cycle,
                quantize=rt_quantize,
            )

            events = []
            events.extend(gm_program_changes_at_start())
            events.extend(note_events_to_step_messages(comp_events, spec=rts, steps_per_cycle=steps_per_cycle))
            events.extend(note_events_to_step_messages(bass_events, spec=rts, steps_per_cycle=steps_per_cycle))

            # Build spec with bar CC settings and bars_limit
            total_bars = prog_bars_per_chord * len(prog_chords)
            spec = RtSpec(
                midi_out=midi_out,
                bpm=effective_bpm,
                grid=grid,
                clave=clave,
                click=click,
                bar_cc_enabled=bar_cc_enabled,
                bar_cc_channel=bar_cc_channel,
                bar_cc_countdown=bar_cc_countdown,
                bar_cc_index=bar_cc_index,
                bar_cc_section=bar_cc_section,
                bars_limit=total_bars,
            )

            # Play for N repeats
            repeats = item.repeats or 1
            print(f"  [{item_idx + 1}/{len(playlist.items)}] {prog_name}")
            print(f"      chords: {' '.join(prog_chords)}")
            print(f"      bpm: {effective_bpm}, style: {prog_style}, repeats: {repeats}, bars: {total_bars}")

            # Emit section marker CC at item start
            if section_port and bar_cc_enabled:
                import mido

                from .realtime_telemetry import _clamp_cc_value
                section_port.send(mido.Message(
                    "control_change",
                    channel=bar_cc_channel,
                    control=bar_cc_section,
                    value=_clamp_cc_value(item_idx),
                ))

            try:
                # Each repeat = 1 cycle (2 bars)
                rt_play_cycle(events=events, spec=spec, max_cycles=repeats)
            except KeyboardInterrupt:
                print("\n  [interrupted by user]")
                if section_port:
                    section_port.close()
                return

    finally:
        if section_port:
            section_port.close()

    # Handle dry-run --all-programs completion
    band_args = _parse_band_control_args()
    if getattr(band_args, "dry_run", False) and getattr(band_args, "all_programs", False):
        is_compact = getattr(band_args, "compact", False)
        if is_compact:
            # Print summary line and exit with proper code
            print(dry_run_stats.summary_line())
            exit_code = 1 if dry_run_stats.any_fail else 0
            status = "fail" if exit_code else "ok"
            print(f"[dry-run] exit: {status}\n")
            raise SystemExit(exit_code)
        else:
            print("[dry-run] all programs validated; exit: ok\n")
            raise SystemExit(0)

    print("\nPlaylist complete.")


if __name__ == "__main__":
    import sys
    
    # Handle --list-presets early (before requiring other args)
    if "--list-presets" in sys.argv:
        _print_presets_and_exit()
    
    # Otherwise, show help since this is a library module
    print("rt_playlist is a library module. Use via CLI:")
    print("  zt-band rt-play --playlist <file.ztplay> ...")
    print()
    print("For presets: zt-band rt-play --list-presets")
    print("Or: python -m zt_band.rt_playlist --list-presets")
