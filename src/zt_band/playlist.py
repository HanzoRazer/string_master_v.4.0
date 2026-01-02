from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-not-found]

from .config import load_program_config
from .engine import generate_accompaniment
from .midi_out import NoteEvent, write_midi_file


@dataclass
class PlaylistItem:
    """
    A single entry in a playlist.

    - config_path: path to a .ztprog file
    - repeat:      how many times to repeat this program in sequence (>= 1)
    """
    config_path: Path
    repeat: int = 1


@dataclass
class Playlist:
    """
    A playlist chains multiple zt-band programs into one long MIDI session.

    - name:    optional human-readable label
    - tempo:   optional global tempo; if None, inferred from first program
    - items:   ordered list of items
    - outfile: optional suggested output filename (can be overridden by CLI)
    """
    name: str | None
    tempo: int | None
    items: list[PlaylistItem]
    outfile: str | None


def _parse_playlist_programs(raw: Any, base_dir: Path) -> list[PlaylistItem]:
    if not isinstance(raw, list):
        raise TypeError("Playlist 'programs' must be a list.")

    items: list[PlaylistItem] = []

    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise TypeError(
                f"Playlist entry #{idx} must be a mapping/object, got {type(entry)!r}."
            )
        cfg_path_raw = entry.get("config")
        if not cfg_path_raw:
            raise KeyError(f"Playlist entry #{idx} is missing required field 'config'.")

        cfg_path = Path(cfg_path_raw)
        if not cfg_path.is_absolute():
            cfg_path = base_dir / cfg_path

        repeat_raw = entry.get("repeat", 1)
        try:
            repeat = int(repeat_raw)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(
                f"Playlist entry #{idx} 'repeat' must be an integer."
            ) from exc
        if repeat < 1:
            raise ValueError(
                f"Playlist entry #{idx} 'repeat' must be >= 1 (got {repeat})."
            )

        items.append(PlaylistItem(config_path=cfg_path, repeat=repeat))

    if not items:
        raise ValueError("Playlist 'programs' list is empty.")

    return items


def load_playlist(path: str | Path) -> Playlist:
    """
    Load a playlist file (JSON or YAML) into a Playlist object.

    Expected keys:
      - name:      optional string
      - tempo:     optional integer; if omitted, will be derived from first program
      - outfile:   optional string; suggested output filename
      - programs:  required list of entries, each:
          - config: path to a .ztprog file (relative to playlist file or absolute)
          - repeat: optional integer >= 1 (default: 1)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Playlist not found: {p}")

    text = p.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Playlist file is empty: {p}")

    first_char = text[0]
    try:
        if first_char in ("{", "["):
            parsed = json.loads(text)
        else:
            parsed = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(
            f"Failed to parse playlist {p}. Ensure it is valid JSON or YAML."
        ) from exc

    if not isinstance(parsed, dict):
        raise TypeError(
            f"Playlist root must be a mapping/object. Got: {type(parsed)!r}"
        )

    name = parsed.get("name")
    tempo_raw = parsed.get("tempo")
    tempo: int | None
    if tempo_raw is None:
        tempo = None
    else:
        try:
            tempo = int(tempo_raw)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Playlist 'tempo' must be an integer.") from exc

    outfile = parsed.get("outfile")
    items = _parse_playlist_programs(parsed.get("programs"), p.parent)

    return Playlist(name=name, tempo=tempo, items=items, outfile=outfile)


def render_playlist_to_midi(playlist: Playlist, outfile: str) -> None:
    """
    Render a playlist into a single combined MIDI file.

    Assumptions / rules:
      - All programs in the playlist must share the same tempo.
        If Playlist.tempo is set, each ProgramConfig.tempo must match it.
        If Playlist.tempo is None, the first program's tempo is used and
        subsequent programs must match.
      - Each ProgramConfig's 'outfile' is ignored; 'outfile' arg is used instead.
    """
    all_comp: list[NoteEvent] = []
    all_bass: list[NoteEvent] = []

    # Determine global tempo
    global_tempo: int | None = playlist.tempo
    total_beats: float = 0.0

    first = True

    for item in playlist.items:
        if not item.config_path.exists():
            raise FileNotFoundError(
                f"Program config in playlist not found: {item.config_path}"
            )

        cfg = load_program_config(item.config_path)

        if first:
            if global_tempo is None:
                global_tempo = cfg.tempo
            first = False

        # Enforce tempo consistency
        if cfg.tempo != global_tempo:
            raise ValueError(
                f"Tempo mismatch in playlist: program {item.config_path} uses "
                f"tempo {cfg.tempo}, but global tempo is {global_tempo}."
            )

        for _ in range(item.repeat):
            # Generate accompaniment for this config, but don't write a file.
            comp_events, bass_events = generate_accompaniment(
                chord_symbols=cfg.chords,
                style_name=cfg.style,
                tempo_bpm=cfg.tempo,
                bars_per_chord=cfg.bars_per_chord,
                outfile=None,
                tritone_mode=cfg.tritone_mode,
                tritone_strength=cfg.tritone_strength,
                tritone_seed=cfg.tritone_seed,
            )

            # Compute length in beats for this segment
            segment_max: float = 0.0
            for ev in comp_events + bass_events:
                end = ev.start_beats + ev.duration_beats
                if end > segment_max:
                    segment_max = end

            # Offset events by total_beats so they chain in time
            for ev in comp_events:
                all_comp.append(
                    NoteEvent(
                        start_beats=ev.start_beats + total_beats,
                        duration_beats=ev.duration_beats,
                        midi_note=ev.midi_note,
                        velocity=ev.velocity,
                        channel=ev.channel,
                    )
                )
            for ev in bass_events:
                all_bass.append(
                    NoteEvent(
                        start_beats=ev.start_beats + total_beats,
                        duration_beats=ev.duration_beats,
                        midi_note=ev.midi_note,
                        velocity=ev.velocity,
                        channel=ev.channel,
                    )
                )

            total_beats += segment_max

    if global_tempo is None:
        # This should not happen, but guard anyway
        global_tempo = 120

    write_midi_file(all_comp, all_bass, tempo_bpm=global_tempo, outfile=outfile)
