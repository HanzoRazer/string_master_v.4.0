from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from mido import MidiFile, MidiTrack, Message, MetaMessage


@dataclass(frozen=True)
class DawExportResult:
    export_dir: Path
    midi_path: Path
    guide_path: Path


def _now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def _has_program_change_at_start(track: MidiTrack, channel: int) -> bool:
    """
    True if the track already has a program_change for this channel at time=0
    near the start of the track (first few events).
    """
    # Look only at the first few events to avoid scanning huge tracks
    for m in list(track)[:12]:
        if isinstance(m, Message) and m.type == "program_change" and getattr(m, "channel", None) == channel:
            if m.time == 0:
                return True
    return False


def _inject_gm_program_changes(mid: MidiFile) -> None:
    """
    Minimal "sounds everywhere" behavior:
      - channel 0: Acoustic Grand Piano (program 0)
      - channel 1: Acoustic Bass (program 32)
      - channel 9: Standard Drum Kit (channel 9 uses percussion; program often ignored but harmless)
    If your generator already emits program changes, this can be skipped via flag.
    """
    # Find first musical tracks (skip meta-only if present)
    # We'll inject at time=0 at the start of each track.
    for ti, tr in enumerate(mid.tracks):
        # Add a track name if missing
        has_name = any(isinstance(m, MetaMessage) and m.type == "track_name" for m in tr)
        if not has_name:
            # Rough naming heuristic
            name = "Track"
            if ti == 0:
                name = "Meta"
            elif ti == 1:
                name = "Comp"
            elif ti == 2:
                name = "Bass"
            elif ti == 3:
                name = "Drums"
            tr.insert(0, MetaMessage("track_name", name=name, time=0))

        # Inject GM program changes for common channels (if track contains note messages)
        has_notes = any(getattr(m, "type", None) in ("note_on", "note_off") for m in tr)
        if not has_notes:
            continue

        # Determine dominant channel used in this track (best-effort)
        channels = [m.channel for m in tr if isinstance(m, Message) and hasattr(m, "channel")]
        ch = channels[0] if channels else 0

        # Program map
        if ch == 0:
            program = 0     # Acoustic Grand Piano
        elif ch == 1:
            program = 32    # Acoustic Bass (GM)
        elif ch == 9:
            program = 0     # Drum kit (often ignored)
        else:
            program = 0

        # Avoid double-injecting if generator already emitted program changes
        if _has_program_change_at_start(tr, ch):
            continue

        # Insert near the top (after an optional track_name at index 0)
        insert_at = 1 if tr and isinstance(tr[0], MetaMessage) and tr[0].type == "track_name" else 0
        tr.insert(insert_at, Message("program_change", channel=ch, program=program, time=0))


def _write_import_guide(
    guide_path: Path,
    *,
    title: str,
    midi_filename: str,
    notes: Sequence[str],
) -> None:
    guide_path.write_text(
        "\n".join([
            f"# {title}",
            "",
            "## Quick import",
            f"1. Drag `{midi_filename}` into your DAW timeline.",
            "2. Confirm the DAW tempo matches the MIDI tempo (should auto-import).",
            "3. Assign instruments:",
            "   - Comp track → Piano / EP / Guitar",
            "   - Bass track → Bass instrument",
            "   - (If present) Drums track → Drum rack / kit",
            "",
            "## Notes",
            *[f"- {n}" for n in notes],
            "",
            "## Smoke test (60 seconds)",
            "- Press play: no stuck notes, no silence, timing feels correct.",
            "- Export a quick MP3/WAV bounce as proof-of-sound.",
            "",
        ]),
        encoding="utf-8",
    )


def export_for_daw(
    *,
    source_midi_path: str | Path,
    export_root: str | Path = "exports/daw",
    title: str = "ZT-Band DAW Export",
    inject_gm: bool = True,
) -> DawExportResult:
    src = Path(source_midi_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"MIDI not found: {src}")

    export_dir = Path(export_root).expanduser().resolve() / _now_stamp()
    export_dir.mkdir(parents=True, exist_ok=True)

    mid = MidiFile(str(src))

    if inject_gm:
        _inject_gm_program_changes(mid)

    out_midi = export_dir / src.name
    mid.save(str(out_midi))

    guide = export_dir / "IMPORT_DAW.md"
    _write_import_guide(
        guide,
        title=title,
        midi_filename=out_midi.name,
        notes=[
            "This export is designed for fast DAW proof-of-sound, not final production polish.",
            "If instruments sound wrong, override the DAW instrument selection per track.",
        ],
    )

    return DawExportResult(export_dir=export_dir, midi_path=out_midi, guide_path=guide)
