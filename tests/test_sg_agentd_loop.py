"""
Tests for sg_agentd attempt loop (Phase 4).

Tests:
1. Seed derivation determinism
2. Range validator pass/fail
3. Loop exhausts budget on repeated failures
4. Loop short-circuits on first success
5. Partial status when budget exhausted but candidate exists
6. Failed status when all attempts crash
"""
from __future__ import annotations

import pytest
from uuid import uuid4
from dataclasses import dataclass
from typing import Any


# ============================================================================
# Seed Derivation Tests
# ============================================================================

class TestSeedDerivation:
    """Test deterministic seed derivation."""

    def test_same_request_id_produces_same_base_seed(self):
        """Same request_id always produces same base seed."""
        try:
            from sg_agentd.seed import derive_base_seed
        except ImportError:
            pytest.skip("sg_agentd not available")

        request_id = uuid4()
        seed1 = derive_base_seed(request_id)
        seed2 = derive_base_seed(request_id)
        assert seed1 == seed2

    def test_different_request_ids_produce_different_seeds(self):
        """Different request_ids produce different base seeds."""
        try:
            from sg_agentd.seed import derive_base_seed
        except ImportError:
            pytest.skip("sg_agentd not available")

        id1 = uuid4()
        id2 = uuid4()
        seed1 = derive_base_seed(id1)
        seed2 = derive_base_seed(id2)
        assert seed1 != seed2

    def test_attempt_seeds_vary_by_index(self):
        """Each attempt index produces a different seed."""
        try:
            from sg_agentd.seed import derive_base_seed, derive_attempt_seed
        except ImportError:
            pytest.skip("sg_agentd not available")

        request_id = uuid4()
        base_seed = derive_base_seed(request_id)

        seeds = [derive_attempt_seed(base_seed, i) for i in range(5)]
        # All should be unique
        assert len(set(seeds)) == 5

    def test_choose_seed_honors_explicit_seed(self):
        """When explicit seed is provided, it's used directly."""
        try:
            from sg_agentd.seed import choose_seed_sequence
        except ImportError:
            pytest.skip("sg_agentd not available")

        request_id = uuid4()
        explicit = 12345
        chosen = choose_seed_sequence(request_id, 0, explicit_seed=explicit)
        assert chosen == explicit


# ============================================================================
# Range Validator Tests
# ============================================================================

@dataclass
class MockNoteEvent:
    """Mock NoteEvent with .note attribute."""
    note: int
    start_beats: float = 0.0
    duration_beats: float = 1.0


class TestRangeValidator:
    """Test pitch range validation."""

    def test_range_within_limit_passes(self):
        """Events within range limit pass validation."""
        try:
            from sg_agentd.validators import validate_pitch_range
        except ImportError:
            pytest.skip("sg_agentd not available")

        # C4 to C5 = 12 semitones
        comp = [MockNoteEvent(note=60), MockNoteEvent(note=72)]
        bass = [MockNoteEvent(note=48)]

        result = validate_pitch_range(comp, bass, limit=24)
        assert result.passed
        assert result.actual_span == 24  # 72 - 48

    def test_range_exceeds_limit_fails(self):
        """Events exceeding range limit fail validation."""
        try:
            from sg_agentd.validators import validate_pitch_range
        except ImportError:
            pytest.skip("sg_agentd not available")

        # C3 to C6 = 36 semitones (3 octaves)
        comp = [MockNoteEvent(note=60), MockNoteEvent(note=84)]
        bass = [MockNoteEvent(note=48)]

        result = validate_pitch_range(comp, bass, limit=24)
        assert not result.passed
        assert result.actual_span == 36
        assert len(result.violations) == 1

    def test_empty_events_passes_with_warning(self):
        """Empty event lists pass with a warning."""
        try:
            from sg_agentd.validators import validate_pitch_range
        except ImportError:
            pytest.skip("sg_agentd not available")

        result = validate_pitch_range([], [], limit=24)
        assert result.passed
        assert result.actual_span is None
        assert len(result.warnings) == 1


# ============================================================================
# Loop Orchestration Tests
# ============================================================================

