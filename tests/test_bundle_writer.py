# tests/test_bundle_writer.py
"""
Tests for zt_band.bundle_writer

Verifies the canonical 4-file bundle is written correctly using the
testable primary API with explicit base_dir.

Design:
    - All tests use pytest's tmp_path fixture for hermetic isolation
    - Tests target the primary API: write_clip_bundle(base_dir=...)
    - Convenience wrapper tests use write_clip_bundle_default()
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import pytest

from zt_band.bundle_writer import (
    ArtifactRef,
    BundleResult,
    _atomic_write_bytes,
    _compute_sha256,
    _generate_clip_id,
    compute_default_bundle_dir,
    write_clip_bundle,
    write_clip_bundle_default,
)
from zt_band.midi_out import NoteEvent


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_events() -> Tuple[List[NoteEvent], List[NoteEvent]]:
    """Simple 4-bar comp + bass events for testing."""
    comp = [
        NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80, channel=0),
        NoteEvent(start_beats=2.0, duration_beats=1.0, midi_note=64, velocity=85, channel=0),
        NoteEvent(start_beats=4.0, duration_beats=1.0, midi_note=67, velocity=30, channel=0),  # ghost
        NoteEvent(start_beats=6.0, duration_beats=1.0, midi_note=72, velocity=110, channel=0),  # accent
    ]
    bass = [
        NoteEvent(start_beats=0.0, duration_beats=2.0, midi_note=36, velocity=90, channel=1),
        NoteEvent(start_beats=4.0, duration_beats=2.0, midi_note=43, velocity=90, channel=1),
    ]
    return comp, bass


@pytest.fixture
def fixed_timestamp() -> datetime:
    """Fixed UTC timestamp for deterministic testing."""
    return datetime(2026, 2, 2, 12, 0, 0, tzinfo=timezone.utc)


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestUtilityFunctions:
    """Tests for module-level utility functions."""

    def test_compute_sha256_format(self) -> None:
        """SHA256 should be in 'sha256:<64-hex-lowercase>' format."""
        data = b"hello world"
        sha = _compute_sha256(data)

        assert sha.startswith("sha256:")
        assert len(sha) == 7 + 64  # "sha256:" + 64 hex chars
        # Verify it's lowercase hex
        hex_part = sha[7:]
        assert hex_part == hex_part.lower()
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_compute_sha256_deterministic(self) -> None:
        """Same input should produce same hash."""
        data = b"deterministic test"
        sha1 = _compute_sha256(data)
        sha2 = _compute_sha256(data)

        assert sha1 == sha2

    def test_generate_clip_id_format(self) -> None:
        """Clip ID should be 'clip_<12-hex-chars>'."""
        clip_id = _generate_clip_id()

        assert clip_id.startswith("clip_")
        assert len(clip_id) == 5 + 12  # "clip_" + 12 hex chars

    def test_generate_clip_id_unique(self) -> None:
        """Each call should generate unique ID."""
        ids = [_generate_clip_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_compute_default_bundle_dir(self, fixed_timestamp: datetime) -> None:
        """Default bundle dir follows {root}/YYYY-MM-DD/{clip_id}/."""
        root = Path("/test/bundles")
        bundle_dir = compute_default_bundle_dir(
            created_at_utc=fixed_timestamp,
            clip_id="test_clip_001",
            root=root,
        )

        assert bundle_dir == root / "2026-02-02" / "test_clip_001"

    def test_compute_default_bundle_dir_uses_home(self, fixed_timestamp: datetime) -> None:
        """When root=None, uses ~/.sg-bundles."""
        bundle_dir = compute_default_bundle_dir(
            created_at_utc=fixed_timestamp,
            clip_id="test_clip_002",
        )

        assert bundle_dir == Path.home() / ".sg-bundles" / "2026-02-02" / "test_clip_002"


class TestAtomicWrite:
    """Tests for atomic write utility."""

    def test_atomic_write_creates_file(self, tmp_path: Path) -> None:
        """Atomic write should create file with correct content."""
        target = tmp_path / "test_file.txt"
        data = b"atomic write test"

        _atomic_write_bytes(target, data)

        assert target.exists()
        assert target.read_bytes() == data

    def test_atomic_write_overwrites(self, tmp_path: Path) -> None:
        """Atomic write should overwrite existing file."""
        target = tmp_path / "overwrite.txt"
        target.write_bytes(b"original content")

        _atomic_write_bytes(target, b"new content")

        assert target.read_bytes() == b"new content"

    def test_atomic_write_no_partial(self, tmp_path: Path) -> None:
        """Temp files should not remain after write."""
        target = tmp_path / "clean.txt"
        _atomic_write_bytes(target, b"clean test")

        # Only the target file should exist, no .tmp files
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].name == "clean.txt"


# ============================================================================
# Primary API Tests: write_clip_bundle()
# ============================================================================


class TestWriteClipBundle:
    """Tests for the primary testable API: write_clip_bundle()."""

    def test_creates_midi_file(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """clip.mid should always be created."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="midi_test",
            created_at_utc=fixed_timestamp,
        )

        midi_path = result.bundle_dir / "clip.mid"
        assert midi_path.exists()
        assert "clip.mid" in result.artifacts
        assert result.artifacts["clip.mid"].size_bytes > 0

    def test_creates_runlog(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """clip.runlog.json should always be created."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="runlog_test",
            created_at_utc=fixed_timestamp,
        )

        runlog_path = result.bundle_dir / "clip.runlog.json"
        assert runlog_path.exists()
        assert "clip.runlog.json" in result.artifacts

    def test_creates_tags_json(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """clip.tags.json should always be created."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="tags_test",
            created_at_utc=fixed_timestamp,
        )

        tags_path = result.bundle_dir / "clip.tags.json"
        assert tags_path.exists()
        assert "clip.tags.json" in result.artifacts

    def test_no_coach_by_default(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """clip.coach.json should NOT be created when require_coach_file=False."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="no_coach_test",
            created_at_utc=fixed_timestamp,
            require_coach_file=False,
        )

        coach_path = result.bundle_dir / "clip.coach.json"
        assert not coach_path.exists()
        assert "clip.coach.json" not in result.artifacts

    def test_coach_created_when_required(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """clip.coach.json should be created when require_coach_file=True."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="coach_required_test",
            created_at_utc=fixed_timestamp,
            require_coach_file=True,
        )

        coach_path = result.bundle_dir / "clip.coach.json"
        assert coach_path.exists()
        assert "clip.coach.json" in result.artifacts

    def test_coach_created_when_assignment_provided(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """clip.coach.json should be created when assignment is provided."""
        comp, bass = sample_events

        assignment = {
            "schema_id": "practice_assignment",
            "schema_version": "v1",
            "focus_area": "timing",
        }

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="coach_assignment_test",
            created_at_utc=fixed_timestamp,
            assignment=assignment,
        )

        coach_path = result.bundle_dir / "clip.coach.json"
        assert coach_path.exists()

        with open(coach_path) as f:
            coach_data = json.load(f)
        assert coach_data["focus_area"] == "timing"

    def test_bundle_dir_structure(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """Bundle dir should be: base_dir/YYYY-MM-DD/clip_id/."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="structure_test",
            created_at_utc=fixed_timestamp,
        )

        # Should be: tmp_path/2026-02-02/structure_test/
        expected = tmp_path / "2026-02-02" / "structure_test"
        assert result.bundle_dir == expected
        assert result.bundle_dir.is_dir()

    def test_sha256_format_in_artifacts(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """All SHA256 hashes should be in 'sha256:<64-hex>' format."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="sha256_test",
            created_at_utc=fixed_timestamp,
        )

        for name, artifact in result.artifacts.items():
            sha = artifact.sha256
            assert sha.startswith("sha256:"), f"{name} sha256 missing prefix"
            assert len(sha) == 7 + 64, f"{name} sha256 wrong length"

    def test_artifact_ref_dataclass(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """Artifacts should be ArtifactRef dataclass instances."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="artifact_ref_test",
            created_at_utc=fixed_timestamp,
        )

        for name, artifact in result.artifacts.items():
            assert isinstance(artifact, ArtifactRef)
            assert artifact.filename == name
            assert artifact.path.exists()
            assert artifact.size_bytes > 0

    def test_result_contains_created_at_utc(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """BundleResult should include created_at_utc field."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="created_at_test",
            created_at_utc=fixed_timestamp,
        )

        assert result.created_at_utc == fixed_timestamp

    def test_runlog_schema_fields(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """Runlog JSON should have required schema fields."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="runlog_schema_test",
            created_at_utc=fixed_timestamp,
        )

        runlog_path = result.bundle_dir / "clip.runlog.json"
        with open(runlog_path) as f:
            runlog = json.load(f)

        assert runlog["schema_id"] == "clip_runlog"
        assert runlog["schema_version"] == "v1"
        assert runlog["clip_id"] == "runlog_schema_test"
        assert "generator" in runlog
        assert "inputs" in runlog
        assert "outputs" in runlog
        assert "validation" in runlog
        assert "attempts" in runlog

    def test_validation_summary(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """Runlog validation should include correct note counts."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="validation_test",
            created_at_utc=fixed_timestamp,
        )

        runlog_path = result.bundle_dir / "clip.runlog.json"
        with open(runlog_path) as f:
            runlog = json.load(f)

        validation = runlog["validation"]
        assert validation["contract_passed"] is True
        assert validation["note_count"] == 6  # 4 comp + 2 bass
        assert validation["comp_event_count"] == 4
        assert validation["bass_event_count"] == 2

    def test_inputs_captured_in_runlog(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """Inputs should be captured in runlog for provenance."""
        comp, bass = sample_events

        inputs = {
            "chord_symbols": ["Dm7", "G7", "Cmaj7"],
            "style_name": "swing_basic",
            "tritone_seed": 42,
        }

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="inputs_test",
            created_at_utc=fixed_timestamp,
            inputs=inputs,
        )

        runlog_path = result.bundle_dir / "clip.runlog.json"
        with open(runlog_path) as f:
            runlog = json.load(f)

        assert runlog["inputs"]["chord_symbols"] == ["Dm7", "G7", "Cmaj7"]
        assert runlog["inputs"]["style_name"] == "swing_basic"
        assert runlog["inputs"]["tritone_seed"] == 42

    def test_tags_json_content(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """Tags JSON should contain expected schema fields."""
        comp, bass = sample_events
        comp_tags = [
            ["articulation.chord.strum"],
            ["articulation.chord.strum"],
            ["articulation.dynamics.ghost"],
            ["articulation.dynamics.accent"],
        ]

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="tags_content_test",
            created_at_utc=fixed_timestamp,
            comp_tags=comp_tags,
            meter="4/4",
            beats_per_bar=4.0,
        )

        tags_path = result.bundle_dir / "clip.tags.json"
        with open(tags_path) as f:
            tags = json.load(f)

        assert tags["schema_id"] == "technique_sidecar"
        assert tags["schema_version"] == "v1"
        assert tags["meter"] == "4/4"
        assert tags["beats_per_bar"] == 4.0
        assert len(tags["comp_tags"]) == 4
        assert tags["comp_tags"][2] == ["articulation.dynamics.ghost"]

    def test_outputs_sha256_in_runlog(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """Runlog outputs should include SHA256 for each artifact."""
        comp, bass = sample_events

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="outputs_sha_test",
            created_at_utc=fixed_timestamp,
        )

        runlog_path = result.bundle_dir / "clip.runlog.json"
        with open(runlog_path) as f:
            runlog = json.load(f)

        outputs = runlog["outputs"]
        assert outputs["clip_mid_sha256"].startswith("sha256:")
        assert outputs["clip_tags_sha256"].startswith("sha256:")

    def test_empty_events(
        self,
        tmp_path: Path,
        fixed_timestamp: datetime,
    ) -> None:
        """Bundle should work with empty event lists."""
        result = write_clip_bundle(
            comp_events=[],
            bass_events=[],
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="empty_events_test",
            created_at_utc=fixed_timestamp,
        )

        assert result.bundle_dir.exists()
        assert (result.bundle_dir / "clip.mid").exists()

        runlog_path = result.bundle_dir / "clip.runlog.json"
        with open(runlog_path) as f:
            runlog = json.load(f)

        assert runlog["validation"]["note_count"] == 0


