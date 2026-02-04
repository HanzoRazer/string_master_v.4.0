"""
Smart Guitar Coach Module (sg_coach)

Business logic for coaching, evaluation, assignment planning, and OTA bundles.
Migrated from sg-spec to maintain proper architectural boundaries.

Schemas remain in sg-spec; this module contains the business logic that
operates on those schemas.

Submodules:
- evaluation: Post-session evaluation (SessionRecord -> CoachEvaluation)
- assignment: Assignment planning (CoachEvaluation -> PracticeAssignment)
- ota: OTA bundle building and verification
- serializer: Assignment serialization
- cli: Command-line interface (sgc)
- planners: Various planner implementations
"""

from .evaluation import evaluate_session, COACH_VERSION
from .assignment import plan_assignment, AssignmentPolicyConfig

__all__ = [
    "evaluate_session",
    "COACH_VERSION",
    "plan_assignment",
    "AssignmentPolicyConfig",
]
