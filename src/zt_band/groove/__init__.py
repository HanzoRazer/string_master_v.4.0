"""
Groove module: Intent providers for runtime intent generation.

Provides a pluggable abstraction for intent sources:
- ManualIntentProvider: Uses CLI/preset controls
- AnalyzerIntentProvider: Scaffolded Groove Layer integration (H.1)

Supporting modules:
- GrooveProfileStore: Device-local JSON profile store
- EvidenceWindowProbe: Runtime telemetry snapshot (stub)
- generate_intent: Groove layer bridge function
"""
from .intent_provider import IntentContext, IntentProvider
from .manual_provider import ManualIntentProvider
from .analyzer_provider import AnalyzerIntentProvider
from .profile_store import GrooveProfileStore
from .window_probe import EvidenceWindow, EvidenceWindowProbe
from .groove_layer_bridge import generate_intent, GrooveLayer

__all__ = [
    "IntentContext",
    "IntentProvider",
    "ManualIntentProvider",
    "AnalyzerIntentProvider",
    "GrooveProfileStore",
    "EvidenceWindow",
    "EvidenceWindowProbe",
    "generate_intent",
    "GrooveLayer",
]
