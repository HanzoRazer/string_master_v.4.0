from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VelocityAssistSender:
    """
    Wraps an existing sender and scales note_on velocities deterministically.

    - Does nothing for messages without type/velocity
    - Does nothing for non-note messages
    - Never raises (best-effort)
    """
    sender: Any
    velocity_mul: float = 1.0

    def send(self, msg: Any) -> None:
        try:
            mtype = getattr(msg, "type", None)
            if mtype != "note_on":
                self.sender.send(msg)
                return

            vel = getattr(msg, "velocity", None)
            if vel is None:
                self.sender.send(msg)
                return

            new_vel = int(round(float(vel) * float(self.velocity_mul)))
            if new_vel < 1:
                new_vel = 1
            if new_vel > 127:
                new_vel = 127

            # Preserve original message object if possible (avoid mutating shared refs)
            if hasattr(msg, "copy"):
                m2 = msg.copy(velocity=new_vel)
                self.sender.send(m2)
            else:
                # Fallback: mutate if we can't copy (best effort)
                try:
                    setattr(msg, "velocity", new_vel)
                except Exception:
                    pass
                self.sender.send(msg)
        except Exception:
            # Never break playback
            self.sender.send(msg)
