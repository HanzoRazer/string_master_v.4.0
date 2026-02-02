"""
Attempt loop orchestrator for sg_agentd.

Runs generation attempts up to budget, validates each attempt,
and selects the best candidate (or signals failure).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from uuid import UUID

from sg_agentd.seed import choose_seed_sequence
from sg_agentd.validators import validate_pitch_range, extract_range_limit


@dataclass
class AttemptRecord:
    """Record of a single generation attempt.
    
    Attributes:
        attempt_index: 0-indexed attempt number
        seed_used: Seed that was used for generation
        duration_ms: Time spent on this attempt
        passed_validation: True if attempt passed all validators
        violations: List of violation messages
        warnings: List of warning messages
        comp_events: Generated comp events (if successful)
        bass_events: Generated bass events (if successful)
    """
    attempt_index: int
    seed_used: int
    duration_ms: int
    passed_validation: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    comp_events: Optional[list[Any]] = None
    bass_events: Optional[list[Any]] = None


@dataclass
class LoopOutcome:
    """Outcome of the attempt loop.
    
    Attributes:
        status: "ok" (passed), "partial" (exhausted but best exists), "failed"
        attempts: List of all attempt records
        selected_attempt: Index of selected attempt, or None if failed
        total_duration_ms: Total time across all attempts
    """
    status: str  # "ok" | "partial" | "failed"
    attempts: list[AttemptRecord]
    selected_attempt: Optional[int]
    total_duration_ms: int


def run_attempt_loop(
    request_id: UUID,
    explicit_seed: Optional[int],
    attempt_budget: int,
    generate_fn: Callable[[int], tuple[list[Any], list[Any]]],
    pitch_range_limit: int = 24,
) -> LoopOutcome:
    """
    Run generation attempts up to budget, validating each.
    
    For each attempt:
    1. Derive seed from request_id + attempt_index (or use explicit seed)
    2. Call generate_fn(seed) to get (comp_events, bass_events)
    3. Validate output against constraints
    4. If passes: return immediately with "ok"
    5. If fails: record and continue to next attempt
    
    After exhausting budget:
    - If any attempt exists: return "partial" with best (first) attempt
    - If all attempts crashed: return "failed"
    
    Args:
        request_id: UUID identifying the generation request
        explicit_seed: User-provided seed (if any)
        attempt_budget: Maximum attempts allowed
        generate_fn: Function(seed) -> (comp_events, bass_events)
        pitch_range_limit: Max pitch span in semitones
        
    Returns:
        LoopOutcome with status, attempts, and selection
    """
    attempts: list[AttemptRecord] = []
    total_start = time.perf_counter()
    
    for attempt_index in range(attempt_budget):
        attempt_start = time.perf_counter()
        
        # Derive seed for this attempt
        seed = choose_seed_sequence(
            request_id=request_id,
            attempt_index=attempt_index,
            explicit_seed=explicit_seed,
        )
        
        # Try generation
        try:
            comp_events, bass_events = generate_fn(seed)
        except Exception as e:
            # Generation crashed - record and continue
            attempt_duration = int((time.perf_counter() - attempt_start) * 1000)
            attempts.append(AttemptRecord(
                attempt_index=attempt_index,
                seed_used=seed,
                duration_ms=attempt_duration,
                passed_validation=False,
                violations=[f"Generation failed: {e}"],
            ))
            continue
        
        # Validate pitch range
        range_result = validate_pitch_range(
            comp_events=comp_events,
            bass_events=bass_events,
            limit=pitch_range_limit,
        )
        
        attempt_duration = int((time.perf_counter() - attempt_start) * 1000)
        
        # Build attempt record
        record = AttemptRecord(
            attempt_index=attempt_index,
            seed_used=seed,
            duration_ms=attempt_duration,
            passed_validation=range_result.passed,
            violations=range_result.violations,
            warnings=range_result.warnings,
            comp_events=comp_events,
            bass_events=bass_events,
        )
        attempts.append(record)
        
        # If passed, we're done
        if range_result.passed:
            total_duration = int((time.perf_counter() - total_start) * 1000)
            return LoopOutcome(
                status="ok",
                attempts=attempts,
                selected_attempt=attempt_index,
                total_duration_ms=total_duration,
            )
    
    # Budget exhausted
    total_duration = int((time.perf_counter() - total_start) * 1000)
    
    # Find best candidate (first one with output, even if failed validation)
    best_attempt = None
    for i, record in enumerate(attempts):
        if record.comp_events is not None and record.bass_events is not None:
            best_attempt = i
            break
    
    if best_attempt is not None:
        return LoopOutcome(
            status="partial",
            attempts=attempts,
            selected_attempt=best_attempt,
            total_duration_ms=total_duration,
        )
    else:
        return LoopOutcome(
            status="failed",
            attempts=attempts,
            selected_attempt=None,
            total_duration_ms=total_duration,
        )
