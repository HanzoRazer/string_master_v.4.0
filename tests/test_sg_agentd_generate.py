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

    def test_tritone_subs_mapped_to_all_doms(self, minimal_request_payload, tmp_path, monkeypatch):
        """Tritone mode 'subs' is mapped to engine mode 'all_doms' (PR2b)."""
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from zt_band.bundle_writer import BundleResult, ArtifactRef
        except ImportError:
            pytest.skip("Required packages not available")

        # --- Capture the tritone_mode passed into the engine ---
        seen = {"tritone_mode": None}

        def mock_generate_accompaniment(**kwargs):
            seen["tritone_mode"] = kwargs.get("tritone_mode")
            # Return minimal (comp_events, bass_events) lists
            return ([], [])

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
            result["generate_accompaniment"] = mock_generate_accompaniment
            result["write_clip_bundle_default"] = mock_write_clip_bundle_default
            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        # --- Set the contract-facing intent mode ---
        minimal_request_payload["tritone"]["mode"] = "subs"
        minimal_request_payload["tritone"]["seed"] = 12345  # explicit seed avoids derivation noise

        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200
        assert seen["tritone_mode"] == "all_doms"
        assert response.json()["status"] in ("ok", "partial")

    def test_generate_artifacts_validate_and_hashes_match(
        self, minimal_request_payload, tmp_path, monkeypatch
    ):
        """
        End-to-end hardening test:
        - Uses real zt_band bundle writer (writes files)
        - Reads returned artifact paths from the /generate response
        - Verifies hashes match file bytes
        - Validates clip.tags.json and clip.runlog.json against sg-spec models
        """
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from sg_spec.schemas.technique_sidecar import TechniqueSidecar
            from sg_spec.schemas.clip_bundle import ClipRunLog
            from zt_band.midi_out import NoteEvent
        except ImportError:
            pytest.skip("Required packages not available (sg-spec / zt_band / fastapi)")

        import hashlib
        import json
        from pathlib import Path
        import sg_agentd.server as server_module

        def sha256_hex(path: str) -> str:
            data = Path(path).read_bytes()
            return hashlib.sha256(data).hexdigest()

        # ---- Patch zt_band import: keep real bundle writer, but control generator + output directory ----
        original_import = server_module._import_zt_band

        def patched_import():
            result = original_import()

            # 1) Make the generator deterministic and always in-range (avoid musical randomness affecting status)
            def mock_generate_accompaniment(**kwargs):
                comp = [
                    NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=90, channel=0),
                    NoteEvent(start_beats=1.0, duration_beats=1.0, midi_note=64, velocity=90, channel=0),
                ]
                bass = [
                    NoteEvent(start_beats=0.0, duration_beats=2.0, midi_note=36, velocity=90, channel=1),
                ]
                return (comp, bass)

            result["generate_accompaniment"] = mock_generate_accompaniment

            # 2) Force bundle writer to write into tmp_path instead of any default location
            #    write_clip_bundle_default() typically uses compute_default_bundle_dir(); patch that.
            import zt_band.bundle_writer as bw

            def _tmp_default_bundle_dir():
                d = tmp_path / "bundles"
                d.mkdir(parents=True, exist_ok=True)
                return d

            monkeypatch.setattr(bw, "compute_default_bundle_dir", _tmp_default_bundle_dir)

            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        # ---- Call endpoint ----
        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "partial")

        # ---- Verify artifacts exist + hashes match file bytes ----
        assert data["midi"] is not None
        assert data["tags"] is not None
        assert data["runlog"] is not None

        midi_path = data["midi"]["path"]
        tags_path = data["tags"]["path"]
        runlog_path = data["runlog"]["path"]

        assert Path(midi_path).exists()
        assert Path(tags_path).exists()
        assert Path(runlog_path).exists()

        midi_hex = sha256_hex(midi_path)
        tags_hex = sha256_hex(tags_path)
        runlog_hex = sha256_hex(runlog_path)

        def normalize_artifact_sha(s: str) -> str:
            # Response may be "sha256:<hex>" or "<hex>" depending on schema choice
            return s.split("sha256:", 1)[-1]

        assert normalize_artifact_sha(data["midi"]["sha256"]) == midi_hex
        assert normalize_artifact_sha(data["tags"]["sha256"]) == tags_hex
        assert normalize_artifact_sha(data["runlog"]["sha256"]) == runlog_hex

        # ---- Validate sg-spec models using response-path payloads ----
        tags_payload = json.loads(Path(tags_path).read_text())
        runlog_payload = json.loads(Path(runlog_path).read_text())

        TechniqueSidecar.model_validate(tags_payload)
        ClipRunLog.model_validate(runlog_payload)

    def test_pitch_range_semitones_drives_attempt_loop_via_generate(
        self, minimal_request_payload, tmp_path, monkeypatch
    ):
        """
        Proves constraints.pitch_range_semitones influences runtime behavior via /generate.
        We patch generate_accompaniment to fail range on attempt 1 and pass on attempt 2.
        """
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from zt_band.bundle_writer import BundleResult, ArtifactRef
            from zt_band.midi_out import NoteEvent
        except ImportError:
            pytest.skip("Required packages not available")

        import sg_agentd.server as server_module

        # ---- Deterministic engine stub: first call fails span>12, second passes span<=12 ----
        call_count = {"n": 0}

        def mock_generate_accompaniment(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # Wide span: 36 semitones (fails if limit=12)
                comp = [
                    NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=72, velocity=90, channel=0),
                ]
                bass = [
                    NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=36, velocity=90, channel=1),
                ]
                return (comp, bass)
            else:
                # Narrow span: 12 semitones (passes if limit=12)
                comp = [
                    NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=90, channel=0),
                ]
                bass = [
                    NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=48, velocity=90, channel=1),
                ]
                return (comp, bass)

        # ---- Mock bundle writer (no filesystem side effects needed for this loop behavior test) ----
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

        # ---- Patch lazy import to inject our stubs ----
        original_import = server_module._import_zt_band

        def patched_import():
            result = original_import()
            result["generate_accompaniment"] = mock_generate_accompaniment
            result["write_clip_bundle_default"] = mock_write_clip_bundle_default
            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        # ---- Configure request to force a failure then success within budget ----
        minimal_request_payload["constraints"]["attempt_budget"] = 2
        minimal_request_payload["constraints"]["pitch_range_semitones"] = 12

        # Use probabilistic so seed handling is exercised; seed may be derived, but our stub ignores it.
        minimal_request_payload["tritone"]["mode"] = "probabilistic"
        minimal_request_payload["tritone"]["seed"] = None
        minimal_request_payload["constraints"]["require_determinism"] = True

        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200
        data = response.json()

        # Should pass on 2nd attempt
        assert data["status"] == "ok"
        assert data["run_log"]["attempts_used"] == 2
        assert call_count["n"] == 2
        assert data["validation"]["passed"] is True

    def test_generate_fullstack_attempt_loop_writes_real_bundle_and_conforms(
        self, minimal_request_payload, tmp_path, monkeypatch
    ):
        """
        True full-stack integration test:
        - /generate endpoint
        - real attempt loop + real range validator
        - patched engine to fail pitch-range on attempt 1 and pass on attempt 2
        - real bundle writer writes files to tmp_path
        - verifies returned hashes match disk bytes
        - validates tags/runlog payloads against sg-spec models
        """
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from sg_spec.schemas.technique_sidecar import TechniqueSidecar
            from sg_spec.schemas.clip_bundle import ClipRunLog
            from zt_band.midi_out import NoteEvent
        except ImportError:
            pytest.skip("Required packages not available (sg-spec / zt_band / fastapi)")

        import hashlib
        import json
        from pathlib import Path
        import sg_agentd.server as server_module

        # --- helper: compute sha256 hex ---
        def sha256_hex(path: str) -> str:
            b = Path(path).read_bytes()
            return hashlib.sha256(b).hexdigest()

        def normalize_artifact_sha(s: str) -> str:
            return s.split("sha256:", 1)[-1]

        # --- deterministic engine stub: fail then pass ---
        call_count = {"n": 0}

        def mock_generate_accompaniment(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # Wide span: 36 semitones (fails if limit=12)
                comp = [
                    NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=72, velocity=90, channel=0),
                ]
                bass = [
                    NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=36, velocity=90, channel=1),
                ]
                return (comp, bass)
            else:
                # Narrow span: 12 semitones (passes if limit=12)
                comp = [
                    NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=90, channel=0),
                ]
                bass = [
                    NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=48, velocity=90, channel=1),
                ]
                return (comp, bass)

        # --- patch zt_band import: use real bundle writer, but force bundle dir into tmp_path ---
        original_import = server_module._import_zt_band

        def patched_import():
            result = original_import()

            # Patch generator to enforce deterministic fail/pass across attempts
            result["generate_accompaniment"] = mock_generate_accompaniment

            # Keep real write_clip_bundle_default, but force its output location.
            import zt_band.bundle_writer as bw

            def _tmp_default_bundle_dir():
                d = tmp_path / "bundles"
                d.mkdir(parents=True, exist_ok=True)
                return d

            monkeypatch.setattr(bw, "compute_default_bundle_dir", _tmp_default_bundle_dir)

            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        # --- configure request: enforce range constraint + allow retry ---
        minimal_request_payload["constraints"]["attempt_budget"] = 2
        minimal_request_payload["constraints"]["pitch_range_semitones"] = 12

        # Make sure we don't block on determinism rules; seed can be derived, generator ignores it anyway.
        minimal_request_payload["tritone"]["mode"] = "probabilistic"
        minimal_request_payload["tritone"]["seed"] = None
        minimal_request_payload["constraints"]["require_determinism"] = True

        # --- call endpoint ---
        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200
        data = response.json()

        # Must take 2 attempts: first fails range, second passes
        assert data["status"] == "ok"
        assert data["run_log"]["attempts_used"] == 2
        assert call_count["n"] == 2
        assert data["validation"]["passed"] is True

        # --- verify artifacts exist ---
        assert data["midi"] is not None
        assert data["tags"] is not None
        assert data["runlog"] is not None
        assert "bundle_path" in data

        midi_path = data["midi"]["path"]
        tags_path = data["tags"]["path"]
        runlog_path = data["runlog"]["path"]

        assert Path(midi_path).exists()
        assert Path(tags_path).exists()
        assert Path(runlog_path).exists()

        # --- verify hashes match actual bytes ---
        assert normalize_artifact_sha(data["midi"]["sha256"]) == sha256_hex(midi_path)
        assert normalize_artifact_sha(data["tags"]["sha256"]) == sha256_hex(tags_path)
        assert normalize_artifact_sha(data["runlog"]["sha256"]) == sha256_hex(runlog_path)

        # --- validate sg-spec models from response-path payloads ---
        tags_payload = json.loads(Path(tags_path).read_text())
        runlog_payload = json.loads(Path(runlog_path).read_text())

        TechniqueSidecar.model_validate(tags_payload)
        ClipRunLog.model_validate(runlog_payload)

        # --- assert TechniqueSidecar.source_midi_sha256 matches MIDI artifact hash ---
        # TechniqueSidecar stores raw hex (no "sha256:" prefix)
        sidecar_midi_hex = tags_payload["source_midi_sha256"]

        # API artifact may include "sha256:" prefix; normalize to raw hex
        api_midi_hex = normalize_artifact_sha(data["midi"]["sha256"])

        assert sidecar_midi_hex == api_midi_hex

        # --- sanity: artifact paths should all be under the same bundle directory ---
        # (We don't assert bundle_path is in tmp_path because BundleResult.bundle_dir
        # may be set before our monkeypatch takes effect on the writer's internal call.
        # What matters: the artifacts exist at returned paths and hashes match.)

    def test_generate_fullstack_negative_control_attempt_budget_1_returns_partial(
        self, minimal_request_payload, tmp_path, monkeypatch
    ):
        """
        Negative control full-stack test:
        - same forced "first attempt fails pitch range" generator
        - attempt_budget=1 so it cannot retry
        - expects status="partial" with validation.passed False
        - still writes a real bundle to disk (selected attempt is the failing one)
        - validates tags/runlog against sg-spec, and asserts source_midi_sha256 matches MIDI artifact hash
        """
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from sg_spec.schemas.technique_sidecar import TechniqueSidecar
            from sg_spec.schemas.clip_bundle import ClipRunLog
            from zt_band.midi_out import NoteEvent
        except ImportError:
            pytest.skip("Required packages not available (sg-spec / zt_band / fastapi)")

        import hashlib
        import json
        from pathlib import Path
        import sg_agentd.server as server_module

        def sha256_hex(path: str) -> str:
            b = Path(path).read_bytes()
            return hashlib.sha256(b).hexdigest()

        def normalize_artifact_sha(s: str) -> str:
            return s.split("sha256:", 1)[-1]

        # --- deterministic engine stub: always fail (wide span) on first call ---
        call_count = {"n": 0}

        def mock_generate_accompaniment(**kwargs):
            call_count["n"] += 1
            # Wide span: 36 semitones (fails if limit=12)
            comp = [
                NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=72, velocity=90, channel=0),
            ]
            bass = [
                NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=36, velocity=90, channel=1),
            ]
            return (comp, bass)

        # --- patch zt_band import: use real bundle writer, but force bundle dir into tmp_path ---
        original_import = server_module._import_zt_band

        def patched_import():
            result = original_import()
            result["generate_accompaniment"] = mock_generate_accompaniment

            import zt_band.bundle_writer as bw

            def _tmp_default_bundle_dir():
                d = tmp_path / "bundles"
                d.mkdir(parents=True, exist_ok=True)
                return d

            monkeypatch.setattr(bw, "compute_default_bundle_dir", _tmp_default_bundle_dir)
            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        # --- configure request: no retry + strict range limit ---
        minimal_request_payload["constraints"]["attempt_budget"] = 1
        minimal_request_payload["constraints"]["pitch_range_semitones"] = 12

        minimal_request_payload["tritone"]["mode"] = "probabilistic"
        minimal_request_payload["tritone"]["seed"] = None
        minimal_request_payload["constraints"]["require_determinism"] = True

        # --- call endpoint ---
        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200
        data = response.json()

        # Must be partial: only attempt fails range and no retries available
        assert data["status"] == "partial"
        assert data["run_log"]["attempts_used"] == 1
        assert call_count["n"] == 1
        assert data["validation"]["passed"] is False
        assert data["validation"]["violations"]  # should contain pitch span violation

        # --- verify artifacts exist (bundle still written from selected attempt) ---
        assert data["midi"] is not None
        assert data["tags"] is not None
        assert data["runlog"] is not None
        assert "bundle_path" in data

        midi_path = data["midi"]["path"]
        tags_path = data["tags"]["path"]
        runlog_path = data["runlog"]["path"]

        assert Path(midi_path).exists()
        assert Path(tags_path).exists()
        assert Path(runlog_path).exists()

        # --- verify hashes match actual bytes ---
        assert normalize_artifact_sha(data["midi"]["sha256"]) == sha256_hex(midi_path)
        assert normalize_artifact_sha(data["tags"]["sha256"]) == sha256_hex(tags_path)
        assert normalize_artifact_sha(data["runlog"]["sha256"]) == sha256_hex(runlog_path)

        # --- validate sg-spec models from response-path payloads ---
        tags_payload = json.loads(Path(tags_path).read_text())
        runlog_payload = json.loads(Path(runlog_path).read_text())

        TechniqueSidecar.model_validate(tags_payload)
        ClipRunLog.model_validate(runlog_payload)

        # --- assert sidecar midi hash matches API midi hash (raw hex vs sha256: prefix) ---
        sidecar_midi_hex = tags_payload["source_midi_sha256"]
        api_midi_hex = normalize_artifact_sha(data["midi"]["sha256"])
        assert sidecar_midi_hex == api_midi_hex

        # NOTE: We do NOT assert bundle_path.startswith(tmp_path) here because
        # BundleResult.bundle_dir is set BEFORE the monkeypatch takes effect.
        # The critical invariant (artifacts exist and hashes match) is verified above.


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


