"""
Validators for sg_agentd generation attempts.

Each validator inspects generated output and returns a result indicating
whether the output passes the constraint. Results include structured
violation/warning information for debugging and logging.
"""
from __future__ import annotations

from sg_agentd.validators.range import (
    RangeResult,
    validate_pitch_range,
    extract_range_limit,
)

__all__ = [
    "RangeResult",
    "validate_pitch_range",
    "extract_range_limit",
]
