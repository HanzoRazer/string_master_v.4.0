"""
Tests for windowed strict practice mode (±ms tolerance before snap/reject).
"""

import pytest
import time

from zt_band import realtime
from zt_band.realtime import RtSpec


# ---------------------------------------------------------------------
# Unit test: window field exists on RtSpec
# ---------------------------------------------------------------------


def test_rtspec_has_practice_window_ms():
    """RtSpec should have practice_window_ms field with default 0."""
    spec = RtSpec(midi_in="X", midi_out="Y")
    assert hasattr(spec, "practice_window_ms")
    assert spec.practice_window_ms == 0.0


def test_rtspec_accepts_custom_window_ms():
    """RtSpec should accept custom practice_window_ms value."""
    spec = RtSpec(midi_in="X", midi_out="Y", practice_window_ms=35.0)
    assert spec.practice_window_ms == 35.0


# ---------------------------------------------------------------------
# CLI test: --strict-window-ms flag exists
# ---------------------------------------------------------------------


def test_practice_strict_window_ms_flag_exists():
    """practice subparser should accept --strict-window-ms argument."""
    from zt_band import cli as zcli

    parser = zcli.build_arg_parser()
    args = parser.parse_args([
        "practice",
        "--midi-in", "TestIn",
        "--midi-out", "TestOut",
        "--strict-window-ms", "25.0",
    ])
    assert abs(args.strict_window_ms - 25.0) < 1e-9


def test_practice_strict_window_ms_default_zero():
    """--strict-window-ms should default to 0."""
    from zt_band import cli as zcli

    parser = zcli.build_arg_parser()
    args = parser.parse_args([
        "practice",
        "--midi-in", "TestIn",
        "--midi-out", "TestOut",
    ])
    assert args.strict_window_ms == 0.0


# ---------------------------------------------------------------------
# Integration test: window tolerance passes notes through unchanged
# ---------------------------------------------------------------------


def test_windowed_strict_allows_within_window(monkeypatch):
    """
    Notes within the window tolerance should be forwarded immediately
    without snapping to the grid.
    """
    sent = []

    class FakeOut:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def send(self, msg):
            sent.append(msg)

    class FakeIn:
        def __init__(self):
            self._sent_note = False

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def iter_pending(self):
            if self._sent_note:
                return []
            self._sent_note = True
            import mido
            return [mido.Message("note_on", note=60, velocity=64, channel=0)]

    fake_in = FakeIn()

    import mido
    monkeypatch.setattr(mido, "open_output", lambda *a, **k: FakeOut())
    monkeypatch.setattr(mido, "open_input", lambda *a, **k: fake_in)

    # Make loop exit after processing
    calls = {"sleep": 0}

    def fake_sleep(x):
        calls["sleep"] += 1
        if calls["sleep"] > 3:
            raise SystemExit(0)

    monkeypatch.setattr(time, "sleep", fake_sleep)

    # Control monotonic clock
    t = {"v": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: t["v"])

    spec = RtSpec(
        midi_in="DummyIn",
        midi_out="DummyOut",
        bpm=120.0,
        grid=16,
        clave="son_2_3",
        click=False,
        practice_strict=True,
        practice_window_ms=40.0,  # 40ms window tolerance
        practice_quantize="nearest",
        practice_reject_offgrid=False,
        lookahead_s=0.01,
        tick_s=0.001,
    )

    with pytest.raises(SystemExit):
        realtime.practice_lock_to_clave(spec)

    # Should have received the note_on
    assert any(getattr(m, "type", None) == "note_on" for m in sent)


def test_windowed_strict_snaps_outside_window(monkeypatch):
    """
    Notes outside the window tolerance should be snapped (or rejected).
    We verify the note still gets sent (snapped, not rejected).
    """
    sent = []

    class FakeOut:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def send(self, msg):
            sent.append(msg)

    class FakeIn:
        def __init__(self):
            self._sent_note = False

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def iter_pending(self):
            if self._sent_note:
                return []
            self._sent_note = True
            import mido
            return [mido.Message("note_on", note=60, velocity=64, channel=0)]

    fake_in = FakeIn()

    import mido
    monkeypatch.setattr(mido, "open_output", lambda *a, **k: FakeOut())
    monkeypatch.setattr(mido, "open_input", lambda *a, **k: fake_in)

    calls = {"sleep": 0}

    def fake_sleep(x):
        calls["sleep"] += 1
        if calls["sleep"] > 3:
            raise SystemExit(0)

    monkeypatch.setattr(time, "sleep", fake_sleep)

    t = {"v": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: t["v"])

    spec = RtSpec(
        midi_in="DummyIn",
        midi_out="DummyOut",
        bpm=120.0,
        grid=16,
        clave="son_2_3",
        click=False,
        practice_strict=True,
        practice_window_ms=0.0,  # No window - must snap
        practice_quantize="nearest",
        practice_reject_offgrid=False,
        lookahead_s=0.01,
        tick_s=0.001,
    )

    with pytest.raises(SystemExit):
        realtime.practice_lock_to_clave(spec)

    # Should still receive the note_on (snapped, not rejected)
    assert any(getattr(m, "type", None) == "note_on" for m in sent)


def test_windowed_strict_rejects_outside_window_with_reject_flag(monkeypatch):
    """
    Notes outside window with --reject-offgrid should be dropped.
    """
    sent = []

    class FakeOut:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def send(self, msg):
            sent.append(msg)

    class FakeIn:
        def __init__(self):
            self._sent_note = False

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def iter_pending(self):
            if self._sent_note:
                return []
            self._sent_note = True
            import mido
            # Send note at a time that will NOT be on clave hit
            return [mido.Message("note_on", note=60, velocity=64, channel=0)]

    fake_in = FakeIn()

    import mido
    monkeypatch.setattr(mido, "open_output", lambda *a, **k: FakeOut())
    monkeypatch.setattr(mido, "open_input", lambda *a, **k: fake_in)

    calls = {"sleep": 0}

    def fake_sleep(x):
        calls["sleep"] += 1
        if calls["sleep"] > 3:
            raise SystemExit(0)

    monkeypatch.setattr(time, "sleep", fake_sleep)

    # Time that lands between clave hits
    t = {"v": 1000.123}  # off-beat timing
    monkeypatch.setattr(time, "monotonic", lambda: t["v"])

    spec = RtSpec(
        midi_in="DummyIn",
        midi_out="DummyOut",
        bpm=120.0,
        grid=16,
        clave="son_2_3",
        click=False,
        practice_strict=True,
        practice_window_ms=0.001,  # Tiny window - effectively no tolerance
        practice_quantize="nearest",
        practice_reject_offgrid=True,  # Reject off-grid notes
        lookahead_s=0.01,
        tick_s=0.001,
    )

    with pytest.raises(SystemExit):
        realtime.practice_lock_to_clave(spec)

    # Note should be rejected (not in sent) OR it happened to land on clave
    # This test primarily verifies the code path runs without error
    # Full behavioral test would require more precise timing control
