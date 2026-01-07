"""
MIDI sender backends for realtime output.

Provides a unified interface for sending MIDI messages,
abstracting over mido (default) and python-rtmidi (low-latency).

Usage:
    sender = create_sender(backend="mido", port_name="My MIDI Port")
    sender.send(mido.Message("note_on", note=60, velocity=64))
    sender.close()
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False

# NOTE: rtmidi import is deferred to RtMidiSender.__init__()
# because python-rtmidi crashes on Python 3.14 during import.
# We only import it when actually requested.
RTMIDI_AVAILABLE: bool | None = None  # lazy-checked


def _check_rtmidi() -> bool:
    """Lazily check if rtmidi is available (avoids crash on import)."""
    global RTMIDI_AVAILABLE
    if RTMIDI_AVAILABLE is None:
        try:
            import rtmidi  # noqa: F401
            RTMIDI_AVAILABLE = True
        except Exception:
            RTMIDI_AVAILABLE = False
    return RTMIDI_AVAILABLE


if TYPE_CHECKING:
    import mido


class MidiSender(Protocol):
    """Protocol for MIDI output backends."""

    def send(self, msg: "mido.Message") -> None:
        """Send a MIDI message."""
        ...

    def close(self) -> None:
        """Close the output port."""
        ...


class MidoSender:
    """MIDI sender using mido (default backend)."""

    def __init__(self, port_name: str) -> None:
        if not MIDO_AVAILABLE:
            raise RuntimeError("mido is not installed")
        self._port = mido.open_output(port_name)

    def send(self, msg: "mido.Message") -> None:
        self._port.send(msg)

    def close(self) -> None:
        self._port.close()


class RtMidiSender:
    """
    MIDI sender using python-rtmidi (lower latency on Linux/Pi).

    Converts mido.Message to raw MIDI bytes for rtmidi.
    """

    def __init__(self, port_name: str) -> None:
        if not _check_rtmidi():
            raise RuntimeError("python-rtmidi is not installed (pip install python-rtmidi)")
        if not MIDO_AVAILABLE:
            raise RuntimeError("mido is required for message conversion")

        import rtmidi
        self._midi_out = rtmidi.MidiOut()
        ports = self._midi_out.get_ports()

        # Find port by name (partial match)
        port_index = None
        for i, name in enumerate(ports):
            if port_name in name or name in port_name:
                port_index = i
                break

        if port_index is None:
            available = ", ".join(ports) if ports else "(none)"
            raise RuntimeError(f"MIDI port '{port_name}' not found. Available: {available}")

        self._midi_out.open_port(port_index)

    def send(self, msg: "mido.Message") -> None:
        # Convert mido Message to raw MIDI bytes
        self._midi_out.send_message(msg.bytes())

    def close(self) -> None:
        self._midi_out.close_port()
        del self._midi_out


class DummySender:
    """No-op sender for testing (collects messages)."""

    def __init__(self) -> None:
        self.sent: list["mido.Message"] = []

    def send(self, msg: "mido.Message") -> None:
        self.sent.append(msg)

    def close(self) -> None:
        pass


def create_sender(backend: str = "mido", port_name: str | None = None) -> MidiSender:
    """
    Factory for MIDI sender backends.

    Args:
        backend: "mido" (default), "rtmidi", or "dummy" (for tests)
        port_name: MIDI output port name (required for mido/rtmidi)

    Returns:
        A MidiSender-compatible object with .send() and .close()
    """
    if backend == "dummy":
        return DummySender()

    if port_name is None:
        raise ValueError("port_name is required for mido/rtmidi backends")

    if backend == "mido":
        return MidoSender(port_name)
    elif backend == "rtmidi":
        return RtMidiSender(port_name)
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'mido', 'rtmidi', or 'dummy'.")
