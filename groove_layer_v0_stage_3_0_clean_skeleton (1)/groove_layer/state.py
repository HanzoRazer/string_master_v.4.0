from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List

@dataclass
class FastWindowStateV0:
    stable_windows: int = 0
    unstable_windows: int = 0

    next_probe_in_windows: int = 0
    probe_cooldown_windows: int = 0
    probe_last_score: float = 0.0
    probe_last_outcome: str = "none"  # none|success|fail
    probe_history: List[dict] = field(default_factory=list)

    last_target_bpm: float = 0.0
    drift_accum_pct: float = 0.0

    last_loop_policy: str = "none"  # none|micro_loop|free_play|coach_loop

@dataclass
class SlowTraitsV0:
    preferred_density: str = "medium"  # sparse|medium|dense
    preferred_feel: str = "straight"   # straight|swing|shuffle
    tempo_follow_bias: float = 0.0     # -1..+1

@dataclass
class GrooveStateV0:
    fast: FastWindowStateV0 = field(default_factory=FastWindowStateV0)
    slow: SlowTraitsV0 = field(default_factory=SlowTraitsV0)

    @staticmethod
    def from_prior_hint(prior: Optional[Dict[str, Any]]) -> "GrooveStateV0":
        st = GrooveStateV0()
        if not prior:
            return st
        fast = prior.get("fast", prior)
        slow = prior.get("slow", prior)
        for k, v in fast.items():
            if hasattr(st.fast, k):
                setattr(st.fast, k, v)
        for k, v in slow.items():
            if hasattr(st.slow, k):
                setattr(st.slow, k, v)
        return st

    def to_hint(self) -> Dict[str, Any]:
        return {"fast": self.fast.__dict__, "slow": self.slow.__dict__}
