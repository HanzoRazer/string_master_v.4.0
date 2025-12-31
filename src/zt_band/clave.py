"""
Clave grid definitions and quantization utilities.

Provides son clave patterns (2-3 / 3-2) and step-based timing grid
for real-time scheduling and practice mode.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

ClaveType = Literal["son_2_3", "son_3_2"]
Grid = Literal[8, 16]  # steps per bar


@dataclass(frozen=True)
class ClaveGrid:
    bpm: float
    grid: Grid = 16           # 16 = sixteenth grid; 8 = eighth grid
    bars_per_cycle: int = 2   # son clave is a 2-bar pattern
    clave: ClaveType = "son_2_3"

    def seconds_per_beat(self) -> float:
        return 60.0 / max(1e-9, self.bpm)

    def seconds_per_bar(self) -> float:
        # 4/4
        return 4.0 * self.seconds_per_beat()

    def seconds_per_step(self) -> float:
        return self.seconds_per_bar() / float(self.grid)

    def steps_per_cycle(self) -> int:
        return self.grid * self.bars_per_cycle


def _son_clave_steps_16(clave: ClaveType) -> List[int]:
    """
    Son clave in 16th-note steps across 2 bars (32 steps).
    Common indexing (0..31):
      2-3: hits at 0, 6, 10, 16, 22, 26
      3-2: hits at 0, 6, 10, 16, 22
    We keep it deterministic and editable later.
    """
    if clave == "son_2_3":
        return [0, 6, 10, 16, 22, 26]
    return [0, 6, 10, 16, 22]


def _son_clave_steps_8(clave: ClaveType) -> List[int]:
    """
    Son clave approximated on 8th grid across 2 bars (16 steps).
    Derived by integer-dividing 16th indices by 2 and de-duplicating.
    """
    s16 = _son_clave_steps_16(clave)
    out = []
    for x in [i // 2 for i in s16]:
        if x not in out:
            out.append(x)
    return out


def clave_hit_steps(grid: Grid, clave: ClaveType) -> List[int]:
    if grid == 16:
        return _son_clave_steps_16(clave)
    return _son_clave_steps_8(clave)


def quantize_step(step: float, *, grid_steps: int, mode: Literal["nearest", "down", "up"]) -> int:
    """
    Quantize fractional step index to an integer step.
    """
    if mode == "nearest":
        return int(round(step)) % grid_steps
    if mode == "down":
        return int(step // 1) % grid_steps
    # up
    return int(-(-step // 1)) % grid_steps  # ceil for positives


def is_allowed_on_clave(step_i: int, *, allowed: List[int], strict: bool) -> bool:
    """
    strict=True means only clave hit steps are allowed.
    strict=False means any grid step is allowed (but we can still align click/groove).
    """
    if not strict:
        return True
    return step_i in set(allowed)
