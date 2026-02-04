"""
Planner implementations for sg_coach.

Various versions of the planning algorithm for assignment generation.

Migrated from sg-spec to string_master for proper architectural boundaries.
Schemas remain in sg-spec; this module contains business logic.
"""
from .v0_4 import (
    AssignmentV0_4,
    CoachFeedbackCompat,
    PlannerPolicyV0_4,
    DEFAULT_POLICY_V0_4,
    plan_next_v0_4,
)
from .v0_5 import (
    PlannerPolicyV0_5,
    DEFAULT_POLICY_V0_5,
    plan_next_v0_5,
)
from .v0_6 import (
    PlannerPolicyV0_6,
    DEFAULT_POLICY_V0_6,
    plan_next_v0_6,
)

__all__ = [
    # v0.4
    "AssignmentV0_4",
    "CoachFeedbackCompat",
    "PlannerPolicyV0_4",
    "DEFAULT_POLICY_V0_4",
    "plan_next_v0_4",
    # v0.5
    "PlannerPolicyV0_5",
    "DEFAULT_POLICY_V0_5",
    "plan_next_v0_5",
    # v0.6
    "PlannerPolicyV0_6",
    "DEFAULT_POLICY_V0_6",
    "plan_next_v0_6",
]
