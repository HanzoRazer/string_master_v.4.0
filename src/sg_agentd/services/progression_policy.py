"""
Progression Policy (Episode 10 + 11)

Deterministic difficulty/tempo/density/sync adaptation logic.
Episode 11 adds coach_hint for user-facing narrative.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Type aliases for buckets
# ============================================================================

Density = Literal["sparse", "medium", "dense"]
Sync = Literal["straight", "light", "heavy"]


# ============================================================================
# Policy decision model
# ============================================================================

class ProgressionDecision(BaseModel):
    """
    Output of the progression policy.

    Describes what adjustments to make for the next iteration,
    with deterministic coach hint (Episode 11).
    """

    difficulty_delta: float
    tempo_delta_bpm: float
    density_bucket: Density
    syncopation_bucket: Sync
    rationale: str
    coach_hint: str = ""  # NEW (Episode 11)
    policy_version: str = Field(default="v1")


# ============================================================================
# Policy tables (deterministic, no ML)
# ============================================================================

# Score thresholds for band classification
SCORE_BANDS = {
    "excellent": 85.0,
    "solid": 70.0,
    "stable": 55.0,
    "recover": 40.0,
    # Below 40 = "reset"
}

# Difficulty deltas by score band
DIFFICULTY_DELTAS = {
    "excellent": 0.05,
    "solid": 0.02,
    "stable": 0.0,
    "recover": -0.03,
    "reset": -0.05,
}

# Tempo deltas by score band
TEMPO_DELTAS = {
    "excellent": 3.0,
    "solid": 1.0,
    "stable": 0.0,
    "recover": -2.0,
    "reset": -5.0,
}

# Density bucket by score band
DENSITY_BY_BAND = {
    "excellent": "dense",
    "solid": "medium",
    "stable": "medium",
    "recover": "sparse",
    "reset": "sparse",
}

# Syncopation bucket by score band
SYNC_BY_BAND = {
    "excellent": "heavy",
    "solid": "light",
    "stable": "straight",
    "recover": "straight",
    "reset": "straight",
}


def _score_to_band(score: float) -> str:
    """Classify score into a named band."""
    if score >= SCORE_BANDS["excellent"]:
        return "excellent"
    if score >= SCORE_BANDS["solid"]:
        return "solid"
    if score >= SCORE_BANDS["stable"]:
        return "stable"
    if score >= SCORE_BANDS["recover"]:
        return "recover"
    return "reset"


def _apply_trend_adjustments(
    decision: ProgressionDecision,
    score_trend: float | None,
) -> ProgressionDecision:
    """
    Adjust decision based on score trend (last N sessions).

    Positive trend = improving → slightly more aggressive
    Negative trend = declining → slightly more conservative
    """
    if score_trend is None:
        return decision

    # Trend thresholds
    if score_trend > 5.0:
        # Strong upward trend: push harder
        return ProgressionDecision(
            difficulty_delta=decision.difficulty_delta + 0.01,
            tempo_delta_bpm=decision.tempo_delta_bpm + 1.0,
            density_bucket=decision.density_bucket,
            syncopation_bucket=decision.syncopation_bucket,
            rationale=f"{decision.rationale} (trend boost: +{score_trend:.1f})",
            coach_hint=decision.coach_hint,
            policy_version=decision.policy_version,
        )
    elif score_trend < -5.0:
        # Strong downward trend: pull back
        return ProgressionDecision(
            difficulty_delta=decision.difficulty_delta - 0.01,
            tempo_delta_bpm=decision.tempo_delta_bpm - 1.0,
            density_bucket=decision.density_bucket,
            syncopation_bucket=decision.syncopation_bucket,
            rationale=f"{decision.rationale} (trend caution: {score_trend:.1f})",
            coach_hint=decision.coach_hint,
            policy_version=decision.policy_version,
        )

    return decision


# ============================================================================
# Coach Hint Builder (Episode 11)
# ============================================================================

def _trend_bucket(score_trend: float | None) -> str:
    """Classify trend into up/down/flat."""
    if score_trend is None:
        return "flat"
    if score_trend > 2.0:
        return "up"
    if score_trend < -2.0:
        return "down"
    return "flat"


def _describe_changes(decision: ProgressionDecision) -> str:
    """Build a short description of the changes being made."""
    # Tempo clause
    if decision.tempo_delta_bpm > 0:
        tempo_clause = f"Tempo up by {decision.tempo_delta_bpm:.0f} BPM."
    elif decision.tempo_delta_bpm < 0:
        tempo_clause = f"Tempo down by {abs(decision.tempo_delta_bpm):.0f} BPM."
    else:
        tempo_clause = "Tempo unchanged."

    # Density / sync clauses
    dens_clause = f"Density: {decision.density_bucket}."
    sync_clause = f"Sync: {decision.syncopation_bucket}."

    return f"{tempo_clause} {dens_clause} {sync_clause}"


def build_coach_hint(
    score: float,
    score_trend: float | None,
    decision: ProgressionDecision,
) -> str:
    """
    Build a deterministic, human-friendly coach hint.

    Uses score band × trend bucket matrix (5 × 3 = 15 templates).
    """
    band = _score_to_band(score)
    tb = _trend_bucket(score_trend)
    changes = _describe_changes(decision)

    # 5 bands × 3 trend buckets
    if band == "excellent":
        if tb == "up":
            return f"Your control is strong and improving. Keep it clean while we push the next rep. {changes}"
        if tb == "down":
            return f"Still strong overall, but the last rep dipped. Focus on clean chord hits before the push. {changes}"
        return f"Strong control. Keep consistency and let the next rep stretch you slightly. {changes}"

    if band == "solid":
        if tb == "up":
            return f"Nice improvement. Keep the groove steady and aim for tighter chord landings. {changes}"
        if tb == "down":
            return f"Good work, but it's slipping a bit. Prioritize timing accuracy over speed. {changes}"
        return f"Solid. Hold steady and try to reduce timing error on the next loop. {changes}"

    if band == "stable":
        if tb == "up":
            return f"You're stabilizing and trending up. Keep it relaxed and consistent. {changes}"
        if tb == "down":
            return f"You're close, but trending down. Simplify your focus: timing first, then chord hits. {changes}"
        return f"Hold here and stabilize—aim for fewer misses and steadier time. {changes}"

    if band == "recover":
        if tb == "up":
            return f"Recovering and improving. Stay patient and lock the downbeats. {changes}"
        if tb == "down":
            return f"Trending down—reset your approach: slower, simpler, and perfectly in time. {changes}"
        return f"Let's reduce load and rebuild control: steady time and clean hits. {changes}"

    # reset band
    if tb == "up":
        return f"Good—starting to recover. Keep it simple and accurate. {changes}"
    if tb == "down":
        return f"Pause and reset fundamentals: strict time, simplest voicings, no rushing. {changes}"
    return f"Reset fundamentals: play it simple, in time, and aim for clean chord hits. {changes}"


# ============================================================================
# Main Policy Function
# ============================================================================

def apply_progression_policy(
    score: float,
    prior_difficulty: float,
    prior_tempo_bpm: float,
    policy_id: str = "v1_default",
    score_trend: float | None = None,
) -> ProgressionDecision:
    """
    Apply the progression policy to determine next iteration adjustments.

    Parameters
    ----------
    score:
        Current performance score (0-100).
    prior_difficulty:
        Current difficulty level (0.0-1.0).
    prior_tempo_bpm:
        Current tempo in BPM.
    policy_id:
        Policy version identifier.
    score_trend:
        Optional trend value from recent sessions (positive = improving).

    Returns
    -------
    ProgressionDecision with difficulty_delta, tempo_delta, buckets, rationale, and coach_hint.
    """
    band = _score_to_band(score)

    # Look up base adjustments from tables
    difficulty_delta = DIFFICULTY_DELTAS[band]
    tempo_delta = TEMPO_DELTAS[band]
    density_bucket: Density = DENSITY_BY_BAND[band]  # type: ignore
    sync_bucket: Sync = SYNC_BY_BAND[band]  # type: ignore

    rationale = f"Score {score:.1f} → band '{band}'"

    decision = ProgressionDecision(
        difficulty_delta=difficulty_delta,
        tempo_delta_bpm=tempo_delta,
        density_bucket=density_bucket,
        syncopation_bucket=sync_bucket,
        rationale=rationale,
        policy_version=policy_id,
    )

    # Apply trend adjustments
    decision = _apply_trend_adjustments(decision, score_trend)

    # Build coach hint (Episode 11)
    decision.coach_hint = build_coach_hint(
        score=score,
        score_trend=score_trend,
        decision=decision,
    )

    return decision
