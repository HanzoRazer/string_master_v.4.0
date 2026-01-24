# zt_band/adapters/default_map.py
"""
MIDI CC assignment map for Groove Control Intent parameters.

Deliberately conservative and easy to change. Choose CCs that won't
collide with your synth/DAW mappings.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MidiControlMap:
    """
    Defines which CCs express which intent parameters.
    Choose CCs that won't collide with your synth/DAW mappings.

    Defaults:
      - Tightness -> CC20
      - Humanization -> CC21
      - Assist gain -> CC22
      - Expression window -> CC23
      - Drift correction mode -> CC24
      - Recovery enable -> CC25
    """
    channel: int = 0  # 0-15

    cc_tightness: int = 20
    cc_humanize: int = 21
    cc_assist_gain: int = 22
    cc_expression_window: int = 23
    cc_drift_correction: int = 24
    cc_recovery_enable: int = 25

    # Optional future:
    cc_syncopation: Optional[int] = None
    cc_density: Optional[int] = None

    def status_cc(self) -> int:
        return 0xB0 | (self.channel & 0x0F)


DEFAULT_MAP = MidiControlMap()
