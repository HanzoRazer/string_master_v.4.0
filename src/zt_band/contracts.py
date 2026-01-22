"""
MIDI Runtime Contract Version Pin

Bump this ONLY when deterministic behavior or runtime invariants change:
- ordering rules
- quantization semantics
- telemetry semantics (bar CC meaning/defaults)
- realtime lateness/panic policy defaults
"""

MIDI_CONTRACT_VERSION: str = "v1"
