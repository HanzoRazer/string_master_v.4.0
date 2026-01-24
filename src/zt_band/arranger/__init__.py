# zt_band/arranger/__init__.py
"""
Arranger subsystem: pattern selection + performance controls.

Driven by ArrangerControlPlan (from adapters layer).
"""
from zt_band.arranger.selection_request import PatternSelectionRequest
from zt_band.arranger.arranger_engine_adapter import to_selection_request
from zt_band.arranger.performance_controls import PerformanceControls, derive_controls
from zt_band.arranger.engine import choose_pattern

__all__ = [
    "PatternSelectionRequest",
    "to_selection_request",
    "PerformanceControls",
    "derive_controls",
    "choose_pattern",
]
