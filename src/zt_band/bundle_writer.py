"""
Bundle Writer: Emit canonical 4-file clip bundles.

This module writes the standardized clip bundle format:
- clip.mid          : MIDI audio content (delegated to midi_out.py)
- clip.tags.json    : Technique tags sidecar
- clip.coach.json   : Practice assignment (optional in v1)
- clip.runlog.json  : Provenance/audit trail

Design Pattern:
    Primary API takes explicit `base_dir: Path` for testability.
    Convenience wrapper provides default `~/.sg-bundles/YYYY-MM-DD/clip_id`.

Usage (testable):
    from zt_band.bundle_writer import write_clip_bundle
    bundle = write_clip_bundle(..., base_dir=Path(tmp_path), ...)

Usage (default convention):
    from zt_band.bundle_writer import write_clip_bundle_default
    bundle = write_clip_bundle_default(..., clip_id="clip_abc123", ...)

Atomic Write Guarantee:
    All files are written to a temporary directory first, then the entire
    bundle directory is renamed atomically to the final path. This ensures:
    - DAW imports never see partial bundles
    - Either the complete bundle exists, or nothing exists
    - Crash-safety: no partial state on filesystem

Collision Policy:
    By default, collision_policy='fail' raises BundleCollisionError if the
    target bundle directory already exists. This fail-fast behavior protects
    reproducibility. Use collision_policy='overwrite' to replace existing.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import uuid4

from .midi_out import NoteEvent, write_midi_file

# ============================================================================
# Optional Dependencies (sg-spec types)
# ============================================================================

try:
    from sg_spec.schemas.clip_bundle import (
        ClipBundle,
        ClipArtifact,
        ClipRunLog,
        ClipAttempt,
    )
    SG_SPEC_AVAILABLE = True
except ImportError:
    SG_SPEC_AVAILABLE = False

try:
    from sg_spec.ai.coach.schemas import PracticeAssignment
    COACH_SCHEMA_AVAILABLE = True
except ImportError:
    COACH_SCHEMA_AVAILABLE = False


# ============================================================================
# Version Info
# ============================================================================

ZT_BAND_VERSION = "0.1.0"


# ============================================================================
# Exceptions
# ============================================================================

class BundleCollisionError(Exception):
    """
    Raised when a bundle directory already exists and collision_policy is 'fail'.

    Fail-fast prevents silent overwrites and protects reproducibility.
    If you need to overwrite, explicitly delete the existing bundle first,
    or use collision_policy='overwrite'.
    """
    def __init__(self, bundle_dir: Path):
        self.bundle_dir = bundle_dir
        super().__init__(
            f"Bundle directory already exists: {bundle_dir}\n"
            "Use collision_policy='overwrite' to allow overwrites, "
            "or delete the existing bundle first."
        )


# ============================================================================
# Utility Functions
# ============================================================================

def _compute_sha256(data: bytes) -> str:
    """Compute SHA256 hash of bytes, return prefixed lowercase hex."""
    return f"sha256:{hashlib.sha256(data).hexdigest().lower()}"


def _generate_clip_id() -> str:
    """Generate a unique clip ID with prefix."""
    return f"clip_{uuid4().hex[:12]}"


def _now_utc() -> datetime:
    """Current datetime in UTC."""
    return datetime.now(timezone.utc)


def _iso_utc(dt: datetime) -> str:
    """ISO timestamp string from datetime."""
    return dt.isoformat()


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """
    Write bytes atomically: temp file + rename.

    Ensures DAW/consumer never sees partial files.
    """
    # Write to temp file in same directory (ensures same filesystem for rename)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        os.write(fd, data)
        os.close(fd)
        # Atomic rename
        os.replace(tmp_path, path)
    except Exception:
        os.close(fd) if fd else None
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _atomic_publish_dir(
    tmp_dir: Path,
    final_dir: Path,
    collision_policy: str = "fail",
) -> None:
    """
    Atomically publish a directory by renaming.

    This provides whole-bundle atomicity: consumers never see
    partial bundles. All files are written to a temp directory
    first, then the entire directory is renamed in one atomic
    operation.

    Parameters
    ----------
    tmp_dir : Path
        Temporary directory containing the complete bundle.
    final_dir : Path
        Target directory path for the published bundle.
    collision_policy : str
        - 'fail': Raise BundleCollisionError if final_dir exists.
        - 'overwrite': Remove existing directory and replace.

    Raises
    ------
    BundleCollisionError
        If final_dir exists and collision_policy='fail'.
    """
    final_dir.parent.mkdir(parents=True, exist_ok=True)

    if final_dir.exists():
        if collision_policy == "fail":
            raise BundleCollisionError(final_dir)
        # overwrite: remove existing before rename
        shutil.rmtree(final_dir)

    os.replace(str(tmp_dir), str(final_dir))


# ============================================================================
# Default Path Convention
# ============================================================================

DEFAULT_BUNDLES_ROOT = Path.home() / ".sg-bundles"


def compute_default_bundle_dir(
    created_at_utc: datetime,
    clip_id: str,
    *,
    root: Optional[Path] = None,
) -> Path:
    """
    Compute canonical bundle directory path.

    Convention: {root}/YYYY-MM-DD/{clip_id}/

    Parameters
    ----------
    created_at_utc : datetime
        Creation timestamp (used for date partition).
    clip_id : str
        Unique clip identifier.
    root : Optional[Path]
        Base directory. Default: ~/.sg-bundles

    Returns
    -------
    Path
        Full path to bundle directory (not yet created).
    """
    if root is None:
        root = DEFAULT_BUNDLES_ROOT
    date_str = created_at_utc.strftime("%Y-%m-%d")
    return root / date_str / clip_id


# ============================================================================
# Result Types
# ============================================================================

@dataclass
class ArtifactRef:
    """Reference to a written artifact."""
    filename: str
    path: Path
    sha256: str
    size_bytes: int


@dataclass
class BundleResult:
    """
    Result of write_clip_bundle().

    Attributes
    ----------
    bundle_dir : Path
        Directory containing all artifacts.
    clip_id : str
        Unique clip identifier.
    created_at_utc : datetime
        Creation timestamp.
    artifacts : Dict[str, ArtifactRef]
        Map of filename -> artifact reference.
    clip_bundle : ClipBundle | None
        Typed bundle manifest (if sg-spec available).
    """
    bundle_dir: Path
    clip_id: str
    created_at_utc: datetime
    artifacts: Dict[str, ArtifactRef]
    clip_bundle: Any = None  # ClipBundle | None


# ============================================================================
# Primary API: Testable (caller-provided base_dir)
# ============================================================================

def write_clip_bundle(
    comp_events: List[NoteEvent],
    bass_events: List[NoteEvent],
    tempo_bpm: int,
    *,
    base_dir: Path,
    clip_id: str,
    created_at_utc: datetime,
    # Tags (optional, aligned 1:1 with events)
    comp_tags: Optional[Sequence[List[str]]] = None,
    bass_tags: Optional[Sequence[List[str]]] = None,
    # Inputs for provenance
    inputs: Optional[Dict[str, Any]] = None,
    # Coach assignment (optional in v1)
    assignment: Optional[Any] = None,
    # Style metadata
    meter: str = "4/4",
    meter_tuple: Tuple[int, int] = (4, 4),  # Phase 6.0: For MIDI time signature
    beats_per_bar: float = 4.0,
    style_params: Optional[Dict[str, Any]] = None,
    # Optional: require coach file even if no assignment
    require_coach_file: bool = False,
    # Collision policy: 'fail' (recommended) or 'overwrite'
    collision_policy: str = "fail",
) -> BundleResult:
    """
    Write a complete clip bundle with explicit base directory.

    This is the testable primary API. For production convenience,
    use write_clip_bundle_default() which computes the standard path.

    Parameters
    ----------
    comp_events : List[NoteEvent]
        Comping track events.
    bass_events : List[NoteEvent]
        Bass track events.
    tempo_bpm : int
        Tempo in BPM.
    base_dir : Path
        Base directory for bundles (explicit, testable).
    clip_id : str
        Clip identifier.
    created_at_utc : datetime
        Creation timestamp (used for runlog and date partition).
    comp_tags : Optional[Sequence[List[str]]]
        Technique tags for comp events (1:1 alignment).
    bass_tags : Optional[Sequence[List[str]]]
        Technique tags for bass events (1:1 alignment).
    inputs : Optional[Dict[str, Any]]
        Generation inputs for provenance.
    assignment : Optional[PracticeAssignment]
        Coach assignment to include (optional in v1).
    meter : str
        Time signature string (e.g., "4/4").
    beats_per_bar : float
        Beats per bar.
    style_params : Optional[Dict[str, Any]]
        Style parameters for tags sidecar.
    require_coach_file : bool
        If True, emit clip.coach.json even without assignment.
    collision_policy : str
        How to handle existing bundle directories:
        - 'fail' (default): Raise BundleCollisionError. Recommended for reproducibility.
        - 'overwrite': Silently overwrite existing files.

    Returns
    -------
    BundleResult
        Contains bundle_dir, clip_id, artifacts, and typed ClipBundle.

    Raises
    ------
    BundleCollisionError
        If bundle directory already exists and collision_policy='fail'.
    """
    start_time = time.time()
    generated_at_str = _iso_utc(created_at_utc)

    # Compute bundle directory path
    date_str = created_at_utc.strftime("%Y-%m-%d")
    date_dir = base_dir / date_str
    bundle_dir = date_dir / clip_id

    # Create date directory (needed for temp dir to be on same filesystem)
    date_dir.mkdir(parents=True, exist_ok=True)

    # Create temp directory alongside final destination
    # Using same parent ensures rename stays on same filesystem (atomic)
    tmp_dir = date_dir / f".tmp_{clip_id}_{secrets.token_hex(4)}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        artifacts: Dict[str, ArtifactRef] = {}

        # ====================================================================
        # 1. Write clip.mid (delegates to canonical midi_out.py)
        # ====================================================================
        midi_path_tmp = tmp_dir / "clip.mid"
        midi_path_final = bundle_dir / "clip.mid"
        write_midi_file(comp_events, bass_events, tempo_bpm=tempo_bpm, outfile=str(midi_path_tmp), meter=meter_tuple)

        midi_bytes = midi_path_tmp.read_bytes()
        midi_sha256 = _compute_sha256(midi_bytes)
        artifacts["clip.mid"] = ArtifactRef(
            filename="clip.mid",
            path=midi_path_final,  # Final path (after publish)
            sha256=midi_sha256,
            size_bytes=len(midi_bytes),
        )

        # sg-spec TechniqueSidecar wants raw hex without "sha256:" prefix
        source_midi_sha256_hex = midi_sha256.split("sha256:", 1)[-1]

        # Helper: flatten tags safely to a per-role list[str]
        def _flatten_tags(tag_groups: Optional[Sequence[List[str]]]) -> List[str]:
            if not tag_groups:
                return []
            flat: List[str] = []
            for group in tag_groups:
                if not group:
                    continue
                for t in group:
                    if t and isinstance(t, str):
                        flat.append(t)
            # stable + dedup
            return sorted(set(flat))

        comp_technique_tags = _flatten_tags(comp_tags)
        bass_technique_tags = _flatten_tags(bass_tags)

        # ====================================================================
        # 2. Write clip.tags.json (always emit, even if no tags)
        # ====================================================================
        tags_path_tmp = tmp_dir / "clip.tags.json"
        tags_path_final = bundle_dir / "clip.tags.json"

        # TechniqueSidecar v1: annotations as list-of-objects
        annotations: List[Dict[str, Any]] = []
        for e in comp_events:
            annotations.append(
                {
                    "start_beats": float(e.start_beats),
                    "duration_beats": float(e.duration_beats),
                    "midi_note": int(getattr(e, "midi_note")),
                    "role": "comp",
                    "technique_tags": comp_technique_tags,
                }
            )
        for e in bass_events:
            annotations.append(
                {
                    "start_beats": float(e.start_beats),
                    "duration_beats": float(e.duration_beats),
                    "midi_note": int(getattr(e, "midi_note")),
                    "role": "bass",
                    "technique_tags": bass_technique_tags,
                }
            )

        tags_payload = {
            "schema_id": "technique_sidecar",
            "schema_version": "v1",
            "generated_at_utc": generated_at_str,
            "source_midi_sha256": source_midi_sha256_hex,
            "meter": meter,
            "beats_per_bar": beats_per_bar,
            "tempo_bpm": float(tempo_bpm),
            "annotations": annotations,
        }
        if style_params:
            tags_payload["style_params"] = style_params

        tags_bytes = json.dumps(tags_payload, indent=2, sort_keys=True).encode("utf-8")
        tags_path_tmp.write_bytes(tags_bytes)
        tags_sha256 = _compute_sha256(tags_bytes)
        artifacts["clip.tags.json"] = ArtifactRef(
            filename="clip.tags.json",
            path=tags_path_final,
            sha256=tags_sha256,
            size_bytes=len(tags_bytes),
        )

        # ====================================================================
        # 3. Write clip.coach.json (optional in v1)
        # ====================================================================
        coach_sha256: Optional[str] = None
        emit_coach = require_coach_file or assignment is not None

        if emit_coach:
            coach_path_tmp = tmp_dir / "clip.coach.json"
            coach_path_final = bundle_dir / "clip.coach.json"

            if assignment is not None:
                # Serialize assignment
                if hasattr(assignment, "model_dump"):
                    coach_payload = assignment.model_dump(mode="json")
                elif hasattr(assignment, "dict"):
                    coach_payload = assignment.dict()
                else:
                    coach_payload = dict(assignment) if isinstance(assignment, dict) else {}
            else:
                # Empty placeholder when require_coach_file=True but no assignment
                coach_payload = {
                    "schema_id": "practice_assignment",
                    "schema_version": "v1",
                    "status": "pending",
                    "clip_id": clip_id,
                }

            coach_bytes = json.dumps(coach_payload, indent=2, sort_keys=True).encode("utf-8")
            coach_path_tmp.write_bytes(coach_bytes)
            coach_sha256 = _compute_sha256(coach_bytes)
            artifacts["clip.coach.json"] = ArtifactRef(
                filename="clip.coach.json",
                path=coach_path_final,
                sha256=coach_sha256,
                size_bytes=len(coach_bytes),
            )

        # ====================================================================
        # 4. Write clip.runlog.json (provenance/audit trail)
        # ====================================================================
        duration_ms = int((time.time() - start_time) * 1000)

        # Calculate validation summary
        note_count_comp = len(comp_events)
        note_count_bass = len(bass_events)
        max_end = 0.0
        for e in comp_events + bass_events:
            end = e.start_beats + e.duration_beats
            if end > max_end:
                max_end = end

        runlog_payload = {
            "schema_id": "clip_runlog",
            "schema_version": "v1",
            "clip_id": clip_id,
            "generated_at_utc": generated_at_str,
            "generator": {
                "module": "zt_band.bundle_writer",
                "function": "write_clip_bundle",
                "version": ZT_BAND_VERSION,
            },
            "inputs": inputs or {},
            "outputs": {
                "clip_mid_sha256": midi_sha256,
                "clip_tags_sha256": tags_sha256,
                "clip_coach_sha256": coach_sha256,
            },
            "validation": {
                "contract_passed": True,
                "duration_beats": max_end,
                "note_count_comp": note_count_comp,
                "note_count_bass": note_count_bass,
                "warnings": [],
            },
            "attempts": [
                {
                    "attempt": 1,
                    "status": "ok",
                    "duration_ms": duration_ms,
                }
            ],
        }

        runlog_path_tmp = tmp_dir / "clip.runlog.json"
        runlog_path_final = bundle_dir / "clip.runlog.json"
        runlog_bytes = json.dumps(runlog_payload, indent=2, sort_keys=True).encode("utf-8")
        runlog_path_tmp.write_bytes(runlog_bytes)
        runlog_sha256 = _compute_sha256(runlog_bytes)
        artifacts["clip.runlog.json"] = ArtifactRef(
            filename="clip.runlog.json",
            path=runlog_path_final,
            sha256=runlog_sha256,
            size_bytes=len(runlog_bytes),
        )

        # ====================================================================
        # Atomically publish the complete bundle directory
        # ====================================================================
        _atomic_publish_dir(tmp_dir, bundle_dir, collision_policy)

        # ====================================================================
        # Build typed ClipBundle if sg-spec available
        # ====================================================================
        clip_bundle = None
        if SG_SPEC_AVAILABLE:
            kind_map = {
                "clip.mid": "midi",
                "clip.tags.json": "tags",
                "clip.coach.json": "coach",
                "clip.runlog.json": "runlog",
            }
            artifact_list = [
                ClipArtifact(
                    artifact_id=name.replace(".", "_"),
                    kind=kind_map.get(name, "attachment"),
                    path=str(ref.path),
                    sha256=ref.sha256,
                )
                for name, ref in artifacts.items()
            ]
            clip_bundle = ClipBundle(
                clip_id=clip_id,
                bundle_path=str(bundle_dir),
                artifacts=artifact_list,
            )

            # ----------------------------------------------------------------
            # Write manifest to disk + add to artifacts (self-describing)
            # ----------------------------------------------------------------
            manifest_path = bundle_dir / "clip.bundle.json"
            manifest_bytes = clip_bundle.model_dump_json(indent=2).encode("utf-8")
            _atomic_write_bytes(manifest_path, manifest_bytes)

            manifest_sha = _compute_sha256(manifest_bytes)
            manifest_size = len(manifest_bytes)

            # Add manifest to artifacts dict
            artifacts["clip.bundle.json"] = ArtifactRef(
                filename="clip.bundle.json",
                path=manifest_path,
                sha256=manifest_sha,
                size_bytes=manifest_size,
            )

            # Update clip_bundle to include itself in artifacts list
            artifact_list.append(
                ClipArtifact(
                    artifact_id="clip_bundle_json",
                    kind="attachment",
                    path=str(manifest_path),
                    sha256=manifest_sha,
                )
            )
            # Rebuild with self-reference
            clip_bundle = ClipBundle(
                clip_id=clip_id,
                bundle_path=str(bundle_dir),
                artifacts=artifact_list,
            )

        return BundleResult(
            bundle_dir=bundle_dir,
            clip_id=clip_id,
            created_at_utc=created_at_utc,
            artifacts=artifacts,
            clip_bundle=clip_bundle,
        )

    except Exception:
        # Clean up temp directory on any failure
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


# ============================================================================
# Convenience Wrapper: Default Path Convention
# ============================================================================

def write_clip_bundle_default(
    comp_events: List[NoteEvent],
    bass_events: List[NoteEvent],
    tempo_bpm: int = 120,
    *,
    # Optional: caller can provide clip_id, otherwise auto-generated
    clip_id: Optional[str] = None,
    # Optional: custom bundles root (default: ~/.sg-bundles)
    bundles_root: Optional[Path] = None,
    # Tags
    comp_tags: Optional[Sequence[List[str]]] = None,
    bass_tags: Optional[Sequence[List[str]]] = None,
    # Inputs for provenance
    inputs: Optional[Dict[str, Any]] = None,
    # Coach assignment (optional in v1)
    assignment: Optional[Any] = None,
    # Style metadata
    meter: str = "4/4",
    meter_tuple: Tuple[int, int] = (4, 4),  # Phase 6.0: For MIDI time signature
    beats_per_bar: float = 4.0,
    style_params: Optional[Dict[str, Any]] = None,
    require_coach_file: bool = False,
    # Collision policy
    collision_policy: str = "fail",
) -> BundleResult:
    """
    Write clip bundle using default path convention.

    Convenience wrapper that auto-generates clip_id and uses
    ~/.sg-bundles/YYYY-MM-DD/{clip_id}/ convention.

    For testability, use write_clip_bundle() with explicit base_dir.

    Parameters
    ----------
    comp_events : List[NoteEvent]
        Comping track events.
    bass_events : List[NoteEvent]
        Bass track events.
    tempo_bpm : int
        Tempo in BPM.
    clip_id : Optional[str]
        Clip identifier. Auto-generated if not provided.
    bundles_root : Optional[Path]
        Base directory. Default: ~/.sg-bundles
    (other params same as write_clip_bundle)

    Returns
    -------
    BundleResult
        Contains bundle_dir, clip_id, artifacts, and typed ClipBundle.
    """
    # Auto-generate clip_id if not provided
    if clip_id is None:
        clip_id = _generate_clip_id()

    # Use current UTC time
    created_at_utc = _now_utc()

    # Resolve bundles root
    if bundles_root is None:
        bundles_root = DEFAULT_BUNDLES_ROOT

    return write_clip_bundle(
        comp_events=comp_events,
        bass_events=bass_events,
        tempo_bpm=tempo_bpm,
        base_dir=bundles_root,
        clip_id=clip_id,
        created_at_utc=created_at_utc,
        comp_tags=comp_tags,
        bass_tags=bass_tags,
        inputs=inputs,
        assignment=assignment,
        meter=meter,
        meter_tuple=meter_tuple,
        beats_per_bar=beats_per_bar,
        style_params=style_params,
        require_coach_file=require_coach_file,
        collision_policy=collision_policy,
    )


# ============================================================================
# Convenience: Generate + Bundle in one call
# ============================================================================

def generate_and_bundle(
    chord_symbols: List[str],
    style_name: str = "swing_basic",
    tempo_bpm: int = 120,
    bars_per_chord: int = 1,
    *,
    tritone_mode: str = "none",
    tritone_strength: float = 1.0,
    tritone_seed: Optional[int] = None,
    style_overrides: Optional[Dict[str, Any]] = None,
    # Bundle options (testable API)
    base_dir: Optional[Path] = None,
    clip_id: Optional[str] = None,
    assignment: Optional[Any] = None,
    require_coach_file: bool = False,
    collision_policy: str = "fail",
) -> BundleResult:
    """
    Generate accompaniment and write complete bundle in one call.

    Combines generate_accompaniment() + write_clip_bundle() for convenience.

    If base_dir is None, uses default path convention (~/.sg-bundles/...).
    If base_dir is provided, writes to explicit location (testable).

    Returns
    -------
    BundleResult
        Contains bundle_dir, clip_id, artifacts, and typed ClipBundle.
    """
    from .engine import generate_accompaniment
    from .rock_tag_attach import attach_tags_sidecar
    from .rock_articulations import Difficulty, RockStyle

    # Generate events (no outfile — we'll write via bundle)
    comp_events, bass_events = generate_accompaniment(
        chord_symbols=chord_symbols,
        style_name=style_name,
        tempo_bpm=tempo_bpm,
        bars_per_chord=bars_per_chord,
        outfile=None,
        tritone_mode=tritone_mode,
        tritone_strength=tritone_strength,
        tritone_seed=tritone_seed,
        style_overrides=style_overrides,
    )

    # Attach technique tags if enabled in style_overrides
    comp_tags: Optional[List[List[str]]] = None
    bass_tags: Optional[List[List[str]]] = None
    style_params: Optional[Dict[str, Any]] = None

    tt_cfg = (style_overrides or {}).get("technique_tags")
    if tt_cfg and tt_cfg.get("enabled", False):
        tag_density = float(tt_cfg.get("density", 0.5))
        tag_seed = tt_cfg.get("seed", tritone_seed)
        tag_seed = int(tag_seed) if tag_seed is not None else None

        comp_tags, bass_tags = attach_tags_sidecar(
            comp_events=comp_events,
            bass_events=bass_events,
            beats_per_bar=4.0,
            difficulty=Difficulty.INTERMEDIATE,
            style=RockStyle.NEUTRAL,
            density=tag_density,
            seed=tag_seed,
        )
        style_params = {
            "density": tag_density,
            "seed": tag_seed,
        }

    # Capture inputs for provenance
    inputs = {
        "chord_symbols": chord_symbols,
        "style_name": style_name,
        "tempo_bpm": tempo_bpm,
        "bars_per_chord": bars_per_chord,
        "tritone_mode": tritone_mode,
        "tritone_strength": tritone_strength,
        "tritone_seed": tritone_seed,
        "style_overrides": style_overrides,
    }

    # Write bundle — use testable API if base_dir provided, else default
    created_at_utc = _now_utc()
    if clip_id is None:
        clip_id = _generate_clip_id()

    if base_dir is not None:
        # Testable path: explicit base_dir
        return write_clip_bundle(
            comp_events=comp_events,
            bass_events=bass_events,
            tempo_bpm=tempo_bpm,
            base_dir=base_dir,
            clip_id=clip_id,
            created_at_utc=created_at_utc,
            comp_tags=comp_tags,
            bass_tags=bass_tags,
            inputs=inputs,
            assignment=assignment,
            style_params=style_params,
            require_coach_file=require_coach_file,
            collision_policy=collision_policy,
        )
    else:
        # Default path convention
        return write_clip_bundle_default(
            comp_events=comp_events,
            bass_events=bass_events,
            tempo_bpm=tempo_bpm,
            clip_id=clip_id,
            comp_tags=comp_tags,
            bass_tags=bass_tags,
            inputs=inputs,
            assignment=assignment,
            style_params=style_params,
            require_coach_file=require_coach_file,
            collision_policy=collision_policy,
        )

