"""
rt_playlist.py — Live playlist runner for rt-play --playlist

Orchestrates sequential playback of .ztplay items, switching
programs at bar boundaries without engine rewrite.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .realtime import RtSpec, rt_play_cycle
from .rt_bridge import (
    RtRenderSpec,
    note_events_to_step_messages,
    gm_program_changes_at_start,
    truncate_events_to_cycle,
)
from .engine import generate_accompaniment
from .patterns import STYLE_REGISTRY


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
                from .realtime_telemetry import _clamp_cc_value
                import mido
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
    
    print("\nPlaylist complete.")