class TestLoopOrchestration:
    """Test attempt loop behavior."""

    def test_loop_returns_ok_on_first_pass(self):
        """Loop returns immediately when first attempt passes."""
        try:
            from sg_agentd.loop import run_attempt_loop
        except ImportError:
            pytest.skip("sg_agentd not available")

        request_id = uuid4()
        call_count = 0

        def generate_fn(seed):
            nonlocal call_count
            call_count += 1
            # Return events within range
            return (
                [MockNoteEvent(note=60), MockNoteEvent(note=67)],
                [MockNoteEvent(note=48)],
            )

        outcome = run_attempt_loop(
            request_id=request_id,
            explicit_seed=None,
            attempt_budget=5,
            generate_fn=generate_fn,
            pitch_range_limit=24,
        )

        assert outcome.status == "ok"
        assert len(outcome.attempts) == 1
        assert call_count == 1
        assert outcome.selected_attempt == 0

    def test_loop_exhausts_budget_on_failures(self):
        """Loop tries all attempts when validation fails."""
        try:
            from sg_agentd.loop import run_attempt_loop
        except ImportError:
            pytest.skip("sg_agentd not available")

        request_id = uuid4()
        call_count = 0

        def generate_fn(seed):
            nonlocal call_count
            call_count += 1
            # Return events with huge range (always fails)
            return (
                [MockNoteEvent(note=24), MockNoteEvent(note=96)],
                [MockNoteEvent(note=36)],
            )

        outcome = run_attempt_loop(
            request_id=request_id,
            explicit_seed=None,
            attempt_budget=3,
            generate_fn=generate_fn,
            pitch_range_limit=24,
        )

        assert outcome.status == "partial"  # Has candidates but none passed
        assert len(outcome.attempts) == 3
        assert call_count == 3
        assert outcome.selected_attempt == 0  # First candidate selected

    def test_loop_returns_failed_when_all_crash(self):
        """Loop returns failed when all attempts crash."""
        try:
            from sg_agentd.loop import run_attempt_loop
        except ImportError:
            pytest.skip("sg_agentd not available")

        request_id = uuid4()

        def generate_fn(seed):
            raise RuntimeError("Generation crashed!")

        outcome = run_attempt_loop(
            request_id=request_id,
            explicit_seed=None,
            attempt_budget=3,
            generate_fn=generate_fn,
            pitch_range_limit=24,
        )

        assert outcome.status == "failed"
        assert len(outcome.attempts) == 3
        assert outcome.selected_attempt is None

    def test_loop_uses_derived_seeds(self):
        """Loop derives different seed for each attempt."""
        try:
            from sg_agentd.loop import run_attempt_loop
        except ImportError:
            pytest.skip("sg_agentd not available")

        request_id = uuid4()
        seeds_seen = []

        def generate_fn(seed):
            seeds_seen.append(seed)
            # Fail validation to force retries
            return (
                [MockNoteEvent(note=24), MockNoteEvent(note=96)],
                [],
            )

        outcome = run_attempt_loop(
            request_id=request_id,
            explicit_seed=None,
            attempt_budget=3,
            generate_fn=generate_fn,
            pitch_range_limit=24,
        )

        # All 3 seeds should be different
        assert len(seeds_seen) == 3
        assert len(set(seeds_seen)) == 3

    def test_loop_short_circuits_on_success(self):
        """Loop stops as soon as validation passes."""
        try:
            from sg_agentd.loop import run_attempt_loop
        except ImportError:
            pytest.skip("sg_agentd not available")

        request_id = uuid4()
        call_count = 0

        def generate_fn(seed):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                # Second attempt passes
                return (
                    [MockNoteEvent(note=60)],
                    [MockNoteEvent(note=48)],
                )
            else:
                # Other attempts fail
                return (
                    [MockNoteEvent(note=24), MockNoteEvent(note=96)],
                    [],
                )

        outcome = run_attempt_loop(
            request_id=request_id,
            explicit_seed=None,
            attempt_budget=5,
            generate_fn=generate_fn,
            pitch_range_limit=24,
        )

        assert outcome.status == "ok"
        assert len(outcome.attempts) == 2
        assert call_count == 2
        assert outcome.selected_attempt == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestLoopIntegration:
    """Test loop integration with server endpoint."""

    def test_endpoint_reports_attempts_used(self, tmp_path, monkeypatch):
        """Endpoint reports correct attempts_used in run_log."""
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from zt_band.bundle_writer import BundleResult, ArtifactRef
        except ImportError:
            pytest.skip("Required packages not available")

        # Mock bundle_writer
        def mock_write_clip_bundle_default(**kwargs):
            bundle_dir = tmp_path / "test_bundle"
            return BundleResult(
                bundle_dir=bundle_dir,
                clip_id="test_clip",
                created_at_utc=__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ),
                artifacts={
                    "clip.mid": ArtifactRef(
                        filename="clip.mid",
                        path=bundle_dir / "clip.mid",
                        sha256="sha256:" + "a" * 64,
                        size_bytes=1024,
                    ),
                    "clip.tags.json": ArtifactRef(
                        filename="clip.tags.json",
                        path=bundle_dir / "clip.tags.json",
                        sha256="sha256:" + "b" * 64,
                        size_bytes=256,
                    ),
                    "clip.runlog.json": ArtifactRef(
                        filename="clip.runlog.json",
                        path=bundle_dir / "clip.runlog.json",
                        sha256="sha256:" + "c" * 64,
                        size_bytes=512,
                    ),
                },
            )

        import sg_agentd.server as server_module
        original_import = server_module._import_zt_band

        def patched_import():
            result = original_import()
            result["write_clip_bundle_default"] = mock_write_clip_bundle_default
            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        payload = {
            "schema_id": "generation_request",
            "schema_version": "v1",
            "request_id": str(uuid4()),
            "requested_at_utc": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "harmony": {
                "chord_symbols": ["Dm7", "G7", "Cmaj7"],
                "bars_per_chord": 1,
            },
            "style": {
                "style_name": "swing_basic",
                "tempo_bpm": 120,
            },
            "tritone": {
                "mode": "none",
            },
            "constraints": {
                "attempt_budget": 3,
                "require_determinism": True,
                "validate_contract": True,
            },
            "requester": "test_harness",
        }

        client = TestClient(app)
        response = client.post("/generate", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should have used 1 attempt (first passes with normal generation)
        assert data["run_log"]["attempts_used"] >= 1
        assert data["run_log"]["seed_used"] is not None
