"""
Tests for sg_agentd /generate endpoint.

Phase 3 scope: single passing test validating contract flow.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from uuid import uuid4


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def minimal_request_payload():
    """Minimal valid GenerationRequest payload."""
    return {
        "schema_id": "generation_request",
        "schema_version": "v1",
        "request_id": str(uuid4()),
        "requested_at_utc": datetime.now(timezone.utc).isoformat(),
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
            "attempt_budget": 1,
            "require_determinism": True,
            "validate_contract": True,
        },
        "requester": "test_harness",
    }


# ============================================================================
# Contract Validation Tests
# ============================================================================

class TestGenerationRequestValidation:
    """Test GenerationRequest schema validation."""

    def test_minimal_request_validates(self, minimal_request_payload):
        """Minimal payload passes validation."""
        try:
            from sg_spec.schemas.generation import GenerationRequest
        except ImportError:
            pytest.skip("sg-spec not installed")

        request = GenerationRequest.model_validate(minimal_request_payload)
        assert request.schema_id == "generation_request"
        assert request.harmony.chord_symbols == ["Dm7", "G7", "Cmaj7"]
        assert request.style.tempo_bpm == 120

    def test_missing_chord_symbols_fails(self, minimal_request_payload):
        """Request without chord_symbols fails validation."""
        try:
            from sg_spec.schemas.generation import GenerationRequest
            from pydantic import ValidationError
        except ImportError:
            pytest.skip("sg-spec not installed")

        minimal_request_payload["harmony"]["chord_symbols"] = []

        with pytest.raises(ValidationError):
            GenerationRequest.model_validate(minimal_request_payload)

    def test_probabilistic_without_seed_allowed_when_determinism_false(
        self, minimal_request_payload
    ):
        """Probabilistic mode without seed is valid when require_determinism=False."""
        try:
            from sg_spec.schemas.generation import GenerationRequest
        except ImportError:
            pytest.skip("sg-spec not installed")

        minimal_request_payload["tritone"]["mode"] = "probabilistic"
        minimal_request_payload["tritone"]["seed"] = None
        minimal_request_payload["constraints"]["require_determinism"] = False

        # This should validate at schema level (determinism check is runtime)
        request = GenerationRequest.model_validate(minimal_request_payload)
        assert request.tritone.mode == "probabilistic"


# ============================================================================
# Server Endpoint Tests
# ============================================================================

class TestGenerateEndpoint:
    """Test /generate endpoint behavior."""

    def test_health_check(self):
        """Health endpoint returns ok."""
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
        except ImportError:
            pytest.skip("FastAPI or sg_agentd not available")

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_generate_minimal_request(self, minimal_request_payload, tmp_path, monkeypatch):
        """Minimal request produces valid GenerationResult."""
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from sg_spec.schemas.generation import GenerationResult
            from zt_band.bundle_writer import BundleResult, ArtifactRef
        except ImportError:
            pytest.skip("Required packages not available")

        # Mock bundle_writer to avoid filesystem side effects
        def mock_write_clip_bundle_default(**kwargs):
            bundle_dir = tmp_path / "test_bundle"
            return BundleResult(
                bundle_dir=bundle_dir,
                clip_id="test_clip",
                created_at_utc=datetime.now(timezone.utc),
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

        # We need to patch the lazy import
        import sg_agentd.server as server_module
        original_import = server_module._import_zt_band

        def patched_import():
            result = original_import()
            result["write_clip_bundle_default"] = mock_write_clip_bundle_default
            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["schema_id"] == "generation_result"
        assert data["run_log"]["engine_module"] == "zt_band.engine"

    def test_determinism_derives_seed_when_missing(self, minimal_request_payload, tmp_path, monkeypatch):
        """Probabilistic mode without seed derives seed from request_id (Phase 4)."""
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from zt_band.bundle_writer import BundleResult, ArtifactRef
        except ImportError:
            pytest.skip("Required packages not available")

        # Mock bundle_writer to avoid filesystem side effects
        def mock_write_clip_bundle_default(**kwargs):
            bundle_dir = tmp_path / "test_bundle"
            return BundleResult(
                bundle_dir=bundle_dir,
                clip_id="test_clip",
                created_at_utc=datetime.now(timezone.utc),
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

        minimal_request_payload["tritone"]["mode"] = "probabilistic"
        minimal_request_payload["tritone"]["seed"] = None
        minimal_request_payload["constraints"]["require_determinism"] = True

        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200
        data = response.json()
        # Phase 4: derives seed instead of failing
        assert data["status"] in ("ok", "partial")
        # Seed was derived and used
        assert data["run_log"]["seed_used"] is not None


# ============================================================================
# Result Validation Tests
# ============================================================================

class TestGenerationResultValidation:
    """Test GenerationResult schema."""

    def test_ok_result_validates(self):
        """Valid ok result passes validation."""
        try:
            from sg_spec.schemas.generation import (
                GenerationResult,
                MidiArtifact,
                ValidationReport,
                RunLog,
            )
        except ImportError:
            pytest.skip("sg-spec not installed")

        result = GenerationResult(
            request_id=uuid4(),
            generated_at_utc=datetime.now(timezone.utc),
            status="ok",
            midi=MidiArtifact(
                path="/tmp/clip.mid",
                sha256="sha256:" + "a" * 64,
                track_count=2,
                duration_beats=12.0,
            ),
            validation=ValidationReport(passed=True),
            run_log=RunLog(
                engine_module="zt_band.engine",
                engine_function="generate_accompaniment",
                duration_ms=100,
                attempts_used=1,
            ),
        )
        assert result.status == "ok"
        assert result.midi.track_count == 2

    def test_failed_result_validates(self):
        """Valid failed result passes validation."""
        try:
            from sg_spec.schemas.generation import (
                GenerationResult,
                ValidationReport,
                RunLog,
            )
        except ImportError:
            pytest.skip("sg-spec not installed")

        result = GenerationResult(
            request_id=uuid4(),
            generated_at_utc=datetime.now(timezone.utc),
            status="failed",
            validation=ValidationReport(passed=False, violations=["Test error"]),
            run_log=RunLog(
                engine_module="zt_band.engine",
                engine_function="generate_accompaniment",
                duration_ms=0,
                attempts_used=1,  # Minimum is 1 per schema
            ),
            error_code="TEST_ERROR",
            error_message="Test error message",
        )
        assert result.status == "failed"
        assert result.error_code == "TEST_ERROR"
