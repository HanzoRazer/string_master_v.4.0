from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .config import load_program_config, ProgramConfig


@dataclass
class ProgramDescriptor:
    """
    Describes a discovered .ztprog file.

    - path:   filesystem path to the config
    - config: parsed ProgramConfig, or None if parsing failed
    - error:  error message if parsing failed, otherwise None
    """
    path: Path
    config: Optional[ProgramConfig]
    error: Optional[str] = None


def discover_programs(root: str | Path = "programs") -> List[ProgramDescriptor]:
    """
    Discover .ztprog files under the given directory (non-recursive).

    Returns a list of ProgramDescriptor entries. If the directory does not
    exist or is empty, an empty list is returned.
    """
    base = Path(root)
    if not base.exists() or not base.is_dir():
        return []

    descriptors: List[ProgramDescriptor] = []
    for file in sorted(base.glob("*.ztprog")):
        try:
            cfg = load_program_config(file)
            descriptors.append(
                ProgramDescriptor(path=file, config=cfg, error=None)
            )
        except Exception as exc:  # noqa: BLE001
            descriptors.append(
                ProgramDescriptor(path=file, config=None, error=str(exc))
            )
    return descriptors
