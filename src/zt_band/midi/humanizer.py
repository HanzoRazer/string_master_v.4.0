# zt_band/midi/humanizer.py
"""
Deterministic Humanizer: seedable jitter generator for MIDI timing.

Same seed + tick_index + channel => same jitter every run.
Hash-based (not PRNG) for cross-platform stability.

Two modes:
    "white": Independent per tick (most deterministic, most "random")
    "smooth": Value-noise interpolation for musical continuity
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


def _u01_from_bytes(b: bytes) -> float:
    """
    Convert bytes to a deterministic uniform [0,1).
    Use 64 bits for stable float mapping across platforms.
    """
    x = int.from_bytes(b[:8], "big", signed=False)
    return (x & ((1 << 64) - 1)) / float(1 << 64)


def _det_u01(*parts: str) -> float:
    """
    Deterministic U(0,1) from hashed parts.
    """
    h = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    return _u01_from_bytes(h)


@dataclass(frozen=True)
class DeterministicHumanizer:
    """
    Seedable deterministic jitter generator.

    Args:
        seed: Stable identifier (e.g., profile_id or intent_id)
        mode: "smooth" for musical continuity, "white" for independent per tick
        smooth_period: Ticks per interpolation segment (only in smooth mode)

    Usage:
        humanizer = DeterministicHumanizer(seed="gp_abc123")
        jitter = humanizer.jitter_ms(tick_index=42, humanize_ms=7.5, channel="note")
        # Apply jitter to scheduled event timing
    """
    seed: str
    mode: str = "smooth"  # "smooth" or "white"
    smooth_period: int = 16  # ticks per interpolation segment (only in smooth mode)

    def jitter_ms(
        self,
        *,
        tick_index: int,
        humanize_ms: float,
        channel: str = "default",
    ) -> float:
        """
        Compute deterministic jitter in milliseconds.

        Args:
            tick_index: Monotonic counter (event index or clock tick bucket)
            humanize_ms: Amplitude bound (0 = no jitter, >0 = ±humanize_ms)
            channel: Lane partition for independent jitter streams ("note", "cc", etc.)

        Returns:
            Jitter in ms, bounded to [-humanize_ms, +humanize_ms]
        """
        if humanize_ms <= 0:
            return 0.0

        amp = float(humanize_ms)

        if self.mode == "white":
            u = _det_u01(self.seed, channel, str(tick_index))
            # map [0,1) -> [-1,1)
            return (2.0 * u - 1.0) * amp

        # smooth mode: value noise between two deterministic anchor samples
        p = max(1, int(self.smooth_period))
        t0 = (tick_index // p) * p
        t1 = t0 + p
        frac = (tick_index - t0) / float(p)

        u0 = _det_u01(self.seed, channel, str(t0))
        u1 = _det_u01(self.seed, channel, str(t1))

        # Smoothstep interpolation (C1 continuous)
        s = frac * frac * (3.0 - 2.0 * frac)
        u = (1.0 - s) * u0 + s * u1

        return (2.0 * u - 1.0) * amp
