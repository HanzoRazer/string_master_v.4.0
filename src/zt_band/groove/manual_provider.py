"""
Manual intent provider: wraps CLI/preset/UI controls.

Produces intent from user controls without requiring a Groove Layer analyzer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from zt_band.groove.intent_provider import IntentContext, IntentProvider
from zt_band.ui.manual_intent import ManualBandControls, build_groove_intent_from_controls


@dataclass(frozen=True)
class ManualIntentProvider:
    """
    Produces intent from user controls (CLI/preset/UI).
    
    Implements IntentProvider protocol.
    """
    controls: ManualBandControls
    profile_id: str = "rt_playlist_manual"

    def get_intent(self, ctx: IntentContext) -> Dict[str, Any] | None:
        try:
            return build_groove_intent_from_controls(
                controls=self.controls,
                profile_id=self.profile_id,
                target_bpm=float(ctx.bpm),
            )
        except Exception:
            return None
