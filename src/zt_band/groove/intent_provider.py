"""
Intent provider interface and context for runtime intent generation.

This module defines the contract for intent providers, allowing runtime
to swap between manual controls and analyzer-generated intent without
touching arranger, scheduler, or playlist logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class IntentContext:
    """
    Minimal runtime context available when generating intent.
    Extend as needed (bar index, recent timing stats, etc.) without breaking callers.
    """
    profile_id: str
    bpm: float
    program_name: str | None = None
    item_idx: int | None = None


class IntentProvider(Protocol):
    """
    Contract: return a GrooveControlIntentV1-shaped dict (or None).
    Never raise. Provider should fail closed (return None) if it cannot produce intent.
    """
    def get_intent(self, ctx: IntentContext) -> Dict[str, Any] | None: ...
