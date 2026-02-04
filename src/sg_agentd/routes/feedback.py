"""
Feedback Route (Episode 10 + 11)

Endpoint for receiving performance feedback and returning suggested adjustments.
Episode 11 adds coach_hint to the response.
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from sg_agentd.services.progression_policy import apply_progression_policy


# ============================================================================
# Request/Response Models
# ============================================================================

class FeedbackRequest(BaseModel):
    """Incoming performance feedback from the client."""

    score: float
    prior_difficulty: float
    prior_tempo_bpm: float
    policy_id: str = "v1_default"
    score_trend: Optional[float] = None


class SuggestedAdjustment(BaseModel):
    """
    Suggested adjustments for the next iteration.

    Episode 11: Added coach_hint field for user-facing narrative.
    """

    difficulty_delta: float
    tempo_delta_bpm: float
    density_hint: Literal["sparse", "medium", "dense"]
    syncopation_hint: Literal["straight", "light", "heavy"]
    rationale: str
    coach_hint: str  # NEW (Episode 11)
    score: float  # keep last


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=SuggestedAdjustment)
def submit_feedback(request: FeedbackRequest) -> SuggestedAdjustment:
    """
    Process performance feedback and return suggested adjustments.

    The policy engine determines difficulty, tempo, density, and syncopation
    changes based on the score and optional trend data.
    """
    decision = apply_progression_policy(
        score=request.score,
        prior_difficulty=request.prior_difficulty,
        prior_tempo_bpm=request.prior_tempo_bpm,
        policy_id=request.policy_id,
        score_trend=request.score_trend,
    )

    suggested = SuggestedAdjustment(
        difficulty_delta=decision.difficulty_delta,
        tempo_delta_bpm=decision.tempo_delta_bpm,
        density_hint=decision.density_bucket,
        syncopation_hint=decision.syncopation_bucket,
        rationale=decision.rationale,
        coach_hint=decision.coach_hint,  # NEW (Episode 11)
        score=request.score,
    )

    return suggested
