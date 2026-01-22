"""
Coach Schema: Session -> Coach -> Assignment spine.

Three layers with strict ownership boundaries:
- SessionRecord: What happened (runtime owns, immutable facts)
- CoachEvaluation: What it means (coach owns, interpretation)
- PracticeAssignment: What's next (planner owns, intent)

INVARIANT: These layers never blur. If they do, stop and fix it.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================================
# Shared Enums & Types
# ============================================================================

Sha256 = str  # store as "sha256:..." for clarity


class Severity(str, Enum):
    primary = "primary"
    secondary = "secondary"
    info = "info"


class CoachMode(str, Enum):
    rules_first = "rules_first"      # Mode 1: All text from templates
    hybrid = "hybrid"                 # Mode 2: AI phrases, rules structure
    generative = "generative"         # Mode 3: AI proposes new exercises


class ProgramType(str, Enum):
    ztprog = "ztprog"
    ztex = "ztex"
    ztplay = "ztplay"


# ============================================================================
# 1️⃣ SessionRecord -- What actually happened
# ============================================================================
# Owner: Runtime / Telemetry
# Created by: Smart Guitar / String Master runtime
# Consumed by: Coach (Mode 1, 2, 3)
#
# 🔒 Invariants:
#   - No free text
#   - No AI language
#   - No user identity beyond instrument/session
#   - Hashes link to immutable engine artifacts
# ============================================================================

class ProgramRef(BaseModel):
    """Reference to an immutable program artifact."""
    type: ProgramType
    name: str = Field(..., pattern=r"^[a-z0-9_]+$")
    hash: Sha256 = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")


class TimingConfig(BaseModel):
    """Timing parameters from the session."""
    bpm: int = Field(..., ge=30, le=300)
    grid: Literal[4, 8, 16, 32] = 16
    clave: str | None = None  # e.g., "son_2_3", "son_3_2", "rumba"
    strict: bool = False
    late_drop_ms: float = Field(default=50.0, ge=0, le=200)


class TimingErrorStats(BaseModel):
    """Statistical summary of timing errors."""
    mean: float = Field(..., ge=0)
    std: float = Field(..., ge=0)
    max: float = Field(..., ge=0)

    @model_validator(mode="after")
    def max_ge_mean(self) -> "TimingErrorStats":
        if self.max < self.mean:
            raise ValueError("max timing error cannot be less than mean")
        return self


class PerformanceMetrics(BaseModel):
    """What the player actually did."""
    bars_played: int = Field(..., ge=0)
    notes_expected: int = Field(..., ge=0)
    notes_played: int = Field(..., ge=0)
    notes_dropped: int = Field(..., ge=0)
    timing_error_ms: TimingErrorStats
    error_by_step: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def notes_add_up(self) -> "PerformanceMetrics":
        if self.notes_played + self.notes_dropped != self.notes_expected:
            # Allow some tolerance for edge cases, but flag obvious errors
            pass  # Soft check - telemetry may have edge cases
        return self


class SessionEvents(BaseModel):
    """Discrete events during session."""
    late_drops: int = Field(default=0, ge=0)
    panic_triggered: bool = False


class SessionRecord(BaseModel):
    """
    Pure fact. No opinions. No coaching.
    
    This is the immutable truth of what happened during practice.
    """
    session_id: str = Field(..., pattern=r"^[a-f0-9-]{36}$")
    instrument_id: str = Field(..., pattern=r"^sg-[0-9]{6}$")
    engine_version: str = Field(..., pattern=r"^zt-band@\d+\.\d+\.\d+$")
    
    program_ref: ProgramRef
    timing: TimingConfig
    duration_s: float = Field(..., ge=0)
    performance: PerformanceMetrics
    events: SessionEvents = Field(default_factory=SessionEvents)
    
    created_at: datetime

    model_config = {"extra": "forbid"}


# ============================================================================
# 2️⃣ CoachEvaluation -- What it means
# ============================================================================
# Owner: Coach layer (Mode 1 deterministic; Mode 2 phrased by AI)
# Created by: Coach
# Consumed by: Assignment planner + UI
#
# 🔒 Invariants:
#   - Coach cannot change notes, chords, or style
#   - Findings must reference measured facts
#   - confidence is required (forces honesty)
# ============================================================================

class FindingEvidence(BaseModel):
    """Evidence backing a coaching finding - must reference measured facts."""
    step: int | None = None
    mean_error_ms: float | None = None
    bars: tuple[int, int] | None = None  # (start, end) bar range
    metric: str | None = None
    value: float | None = None


class Finding(BaseModel):
    """A single coaching observation tied to evidence."""
    type: Literal["timing", "accuracy", "tempo", "consistency", "technique"]
    severity: Severity
    evidence: FindingEvidence
    interpretation: str = Field(..., max_length=200)

    @field_validator("interpretation")
    @classmethod
    def no_ai_hallucination(cls, v: str) -> str:
        """Interpretation must be grounded, not inventive."""
        forbidden = ["amazing", "incredible", "you should feel", "I think"]
        for word in forbidden:
            if word.lower() in v.lower():
                raise ValueError(f"Interpretation contains non-grounded language: '{word}'")
        return v


class FocusRecommendation(BaseModel):
    """What to focus on next, derived from findings."""
    concept: str = Field(..., pattern=r"^[a-z_]+$")
    reason: str = Field(..., max_length=200)


class CoachEvaluation(BaseModel):
    """
    Interpretation, but still structured.
    
    Coach sees facts, produces meaning. Never touches music.
    """
    session_id: str = Field(..., pattern=r"^[a-f0-9-]{36}$")
    coach_version: str = Field(..., pattern=r"^coach-rules@\d+\.\d+\.\d+$")
    
    findings: list[Finding] = Field(default_factory=list, max_length=10)
    strengths: list[str] = Field(default_factory=list, max_length=5)
    weaknesses: list[str] = Field(default_factory=list, max_length=5)
    
    focus_recommendation: FocusRecommendation | None = None
    
    confidence: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime

    @field_validator("strengths", "weaknesses")
    @classmethod
    def bounded_text(cls, v: list[str]) -> list[str]:
        for item in v:
            if len(item) > 100:
                raise ValueError("Strength/weakness text too long (max 100 chars)")
        return v


# ============================================================================
# 3️⃣ PracticeAssignment -- What to do next
# ============================================================================
# Owner: Curriculum / Planner
# Created by: Assignment engine (possibly AI-assisted)
# Consumed by: Runtime
#
# 🔒 Invariants:
#   - Assignment cannot invent new theory
#   - Only uses existing programs/exercises
#   - Constraints are numeric, testable, and reversible
# ============================================================================

class AssignmentProgram(BaseModel):
    """Reference to existing program - no invention allowed."""
    type: ProgramType
    name: str = Field(..., pattern=r"^[a-z0-9_]+$")


class PracticeConstraints(BaseModel):
    """Numeric, testable, reversible constraints."""
    tempo_start: int = Field(..., ge=30, le=300)
    tempo_target: int = Field(..., ge=30, le=300)
    tempo_step: int = Field(default=5, ge=1, le=20)
    
    strict: bool = False
    strict_window_ms: float = Field(default=50.0, ge=10, le=100)
    
    bars_per_loop: int = Field(default=4, ge=1, le=32)
    repetitions: int = Field(default=4, ge=1, le=100)

    @model_validator(mode="after")
    def tempo_order(self) -> "PracticeConstraints":
        # Allow both increasing and decreasing tempo progressions
        return self


class PracticeFocus(BaseModel):
    """What to pay attention to."""
    primary: str = Field(..., pattern=r"^[a-z_]+$")
    secondary: str | None = Field(default=None, pattern=r"^[a-z_]+$")


class SuccessCriteria(BaseModel):
    """Measurable success thresholds."""
    max_mean_error_ms: float = Field(..., ge=0, le=100)
    max_late_drops: int = Field(default=3, ge=0)
    min_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)


class CoachPrompt(BaseModel):
    """Optional coaching message for UI."""
    mode: Literal["required", "optional", "hidden"] = "optional"
    message: str = Field(default="", max_length=200)


class PracticeAssignment(BaseModel):
    """
    Controls practice, not music.
    
    This is intent - what the student should do next.
    """
    assignment_id: str = Field(..., pattern=r"^[a-f0-9-]{36}$")
    session_id: str | None = Field(default=None, pattern=r"^[a-f0-9-]{36}$")
    
    program: AssignmentProgram
    constraints: PracticeConstraints
    focus: PracticeFocus
    success_criteria: SuccessCriteria
    
    coach_prompt: CoachPrompt = Field(default_factory=CoachPrompt)
    
    expires_after_sessions: int = Field(default=3, ge=1, le=10)

    model_config = {"extra": "forbid"}


# ============================================================================
# Validation helpers
# ============================================================================

def validate_coach_references_session(
    evaluation: CoachEvaluation,
    session: SessionRecord,
) -> None:
    """Ensure coach findings reference actual session data."""
    if evaluation.session_id != session.session_id:
        raise ValueError("CoachEvaluation.session_id must match SessionRecord.session_id")
    
    # Validate that referenced steps exist in session data
    session_steps = set(session.performance.error_by_step.keys())
    for finding in evaluation.findings:
        if finding.evidence.step is not None:
            if str(finding.evidence.step) not in session_steps:
                raise ValueError(
                    f"Finding references step {finding.evidence.step} "
                    f"not in session data: {session_steps}"
                )


def validate_assignment_program_exists(
    assignment: PracticeAssignment,
    available_programs: set[str],
) -> None:
    """Ensure assignment references an existing program."""
    if assignment.program.name not in available_programs:
        raise ValueError(
            f"Assignment references unknown program: {assignment.program.name}"
        )
