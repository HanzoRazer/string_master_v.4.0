"""
Tests for daw_export.py — DAW-ready MIDI export with GM patches.
"""
import tempfile
from pathlib import Path

import pytest

# daw_export requires mido
pytest.importorskip("mido")

import mido

from zt_band.daw_export import (
    DawExportResult,
    _has_program_change_at_start,
    _inject_gm_program_changes,
    _now_stamp,
    _write_import_guide,
    export_for_daw,
)


class TestNowStamp:
    def test_returns_string(self):
        stamp = _now_stamp()
        assert isinstance(stamp, str)

    def test_format_includes_date_and_time(self):
        stamp = _now_stamp()
        # Format: YYYY-MM-DD_HHMMSS
        assert len(stamp) == 17
        assert stamp[4] == "-"
        assert stamp[7] == "-"
        assert stamp[10] == "_"


class TestHasProgramChangeAtStart:
    def test_detects_program_change(self):
        track = mido.MidiTrack()
        track.append(mido.Message("program_change", channel=0, program=0, time=0))
        track.append(mido.Message("note_on", channel=0, note=60, velocity=80, time=0))

        assert _has_program_change_at_start(track, channel=0) is True

    def test_no_program_change(self):
        track = mido.MidiTrack()
        track.append(mido.Message("note_on", channel=0, note=60, velocity=80, time=0))

        assert _has_program_change_at_start(track, channel=0) is False

    def test_wrong_channel(self):
        track = mido.MidiTrack()
        track.append(mido.Message("program_change", channel=1, program=0, time=0))

        assert _has_program_change_at_start(track, channel=0) is False

    def test_program_change_not_at_time_zero(self):
        track = mido.MidiTrack()
        track.append(mido.Message("note_on", channel=0, note=60, velocity=80, time=0))
        track.append(mido.Message("program_change", channel=0, program=0, time=100))

        assert _has_program_change_at_start(track, channel=0) is False


class TestInjectGmProgramChanges:
    def test_injects_program_changes(self):
        mid = mido.MidiFile(type=1)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.Message("note_on", channel=0, note=60, velocity=80, time=0))
        track.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=480))

        _inject_gm_program_changes(mid)

        # Should now have program_change and track_name
        msg_types = [m.type for m in track]
        assert "program_change" in msg_types
        assert "track_name" in [m.type for m in track if hasattr(m, "type")]

    def test_does_not_double_inject(self):
        mid = mido.MidiFile(type=1)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.Message("program_change", channel=0, program=5, time=0))
        track.append(mido.Message("note_on", channel=0, note=60, velocity=80, time=0))

        _inject_gm_program_changes(mid)

        # Should not add another program_change
        pc_count = sum(1 for m in track if getattr(m, "type", None) == "program_change")
        assert pc_count == 1

    def test_skips_tracks_without_notes(self):
        mid = mido.MidiFile(type=1)
        # Tempo-only track
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))

        _inject_gm_program_changes(mid)

        # Should add track_name but no program_change (no notes)
        pc_count = sum(1 for m in track if getattr(m, "type", None) == "program_change")
        assert pc_count == 0


class TestWriteImportGuide:
    def test_creates_markdown_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            guide_path = Path(tmpdir) / "IMPORT_DAW.md"
            _write_import_guide(
                guide_path,
                title="Test Export",
                midi_filename="test.mid",
                notes=["Note 1", "Note 2"],
            )

            assert guide_path.exists()
            content = guide_path.read_text(encoding="utf-8")
            assert "# Test Export" in content
            assert "test.mid" in content
            assert "Note 1" in content
            assert "Note 2" in content
            assert "## Quick import" in content
            assert "## Smoke test" in content


class TestExportForDaw:
    @pytest.fixture
    def sample_midi(self, tmp_path):
        """Create a minimal valid MIDI file for testing."""
        mid = mido.MidiFile(type=1, ticks_per_beat=480)

        # Tempo track
        tempo_track = mido.MidiTrack()
        mid.tracks.append(tempo_track)
        tempo_track.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))

        # Note track
        note_track = mido.MidiTrack()
        mid.tracks.append(note_track)
        note_track.append(mido.Message("note_on", channel=0, note=60, velocity=80, time=0))
        note_track.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=480))

        midi_path = tmp_path / "input.mid"
        mid.save(str(midi_path))
        return midi_path

    def test_export_creates_directory(self, sample_midi, tmp_path):
        export_root = tmp_path / "exports"
        result = export_for_daw(
            source_midi_path=sample_midi,
            export_root=export_root,
            title="Test Export",
        )

        assert isinstance(result, DawExportResult)
        assert result.export_dir.exists()
        assert result.export_dir.parent == export_root

    def test_export_creates_midi_file(self, sample_midi, tmp_path):
        export_root = tmp_path / "exports"
        result = export_for_daw(
            source_midi_path=sample_midi,
            export_root=export_root,
        )

        assert result.midi_path.exists()
        assert result.midi_path.suffix == ".mid"

    def test_export_creates_guide_file(self, sample_midi, tmp_path):
        export_root = tmp_path / "exports"
        result = export_for_daw(
            source_midi_path=sample_midi,
            export_root=export_root,
        )

        assert result.guide_path.exists()
        assert result.guide_path.name == "IMPORT_DAW.md"

    def test_export_without_gm_injection(self, sample_midi, tmp_path):
        export_root = tmp_path / "exports"
        result = export_for_daw(
            source_midi_path=sample_midi,
            export_root=export_root,
            inject_gm=False,
        )

        # Should still create files
        assert result.midi_path.exists()
        assert result.guide_path.exists()

    def test_export_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            export_for_daw(
                source_midi_path=tmp_path / "nonexistent.mid",
                export_root=tmp_path / "exports",
            )


class TestDawExportResult:
    def test_dataclass_fields(self):
        result = DawExportResult(
            export_dir=Path("/tmp/export"),
            midi_path=Path("/tmp/export/file.mid"),
            guide_path=Path("/tmp/export/IMPORT_DAW.md"),
        )
        assert result.export_dir == Path("/tmp/export")
        assert result.midi_path == Path("/tmp/export/file.mid")
        assert result.guide_path == Path("/tmp/export/IMPORT_DAW.md")
