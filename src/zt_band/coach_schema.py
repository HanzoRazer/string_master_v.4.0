"""
zt_band coach_schema — re-exported from sg_coach.schemas.

This module is a thin wrapper for backward compatibility.
All types are defined in sg_coach.schemas (single source of truth).

Legacy aliases are provided for backward compatibility with existing code.
"""
from sg_coach.schemas import (
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

# Legacy aliases for backward compatibility
TimingConfig = SessionTiming
PerformanceMetrics = PerformanceSummary
Finding = CoachFinding
AssignmentProgram = ProgramRef
PracticeConstraints = AssignmentConstraints
PracticeFocus = AssignmentFocus

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
    # Legacy aliases
    "TimingConfig",
    "PerformanceMetrics",
    "Finding",
    "AssignmentProgram",
    "PracticeConstraints",
    "PracticeFocus",
]
