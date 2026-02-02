"""
Pitch range validator for generated MIDI output.

Checks that generated notes stay within acceptable pitch span,
useful for ensuring playability on instruments with limited range.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RangeResult:
    """Result of pitch range validation.
    
    Attributes:
        passed: True if all notes within range limit
        actual_span: max(notes) - min(notes), or None if no notes
        limit: The constraint that was checked
        violations: List of violation messages (if any)
        warnings: List of warning messages (if any)
    """
    passed: bool
    actual_span: Optional[int]
    limit: int
    violations: list[str]
    warnings: list[str]


def validate_pitch_range(
    comp_events: list[Any],
    bass_events: list[Any],
    limit: int = 24,
) -> RangeResult:
    """
    Validate that all generated notes fall within pitch span limit.
    
    Combines notes from both comp and bass tracks, computes span as
    max(notes) - min(notes), and checks against limit.
    
    Args:
        comp_events: List of NoteEvent from comp track
        bass_events: List of NoteEvent from bass track
        limit: Maximum allowed pitch span (default 24 = 2 octaves)
        
    Returns:
        RangeResult with validation outcome
    """
    # Extract MIDI pitches from events
    # NoteEvent has .note attribute (MIDI pitch 0-127)
    all_notes: list[int] = []
    
    for event in comp_events:
        if hasattr(event, "note"):
            all_notes.append(event.note)
    
    for event in bass_events:
        if hasattr(event, "note"):
            all_notes.append(event.note)
    
    # Handle empty case
    if not all_notes:
        return RangeResult(
            passed=True,
            actual_span=None,
            limit=limit,
            violations=[],
            warnings=["No notes found in generated output"],
        )
    
    min_note = min(all_notes)
    max_note = max(all_notes)
    actual_span = max_note - min_note
    
    if actual_span <= limit:
        return RangeResult(
            passed=True,
            actual_span=actual_span,
            limit=limit,
            violations=[],
            warnings=[],
        )
    else:
        return RangeResult(
            passed=False,
            actual_span=actual_span,
            limit=limit,
            violations=[
                f"Pitch span {actual_span} exceeds limit {limit} "
                f"(min={min_note}, max={max_note})"
            ],
            warnings=[],
        )


def extract_range_limit(constraints: Any) -> int:
    """
    Extract pitch_range_semitones from constraints, with default.
    
    Args:
        constraints: GenerationConstraints object or dict
        
    Returns:
        Pitch range limit in semitones (default 24 = 2 octaves)
    """
    default_limit = 24
    
    if constraints is None:
        return default_limit
    
    # Handle dict-like access
    if isinstance(constraints, dict):
        return constraints.get("pitch_range_semitones", default_limit)
    
    # Handle object attribute access
    return getattr(constraints, "pitch_range_semitones", default_limit)