# ============================================================================
# Convenience Wrapper Tests: write_clip_bundle_default()
# ============================================================================


class TestWriteClipBundleDefault:
    """Tests for the convenience wrapper: write_clip_bundle_default()."""

    def test_auto_generates_clip_id(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
    ) -> None:
        """When clip_id is None, should auto-generate unique ID."""
        comp, bass = sample_events

        result = write_clip_bundle_default(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            bundles_root=tmp_path,
        )

        assert result.clip_id.startswith("clip_")
        assert len(result.clip_id) == 5 + 12  # "clip_" + 12 hex chars

    def test_uses_provided_clip_id(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
    ) -> None:
        """When clip_id is provided, should use it."""
        comp, bass = sample_events

        result = write_clip_bundle_default(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            clip_id="custom_clip_id",
            bundles_root=tmp_path,
        )

        assert result.clip_id == "custom_clip_id"

    def test_uses_custom_bundles_root(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
    ) -> None:
        """When bundles_root is provided, should use it."""
        comp, bass = sample_events
        custom_root = tmp_path / "custom_bundles"

        result = write_clip_bundle_default(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            bundles_root=custom_root,
        )

        # Bundle should be under custom root
        assert str(result.bundle_dir).startswith(str(custom_root))

    def test_creates_complete_bundle(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
    ) -> None:
        """Should create all required files."""
        comp, bass = sample_events

        result = write_clip_bundle_default(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            bundles_root=tmp_path,
        )

        assert (result.bundle_dir / "clip.mid").exists()
        assert (result.bundle_dir / "clip.tags.json").exists()
        assert (result.bundle_dir / "clip.runlog.json").exists()

    def test_result_has_created_at_utc(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
    ) -> None:
        """Result should have auto-generated created_at_utc."""
        comp, bass = sample_events

        result = write_clip_bundle_default(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            bundles_root=tmp_path,
        )

        assert result.created_at_utc is not None
        assert isinstance(result.created_at_utc, datetime)
        # Should be recent (within last minute)
        now = datetime.now(timezone.utc)
        delta = (now - result.created_at_utc).total_seconds()
        assert 0 <= delta < 60


