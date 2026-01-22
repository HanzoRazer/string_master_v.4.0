"""
sg_coach models — re-exported from shared.coach_schemas.

This module is a thin wrapper for backward compatibility.
All types are defined in shared/coach_schemas.py (single source of truth).
"""
from shared.coach_schemas import (
    # Type aliases
    Sha256,
    # Enums
    ProgramType,
    Severity,
    ClaveKind,
    CoachMode,
    # Shared
    ProgramRef,
    # Session layer
    SessionTiming,
    TimingErrorStats,
    PerformanceSummary,
    SessionEvents,
    SessionRecord,
    # Coach layer
    FindingEvidence,
    CoachFinding,
    FocusRecommendation,
    CoachEvaluation,
    # Assignment layer
    AssignmentConstraints,
    AssignmentFocus,
    SuccessCriteria,
    CoachPrompt,
    PracticeAssignment,
    # Validators
    validate_coach_references_session,
    validate_assignment_program_exists,
)

__all__ = [
    # Type aliases
    "Sha256",
    # Enums
    "ProgramType",
    "Severity",
    "ClaveKind",
    "CoachMode",
    # Shared
    "ProgramRef",
    # Session layer
    "SessionTiming",
    "TimingErrorStats",
    "PerformanceSummary",
    "SessionEvents",
    "SessionRecord",
    # Coach layer
    "FindingEvidence",
    "CoachFinding",
    "FocusRecommendation",
    "CoachEvaluation",
    # Assignment layer
    "AssignmentConstraints",
    "AssignmentFocus",
    "SuccessCriteria",
    "CoachPrompt",
    "PracticeAssignment",
    # Validators
    "validate_coach_references_session",
    "validate_assignment_program_exists",
]
