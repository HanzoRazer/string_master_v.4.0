"""
Tests for assignment serializer (UUID-safe JSON export).
"""
from __future__ import annotations

import json
from uuid import uuid4

from sg_coach.schemas import (
    SessionRecord,
    SessionTiming,
    PerformanceSummary,
    TimingErrorStats,
    SessionEvents,
    ProgramRef,
    ProgramType,
)
from sg_coach.coach_policy import evaluate_session
from sg_coach.assignment_policy import plan_assignment
from sg_coach.assignment_serializer import serialize_bundle, deserialize_bundle


def _make_session() -> SessionRecord:
    """Create a valid SessionRecord for testing."""
    return SessionRecord(
        session_id=uuid4(),
        instrument_id="test-guitar-001",
        engine_version="zt-band@0.2.0",
        program_ref=ProgramRef(
            type=ProgramType.ztprog,
            name="golden_vector_program",
        ),
        timing=SessionTiming(
            bpm=120.0,
            grid=16,
        ),
        duration_s=300,
        performance=PerformanceSummary(
            bars_played=8,
            notes_expected=100,
            notes_played=98,
            notes_dropped=2,
            timing_error_ms=TimingErrorStats(mean=12.0, std=8.0, max=38.0),
            error_by_step={"0": 5.0, "4": -8.0, "8": 15.0, "12": -3.0},
        ),
        events=SessionEvents(late_drops=1, panic_triggered=False),
    )


def test_assignment_serializer_uuid_safe():
    """Serialized assignment should have string UUIDs, not UUID objects."""
    session = _make_session()
    ev = evaluate_session(session)
    assignment = plan_assignment(ev, session.program_ref)

    data = serialize_bundle(assignment)

    # Must be JSON serializable
    dumped = json.dumps(data)
    assert "payload" in data
    payload = data["payload"]
    assert "assignment_id" in payload
    assert payload["session_id"] == str(session.session_id)
    assert isinstance(payload["assignment_id"], str)


def test_assignment_to_json_roundtrip():
    """serialize_bundle/deserialize_bundle should round-trip."""
    session = _make_session()
    ev = evaluate_session(session)
    assignment = plan_assignment(ev, session.program_ref)

    data = serialize_bundle(assignment)
    recovered = deserialize_bundle(data)

    assert recovered.assignment_id == assignment.assignment_id
    assert recovered.session_id == assignment.session_id
    assert recovered.program.name == assignment.program.name
    assert recovered.constraints.tempo_start == assignment.constraints.tempo_start
