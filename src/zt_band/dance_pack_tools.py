"""Dance Pack authoring tools - validate + build canonical .dpack.json

This module provides safety rails for authoring Dance Packs:
- Load YAML or JSON source files
- Validate against the strict Pydantic DancePackV1 model (enums enforced)
- Write canonical JSON (.dpack.json) with stable formatting (cross-platform diffs)
- Support directory recursion for batch builds

Usage:
    zt-band dance-pack-validate D_forms/
    zt-band dance-pack-build-json D_forms/
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from .dance_pack import DancePackV1, DancePackLoadError


@dataclass(frozen=True)
class BuildResult:
    """Result of building a .dpack.json file."""
    source: Path
    output: Path
    ok: bool
    error: str | None = None


def _load_text(path: Path) -> str:
    """Read file contents as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def load_pack_any(path: Path) -> dict:
    """Load a pack from YAML or JSON file.

    Args:
        path: Path to .yaml, .yml, or .json file

    Returns:
        Parsed dict

    Raises:
        ValueError: If file extension is unsupported or content is not a dict
    """
    text = _load_text(path)
    suffix = path.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Unsupported pack extension: {path.suffix}")

    if not isinstance(data, dict):
        raise ValueError("Pack must deserialize to a JSON/YAML object at the root.")

    return data


def validate_pack(path: Path) -> DancePackV1:
    """Load and validate a pack against the strict schema.

    Args:
        path: Path to pack file (YAML or JSON)

    Returns:
        Validated DancePackV1 instance

    Raises:
        DancePackLoadError: If validation fails
    """
    try:
        raw = load_pack_any(path)
        return DancePackV1.model_validate(raw)
    except Exception as e:
        raise DancePackLoadError(f"Validation failed for {path}: {e}") from e


def dump_canonical_json(pack: DancePackV1) -> str:
    """Serialize pack to canonical JSON (stable, cross-platform, deterministic).

    Args:
        pack: Validated DancePackV1 instance

    Returns:
        JSON string with consistent formatting
    """
    obj = pack.model_dump(mode="json", by_alias=True, exclude_none=True)
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def build_dpack_json(source: Path, out_path: Path | None = None) -> BuildResult:
    """Validate pack and emit canonical .dpack.json.

    Args:
        source: Path to source pack file (YAML or JSON)
        out_path: Optional output path. If None, uses same directory with .dpack.json extension.

    Returns:
        BuildResult with success/failure info
    """
    try:
        pack = validate_pack(source)

        if out_path is None:
            # Default: same directory, same stem, .dpack.json
            stem = source.stem
            if stem.endswith(".dpack"):
                stem = stem[:-6]  # Remove .dpack if present
            out_path = source.parent / f"{stem}.dpack.json"

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(dump_canonical_json(pack), encoding="utf-8")

        return BuildResult(source=source, output=out_path, ok=True)
    except Exception as e:
        return BuildResult(
            source=source,
            output=out_path or source,
            ok=False,
            error=str(e)
        )


def iter_pack_sources(root: Path, include_built: bool = False) -> Iterable[Path]:
    """Iterate over pack source files in a directory (recursive).

    Yields YAML and JSON files. By default excludes already-built .dpack.json files.

    Args:
        root: File or directory to scan
        include_built: If True, also yield .dpack.json files (for validation)

    Yields:
        Paths to pack source files
    """
    if root.is_file():
        yield root
        return

    for p in sorted(root.rglob("*")):
        if p.is_file():
            suffix = p.suffix.lower()
            # Include YAML and JSON
            if suffix in {".yaml", ".yml"}:
                yield p
            elif suffix == ".json":
                # Exclude .dpack.json unless include_built is True
                if include_built or not p.name.endswith(".dpack.json"):
                    yield p