# ============================================================================
# Collision and Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and collision handling."""

    def test_existing_bundle_dir_ok(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """Writing to existing bundle dir should succeed (overwrite)."""
        comp, bass = sample_events

        # First write
        result1 = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="collision_test",
            created_at_utc=fixed_timestamp,
        )

        # Second write to same location
        result2 = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=140,  # Different tempo
            base_dir=tmp_path,
            clip_id="collision_test",
            created_at_utc=fixed_timestamp,
        )

        # Both should succeed
        assert result1.bundle_dir == result2.bundle_dir

    def test_different_dates_different_dirs(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
    ) -> None:
        """Different dates should produce different directories."""
        comp, bass = sample_events

        ts1 = datetime(2026, 1, 15, tzinfo=timezone.utc)
        ts2 = datetime(2026, 1, 16, tzinfo=timezone.utc)

        result1 = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="same_clip",
            created_at_utc=ts1,
        )

        result2 = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="same_clip",
            created_at_utc=ts2,
        )

        assert result1.bundle_dir != result2.bundle_dir
        assert "2026-01-15" in str(result1.bundle_dir)
        assert "2026-01-16" in str(result2.bundle_dir)

    def test_special_chars_in_style_params(
        self,
        tmp_path: Path,
        sample_events: Tuple[List[NoteEvent], List[NoteEvent]],
        fixed_timestamp: datetime,
    ) -> None:
        """Style params with special characters should serialize correctly."""
        comp, bass = sample_events

        style_params = {
            "name": "swing 'classic'",
            "description": 'Has "quotes" and unicode: \u2605',
            "nested": {"key": "value"},
        }

        result = write_clip_bundle(
            comp_events=comp,
            bass_events=bass,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="special_chars_test",
            created_at_utc=fixed_timestamp,
            style_params=style_params,
        )

        tags_path = result.bundle_dir / "clip.tags.json"
        with open(tags_path, encoding="utf-8") as f:
            tags = json.load(f)

        assert tags["style_params"]["name"] == "swing 'classic'"
        assert "\u2605" in tags["style_params"]["description"]
