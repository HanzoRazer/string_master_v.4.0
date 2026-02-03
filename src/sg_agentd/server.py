"""
sg-agentd HTTP Server

Minimal FastAPI service for generation orchestration.

Run:
    uvicorn sg_agentd.server:app --reload --port 7878

Test:
    curl -X POST http://localhost:7878/generate -H "Content-Type: application/json" \
         -d '{"request_id": "...", "harmony": {"chord_symbols": ["Dm7", "G7", "Cmaj7"]}, ...}'

Phase 4: Attempt loop with deterministic seed derivation and range validation.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from sg_agentd.loop import run_attempt_loop
from sg_agentd.validators import extract_range_limit

# ============================================================================
# Lazy imports to avoid hard dependency on sg-spec during tests
# ============================================================================

def _import_contracts():
    """Import generation contracts from sg-spec."""
    try:
        from sg_spec.schemas.generation import (
            GenerationRequest,
            GenerationResult,
            MidiArtifact,
            JsonArtifact,
            ValidationReport,
            RunLog,
        )
        return {
            "GenerationRequest": GenerationRequest,
            "GenerationResult": GenerationResult,
            "MidiArtifact": MidiArtifact,
            "JsonArtifact": JsonArtifact,
            "ValidationReport": ValidationReport,
            "RunLog": RunLog,
        }
    except ImportError as e:
        raise RuntimeError(
            "sg-spec not installed. Run: pip install -e /path/to/sg-spec"
        ) from e


def _import_zt_band():
    """Import zt_band generation engine."""
    try:
        from zt_band.engine import generate_accompaniment
        from zt_band.bundle_writer import write_clip_bundle_default, BundleResult
        from zt_band.midi_out import NoteEvent
        return {
            "generate_accompaniment": generate_accompaniment,
            "write_clip_bundle_default": write_clip_bundle_default,
            "BundleResult": BundleResult,
            "NoteEvent": NoteEvent,
        }
    except ImportError as e:
        raise RuntimeError(
            "zt_band not installed. Run: pip install -e /path/to/string_master_v.4.0"
        ) from e


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="sg-agentd",
    description="Generation orchestrator for Smart Guitar AI Infrastructure",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "sg-agentd", "version": "0.1.0"}


@app.post("/generate")
def generate_endpoint(payload: Dict[str, Any]):
    """
    Generate accompaniment and emit 4-file bundle.

    Accepts GenerationRequest (validated via sg-spec),
    calls zt_band.engine.generate_accompaniment,
    writes bundle via bundle_writer,
    returns GenerationResult.

    Phase 4: Attempt loop with seed derivation and range validation.
    """
    contracts = _import_contracts()
    zt_band = _import_zt_band()

    GenerationRequest = contracts["GenerationRequest"]
    GenerationResult = contracts["GenerationResult"]
    MidiArtifact = contracts["MidiArtifact"]
    JsonArtifact = contracts["JsonArtifact"]
    ValidationReport = contracts["ValidationReport"]
    RunLog = contracts["RunLog"]

    generate_accompaniment = zt_band["generate_accompaniment"]
    write_clip_bundle_default = zt_band["write_clip_bundle_default"]

    # ---- Validate request ----
    try:
        request = GenerationRequest.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    start_time = time.perf_counter()

    # ---- Extract parameters ----
    chord_symbols = request.harmony.chord_symbols
    style_name = request.style.style_name
    tempo_bpm = request.style.tempo_bpm
    bars_per_chord = request.harmony.bars_per_chord

    tritone_mode = request.tritone.mode
    tritone_strength = request.tritone.strength
    tritone_seed = request.tritone.seed

    # Contract intent → engine implementation mapping
    # sg-spec uses "subs" (intent). zt_band expects "all_doms" (impl detail).
    if tritone_mode == "subs":
        tritone_mode = "all_doms"

    attempt_budget = request.constraints.attempt_budget
    pitch_range_limit = extract_range_limit(request.constraints)

    # ---- Build generate function for loop ----
    def make_generate_fn(seed: int):
        """Generate with derived seed."""
        return generate_accompaniment(
            chord_symbols=chord_symbols,
            style_name=style_name,
            tempo_bpm=tempo_bpm,
            bars_per_chord=bars_per_chord,
            tritone_mode=tritone_mode,
            tritone_strength=tritone_strength,
            tritone_seed=seed,
            style_overrides=request.style.overrides,
        )

    # ---- Run attempt loop ----
    loop_outcome = run_attempt_loop(
        request_id=request.request_id,
        explicit_seed=tritone_seed,
        attempt_budget=attempt_budget,
        generate_fn=make_generate_fn,
        pitch_range_limit=pitch_range_limit,
    )

    # ---- Handle loop outcome ----
    if loop_outcome.status == "failed":
        # All attempts crashed
        all_violations = []
        for attempt in loop_outcome.attempts:
            all_violations.extend(attempt.violations)
        return _build_error_result(
            request_id=request.request_id,
            code="GENERATION_FAILED",
            message="; ".join(all_violations) if all_violations else "All attempts failed",
            contracts=contracts,
        )

    # Get selected attempt
    selected = loop_outcome.attempts[loop_outcome.selected_attempt]
    comp_events = selected.comp_events
    bass_events = selected.bass_events

    # ---- Write bundle ----
    try:
        bundle_result = write_clip_bundle_default(
            comp_events=comp_events,
            bass_events=bass_events,
            tempo_bpm=tempo_bpm,
            clip_id=f"gen_{request.request_id.hex[:12]}",
            inputs={
                "request_id": str(request.request_id),
                "requester": request.requester,
                "chord_symbols": chord_symbols,
                "style_name": style_name,
                "tritone_mode": tritone_mode,
                "tritone_seed": selected.seed_used,
            },
            assignment=request.assignment,  # Coach integration (PR5)
            collision_policy="fail",
        )
    except Exception as e:
        return _build_error_result(
            request_id=request.request_id,
            code="BUNDLE_WRITE_FAILED",
            message=str(e),
            contracts=contracts,
        )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    # ---- Build result from BundleResult ----
    midi_artifact = None
    tags_artifact = None
    runlog_artifact = None

    if "clip.mid" in bundle_result.artifacts:
        art = bundle_result.artifacts["clip.mid"]
        midi_artifact = MidiArtifact(
            path=str(art.path),
            sha256=art.sha256,
            track_count=2,  # comp + bass
            duration_beats=float(len(chord_symbols) * bars_per_chord * 4),
        )

    if "clip.tags.json" in bundle_result.artifacts:
        art = bundle_result.artifacts["clip.tags.json"]
        tags_artifact = JsonArtifact(path=str(art.path), sha256=art.sha256)

    if "clip.runlog.json" in bundle_result.artifacts:
        art = bundle_result.artifacts["clip.runlog.json"]
        runlog_artifact = JsonArtifact(path=str(art.path), sha256=art.sha256)

    # ---- Coach artifact (conditional) ----
    coach_artifact = None
    if "clip.coach.json" in bundle_result.artifacts:
        art = bundle_result.artifacts["clip.coach.json"]
        coach_artifact = JsonArtifact(path=str(art.path), sha256=art.sha256)

    # ---- Collect warnings from all attempts ----
    all_warnings = []
    for attempt in loop_outcome.attempts:
        all_warnings.extend(attempt.warnings)

    # ---- Build result ----
    result = GenerationResult(
        request_id=request.request_id,
        generated_at_utc=datetime.now(timezone.utc),
        status=loop_outcome.status,  # "ok" or "partial"
        midi=midi_artifact,
        tags=tags_artifact,
        runlog=runlog_artifact,
        coach=coach_artifact,
        validation=ValidationReport(
            passed=(loop_outcome.status == "ok"),
            violations=selected.violations,
            warnings=all_warnings,
        ),
        run_log=RunLog(
            engine_module="zt_band.engine",
            engine_function="generate_accompaniment",
            duration_ms=loop_outcome.total_duration_ms,
            attempts_used=len(loop_outcome.attempts),
            seed_used=selected.seed_used,
        ),
        bundle_path=str(bundle_result.bundle_dir),
    )

    return result.model_dump(mode="json")


def _build_error_result(
    request_id: UUID,
    code: str,
    message: str,
    contracts: dict,
) -> dict:
    """Build a failed GenerationResult."""
    GenerationResult = contracts["GenerationResult"]
    ValidationReport = contracts["ValidationReport"]
    RunLog = contracts["RunLog"]

    result = GenerationResult(
        request_id=request_id,
        generated_at_utc=datetime.now(timezone.utc),
        status="failed",
        validation=ValidationReport(passed=False, violations=[message]),
        run_log=RunLog(
            engine_module="zt_band.engine",
            engine_function="generate_accompaniment",
            duration_ms=0,
            attempts_used=1,  # Minimum is 1 (pre-validation failure counts as 1 attempt)
        ),
        error_code=code,
        error_message=message,
    )
    return result.model_dump(mode="json")


# ============================================================================
# CLI entrypoint (optional)
# ============================================================================

def main():
    """Run the server via uvicorn."""
    import uvicorn
    uvicorn.run("sg_agentd.server:app", host="0.0.0.0", port=7878, reload=True)


if __name__ == "__main__":
    main()
