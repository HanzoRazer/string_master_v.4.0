"""
Device-local GrooveProfileV1 JSON store.

Profiles are stored as JSON files named: <profile_id>.json
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class GrooveProfileStore:
    """
    Minimal device-local profile store.
    Profiles are stored as JSON files named: <profile_id>.json
    """
    root_dir: Path

    def load_profile(self, profile_id: str) -> Dict[str, Any] | None:
        """
        Load a GrooveProfileV1 JSON by profile_id.

        Returns None (fail closed) if:
        - File doesn't exist
        - JSON parse fails
        - schema_id != "groove_profile"
        - schema_version != "v1"
        - profile_id in file doesn't match requested profile_id
        """
        try:
            p = self.root_dir / f"{profile_id}.json"
            if not p.exists():
                return None
            data = json.loads(p.read_text(encoding="utf-8"))
            # Minimal sanity checks: shape of GrooveProfileV1-like contract
            if not isinstance(data, dict):
                return None
            if data.get("schema_id") != "groove_profile":
                return None
            if data.get("schema_version") != "v1":
                return None
            if data.get("profile_id") != profile_id:
                # allow mismatch to fail closed; avoids accidentally using wrong file
                return None
            return data
        except Exception:
            return None
