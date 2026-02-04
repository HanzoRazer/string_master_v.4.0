"""
Tests for Coach Hint (Episode 11)

Validates that progression policy generates meaningful coach hints.
"""
from __future__ import annotations

import pytest

from sg_agentd.services.progression_policy import apply_progression_policy


def test_coach_hint_present_and_nonempty():
    """Coach hint should be present and non-empty for any valid decision."""
    d = apply_progression_policy(
        score=72.0,
        prior_difficulty=0.5,
        prior_tempo_bpm=120,
        policy_id="v1_default",
        score_trend=0.0,
    )
    assert isinstance(d.coach_hint, str)
    assert len(d.coach_hint.strip()) > 0


def test_coach_hint_reflects_trend_up():
    """Coach hint should mention improvement when trend is positive."""
    d = apply_progression_policy(
        score=72.0,
        prior_difficulty=0.5,
        prior_tempo_bpm=120,
        policy_id="v1_default",
        score_trend=10.0,
    )
    # Should contain "improvement" or "improving"
    assert "improv" in d.coach_hint.lower()


def test_coach_hint_mentions_changes():
    """Coach hint should mention tempo, density, and sync changes."""
    d = apply_progression_policy(
        score=90.0,
        prior_difficulty=0.5,
        prior_tempo_bpm=120,
        policy_id="v1_default",
        score_trend=None,
    )
    text = d.coach_hint.lower()
    assert "tempo" in text
    assert "density" in text
    assert "sync" in text


def test_coach_hint_reset_band():
    """Coach hint for reset band should emphasize fundamentals."""
    d = apply_progression_policy(
        score=30.0,
        prior_difficulty=0.5,
        prior_tempo_bpm=120,
        policy_id="v1_default",
        score_trend=None,
    )
    text = d.coach_hint.lower()
    assert "fundamental" in text or "simple" in text


def test_coach_hint_recover_band():
    """Coach hint for recover band should be supportive."""
    d = apply_progression_policy(
        score=45.0,
        prior_difficulty=0.5,
        prior_tempo_bpm=120,
        policy_id="v1_default",
        score_trend=None,
    )
    text = d.coach_hint.lower()
    assert "rebuild" in text or "reduce" in text or "steady" in text


def test_coach_hint_trend_down_warning():
    """Coach hint should warn when trend is negative."""
    d = apply_progression_policy(
        score=72.0,
        prior_difficulty=0.5,
        prior_tempo_bpm=120,
        policy_id="v1_default",
        score_trend=-5.0,
    )
    text = d.coach_hint.lower()
    # Should mention slipping, accuracy, or similar
    assert "slip" in text or "accuracy" in text or "prioritize" in text
