"""
Evidence window probe for runtime telemetry.

Stub implementation: captures minimal snapshot for groove-layer intent generator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class EvidenceWindow:
    """
    Minimal runtime evidence window passed to groove-layer intent generator.
    Extend later with timing stats, recent note onsets, tempo drift metrics, etc.
    """
    horizon_ms: int = 2000
    # Optional fields to support future analyzer upgrades
    features: Dict[str, Any] = field(default_factory=dict)


class EvidenceWindowProbe:
    """
    Stub probe. In later ships, attach this to realtime telemetry buffers.

    Usage:
        probe = EvidenceWindowProbe()
        window = probe.snapshot(horizon_ms=2000)
    """

    def snapshot(self, *, horizon_ms: int) -> EvidenceWindow | None:
        """
        Capture a snapshot of the current evidence window.

        Returns None (fail closed) if snapshot cannot be captured.
        """
        try:
            return EvidenceWindow(horizon_ms=int(horizon_ms), features={})
        except Exception:
            return None
