"""
realtime_telemetry.py -- Bar boundary CC emission for UI/DAW mapping.

Pure helper functions for generating telemetry MIDI messages.
Keeps telemetry logic testable without realtime dependencies.
"""

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    mido = None  # type: ignore
    MIDO_AVAILABLE = False


def _clamp_cc_value(v: int) -> int:
    """Clamp value to valid MIDI CC range 0-127."""
    return 0 if v < 0 else 127 if v > 127 else int(v)


def make_bar_cc_messages(
    channel: int,
    cc_countdown: int,
    cc_index: int,
    bars_remaining: int,
    bar_index: int,
):
    """
    Create MIDI CC messages for bar boundary telemetry.

    Args:
        channel: MIDI channel (0-15)
        cc_countdown: CC number for bars-remaining countdown
        cc_index: CC number for bar index count-up
        bars_remaining: Bars left in current item (countdown)
        bar_index: Current bar number (count-up, 1-based)

    Returns:
        List of two mido.Message objects (countdown CC, index CC)
    """
    if not MIDO_AVAILABLE:
        return []

    return [
        mido.Message(
            "control_change",
            channel=int(channel) % 16,
            control=int(cc_countdown) % 128,
            value=_clamp_cc_value(bars_remaining),
        ),
        mido.Message(
            "control_change",
            channel=int(channel) % 16,
            control=int(cc_index) % 128,
            value=_clamp_cc_value(bar_index),
        ),
    ]
