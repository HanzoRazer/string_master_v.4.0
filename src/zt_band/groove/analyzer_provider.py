"""
H.1: Scaffolded analyzer intent provider.

Loads GrooveProfileV1 from device-local store, captures evidence window,
calls groove-layer generate_intent(), and returns None if any step fails.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from zt_band.groove.intent_provider import IntentContext, IntentProvider
from zt_band.groove.profile_store import GrooveProfileStore
from zt_band.groove.window_probe import EvidenceWindowProbe
from zt_band.groove.groove_layer_bridge import generate_intent


@dataclass(frozen=True)
class AnalyzerIntentProvider:
    """
    H.1: Scaffolded analyzer provider.

    - Loads GrooveProfileV1 from device-local store
    - Captures a small EvidenceWindow snapshot
    - Calls groove-layer generate_intent(profile, window, now)
    - Returns None if any step is unavailable

    Implements IntentProvider protocol.
    """
    profile_store_dir: Path
    probe: EvidenceWindowProbe = field(default_factory=EvidenceWindowProbe)
    default_horizon_ms: int = 2000
    service_timeout_s: float | None = None

    def get_intent(self, ctx: IntentContext) -> Dict[str, Any] | None:
        """
        Generate intent from profile + evidence window.

        Returns None (fail closed) if:
        - Profile cannot be loaded
        - Evidence window cannot be captured
        - generate_intent() returns None or invalid shape
        - Any exception occurs
        """
        try:
            store = GrooveProfileStore(root_dir=self.profile_store_dir)
            profile = store.load_profile(ctx.profile_id)
            if not profile:
                return None

            window = self.probe.snapshot(horizon_ms=self.default_horizon_ms)
            if window is None:
                return None

            now = datetime.now(timezone.utc)
            intent = generate_intent(
                profile=profile,
                window=window,
                now_utc=now,
                timeout_s=self.service_timeout_s,
            )
            if not intent or not isinstance(intent, dict):
                return None

            # Minimal contract sanity: GrooveControlIntentV1-like shape
            if intent.get("schema_id") != "groove_control_intent":
                return None
            if intent.get("schema_version") != "v1":
                return None
            if intent.get("profile_id") != ctx.profile_id:
                return None

            return intent
        except Exception:
            return None