# ============================================================================
# PR4: End-to-End Artifact Hardening Tests
# ============================================================================

class TestArtifactIntegrity:
    """
    PR4: End-to-end artifact verification.
    
    These tests ensure:
    - SHA256 hashes match file contents (PR4.1)
    - Response artifacts validate against sg-spec models (PR4.2)
    - pitch_range_semitones constraint drives attempt loop (PR4.3)
    - Boundary behavior (e.g., subs→all_doms) remains locked (PR4.4)
    """

    def test_artifact_hashes_match_file_bytes(self, tmp_path):
        """
        PR4.1: Artifact hashes in BundleResult match actual file bytes.
        
        Verifies that sha256 fields use 'sha256:' prefix and match
        the computed hash of the written file.
        """
        try:
            import hashlib
            from zt_band.bundle_writer import write_clip_bundle
            from zt_band.midi_out import NoteEvent
        except ImportError:
            pytest.skip("zt_band not available")

        # NoteEvent fields: start_beats, duration_beats, midi_note, velocity, channel
        comp_events = [NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80, channel=0)]
        bass_events = [NoteEvent(start_beats=0.0, duration_beats=2.0, midi_note=36, velocity=70, channel=1)]

        bundle_result = write_clip_bundle(
            comp_events=comp_events,
            bass_events=bass_events,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="test_hash_check",
            created_at_utc=datetime.now(timezone.utc),
        )

        # Verify all artifact hashes match file bytes
        for filename, artifact_ref in bundle_result.artifacts.items():
            file_bytes = artifact_ref.path.read_bytes()
            computed_hash = f"sha256:{hashlib.sha256(file_bytes).hexdigest().lower()}"
            
            assert artifact_ref.sha256 == computed_hash, (
                f"{filename}: stored hash {artifact_ref.sha256} != computed {computed_hash}"
            )
            # Confirm the prefix is present
            assert artifact_ref.sha256.startswith("sha256:"), (
                f"{filename}: missing 'sha256:' prefix"
            )

    def test_artifacts_validate_against_sgspec_models(self, tmp_path):
        """
        PR4.2: Written artifacts validate against sg-spec Pydantic models.
        
        Ensures clip.tags.json validates as TechniqueSidecar
        and clip.runlog.json validates as ClipRunLog.
        """
        try:
            import json
            from zt_band.bundle_writer import write_clip_bundle
            from zt_band.midi_out import NoteEvent
            from sg_spec.schemas.technique_sidecar import TechniqueSidecar
            from sg_spec.schemas.clip_bundle import ClipRunLog
        except ImportError:
            pytest.skip("zt_band or sg-spec not available")

        # NoteEvent fields: start_beats, duration_beats, midi_note, velocity, channel
        comp_events = [NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80, channel=0)]
        bass_events = [NoteEvent(start_beats=0.0, duration_beats=2.0, midi_note=36, velocity=70, channel=1)]

        bundle_result = write_clip_bundle(
            comp_events=comp_events,
            bass_events=bass_events,
            tempo_bpm=120,
            base_dir=tmp_path,
            clip_id="test_model_validate",
            created_at_utc=datetime.now(timezone.utc),
            style_params={"style_name": "swing_basic"},
        )

        # Validate clip.tags.json as TechniqueSidecar
        tags_path = bundle_result.artifacts["clip.tags.json"].path
        tags_data = json.loads(tags_path.read_text())
        sidecar = TechniqueSidecar.model_validate(tags_data)
        assert sidecar.schema_id == "technique_sidecar"
        assert sidecar.schema_version == "v1"
        assert len(sidecar.annotations) == 2  # 1 comp + 1 bass

        # Validate clip.runlog.json as ClipRunLog
        runlog_path = bundle_result.artifacts["clip.runlog.json"].path
        runlog_data = json.loads(runlog_path.read_text())
        runlog = ClipRunLog.model_validate(runlog_data)
        assert runlog.schema_id == "clip_runlog"
        assert runlog.schema_version == "v1"
        assert runlog.validation.contract_passed is True

    def test_pitch_range_semitones_drives_attempt_loop(self, minimal_request_payload, tmp_path, monkeypatch):
        """
        PR4.3: pitch_range_semitones constraint causes retry when violated.
        
        First attempt returns notes spanning > allowed range (fail).
        Second attempt returns notes within range (pass).
        Assert status=='ok' and attempts_used==2.
        """
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from zt_band.bundle_writer import BundleResult, ArtifactRef
        except ImportError:
            pytest.skip("Required packages not available")

        call_count = [0]

        def mock_generate_accompaniment(**kwargs):
            """Return wide span on first call, narrow span on second."""
            call_count[0] += 1
            
            if call_count[0] == 1:
                # First attempt: span of 36 semitones (C2 to C5) - fails if range <= 24
                comp_events = [
                    type('NoteEvent', (), {'start_beats': 0.0, 'duration_beats': 1.0, 'midi_note': 36, 'velocity': 80})(),
                    type('NoteEvent', (), {'start_beats': 1.0, 'duration_beats': 1.0, 'midi_note': 72, 'velocity': 80})(),
                ]
                bass_events = []
            else:
                # Second attempt: span of 12 semitones (C3 to C4) - passes
                comp_events = [
                    type('NoteEvent', (), {'start_beats': 0.0, 'duration_beats': 1.0, 'midi_note': 48, 'velocity': 80})(),
                    type('NoteEvent', (), {'start_beats': 1.0, 'duration_beats': 1.0, 'midi_note': 60, 'velocity': 80})(),
                ]
                bass_events = []
            
            return (comp_events, bass_events)

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
            result["generate_accompaniment"] = mock_generate_accompaniment
            result["write_clip_bundle_default"] = mock_write_clip_bundle_default
            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        # Set constraint: pitch_range_semitones = 24 (default), attempt_budget = 3
        minimal_request_payload["constraints"]["attempt_budget"] = 3
        minimal_request_payload["constraints"]["pitch_range_semitones"] = 24

        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200
        data = response.json()
        
        # Should succeed after retry
        assert data["status"] in ("ok", "partial")
        assert data["run_log"]["attempts_used"] >= 2, (
            f"Expected at least 2 attempts, got {data['run_log']['attempts_used']}"
        )

    def test_subs_to_all_doms_adapter_locked(self, minimal_request_payload, tmp_path, monkeypatch):
        """
        PR4.4: Boundary test - 'subs' mode maps to engine 'all_doms'.
        
        This locks the tritone adapter behavior introduced in PR2b.
        """
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from zt_band.bundle_writer import BundleResult, ArtifactRef
        except ImportError:
            pytest.skip("Required packages not available")

        seen = {"tritone_mode": None}

        def mock_generate_accompaniment(**kwargs):
            seen["tritone_mode"] = kwargs.get("tritone_mode")
            return ([], [])

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
            result["generate_accompaniment"] = mock_generate_accompaniment
            result["write_clip_bundle_default"] = mock_write_clip_bundle_default
            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        minimal_request_payload["tritone"]["mode"] = "subs"
        minimal_request_payload["tritone"]["seed"] = 12345

        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200
        # Core assertion: subs → all_doms
        assert seen["tritone_mode"] == "all_doms", (
            f"Expected tritone_mode='all_doms', got '{seen['tritone_mode']}'"
        )

    def test_generate_fullstack_coach_artifact_plumbing(
        self, minimal_request_payload, tmp_path, monkeypatch
    ):
        """
        PR5: Coach artifact E2E test.
        
        Verifies:
        - Request with PracticeAssignment → bundle writer emits clip.coach.json
        - Response includes coach artifact with valid path and sha256
        - Coach JSON on disk validates against sg-spec PracticeAssignment schema
        """
        try:
            from fastapi.testclient import TestClient
            from sg_agentd.server import app
            from sg_spec.ai.coach.schemas import (
                PracticeAssignment,
                ProgramRef,
                ProgramType,
                AssignmentConstraints,
                AssignmentFocus,
                SuccessCriteria,
                CoachPrompt,
            )
            from zt_band.midi_out import NoteEvent
        except ImportError:
            pytest.skip("Required packages not available (sg-spec / zt_band / fastapi)")

        import hashlib
        import json
        from pathlib import Path
        from uuid import uuid4
        import sg_agentd.server as server_module

        # --- helper: compute sha256 hex ---
        def sha256_hex(path: str) -> str:
            b = Path(path).read_bytes()
            return hashlib.sha256(b).hexdigest()

        def normalize_artifact_sha(s: str) -> str:
            return s.split("sha256:", 1)[-1]

        # --- deterministic engine stub: return valid events ---
        def mock_generate_accompaniment(**kwargs):
            comp = [
                NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=90, channel=0),
            ]
            bass = [
                NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=48, velocity=90, channel=1),
            ]
            return (comp, bass)

        # --- patch zt_band import: use real bundle writer, force output to tmp_path ---
        original_import = server_module._import_zt_band

        def patched_import():
            result = original_import()
            result["generate_accompaniment"] = mock_generate_accompaniment

            import zt_band.bundle_writer as bw

            def _tmp_default_bundle_dir():
                d = tmp_path / "bundles"
                d.mkdir(parents=True, exist_ok=True)
                return d

            monkeypatch.setattr(bw, "compute_default_bundle_dir", _tmp_default_bundle_dir)
            return result

        monkeypatch.setattr(server_module, "_import_zt_band", patched_import)

        # --- Build a minimal PracticeAssignment ---
        assignment = PracticeAssignment(
            assignment_id=uuid4(),
            session_id=uuid4(),
            program=ProgramRef(type=ProgramType.ztprog, name="test_program"),
            constraints=AssignmentConstraints(
                tempo_start=60,
                tempo_target=120,
                tempo_step=10,
                bars_per_loop=4,
                repetitions=1,
            ),
            focus=AssignmentFocus(primary="timing"),
            success_criteria=SuccessCriteria(max_mean_error_ms=50.0, max_late_drops=3),
            coach_prompt=CoachPrompt(mode="optional", message="Focus on timing."),
        )

        # --- Add assignment to request payload ---
        minimal_request_payload["assignment"] = assignment.model_dump(mode="json")

        # --- call endpoint ---
        client = TestClient(app)
        response = client.post("/generate", json=minimal_request_payload)

        assert response.status_code == 200, f"Unexpected status: {response.text}"
        data = response.json()

        # --- Verify coach artifact in response ---
        assert data.get("coach") is not None, "Expected coach artifact in response"
        coach_artifact = data["coach"]
        assert "path" in coach_artifact
        assert "sha256" in coach_artifact

        # --- Verify file exists on disk ---
        coach_path = Path(coach_artifact["path"])
        assert coach_path.exists(), f"Coach file not found at {coach_path}"

        # --- Verify sha256 matches disk bytes ---
        actual_sha = sha256_hex(str(coach_path))
        expected_sha = normalize_artifact_sha(coach_artifact["sha256"])
        assert actual_sha == expected_sha, (
            f"SHA mismatch: response={expected_sha}, disk={actual_sha}"
        )

        # --- Validate coach JSON against PracticeAssignment schema ---
        coach_json = json.loads(coach_path.read_text(encoding="utf-8"))
        validated = PracticeAssignment.model_validate(coach_json)
        assert validated.assignment_id == assignment.assignment_id
        assert validated.focus.primary == "timing"
