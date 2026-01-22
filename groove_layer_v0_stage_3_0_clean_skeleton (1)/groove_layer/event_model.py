from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

EventType = Literal["note_onset", "strum_onset", "percussive_onset"]

@dataclass(frozen=True)
class GrooveEventV0:
    """Minimal event shape (v0)."""
    t_onset_ms: int
    event_type: EventType
    strength: float  # 0..1
    confidence: float  # 0..1

    @staticmethod
    def from_dict(d: dict) -> "GrooveEventV0":
        return GrooveEventV0(
            t_onset_ms=int(d["t_onset_ms"]),
            event_type=d["event_type"],
            strength=float(d.get("strength", 0.0)),
            confidence=float(d.get("confidence", 0.0)),
        )
