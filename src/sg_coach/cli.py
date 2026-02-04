"""
Smart Guitar Coach CLI.

Commands:
- sgc export-bundle: Build firmware envelope from evaluation + assignment
- sgc ota-pack: Build OTA payload with HMAC signature
- sgc ota-verify: Verify HMAC-signed OTA payload
- sgc ota-bundle: Build OTA folder/zip bundle (from SessionRecord or Pack Set)
- sgc ota-verify-zip: Verify bundle.zip integrity
- sgc dance-pack-list: List bundled dance packs
- sgc dance-pack-set-list: List bundled dance pack sets
- sgc dance-pack-set-validate: Validate pack set references
- sgc dance-pack-set-show: Show pack set summary

Migrated from sg-spec to string_master for proper architectural boundaries.
Schemas and dance pack YAML files remain in sg-spec; this CLI contains
the business logic commands.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from uuid import uuid4, uuid5, NAMESPACE_DNS

# Schemas from sg-spec (correct dependency direction)
from sg_spec.ai.coach.schemas import (
    AssignmentConstraints,
    AssignmentFocus,
    CoachPrompt,
    PracticeAssignment,
    ProgramRef,
    ProgramType,
    SessionRecord,
    SuccessCriteria,
)

# Business logic from local sg_coach modules
from .evaluation import evaluate_session
from .assignment import plan_assignment
from .serializer import serialize_bundle
from .ota import (
    build_ota_payload,
    verify_ota_payload,
    build_assignment_ota_bundle,
    verify_bundle_integrity,
    verify_zip_bundle,
)

# Dance Pack imports (loaders stay in sg-spec, but binding logic here)
from sg_spec.ai.coach.dance_pack import (
    load_pack_by_id,
    load_pack_from_file,
    list_pack_ids,
    DancePackV1,
)
from sg_spec.ai.coach.dance_pack_set import (
    DancePackSetV1,
    load_set_by_id,
    load_set_from_file,
    list_all_sets,
    validate_set_references,
)


def _read_text(path: str | Path) -> str:
    """Read text from a file, raising FileNotFoundError if missing."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return p.read_text(encoding="utf-8")


def _read_json(path: str | Path) -> dict:
    """Read JSON from a file."""
    return json.loads(_read_text(path))


def _find_bundle_root(extract_dir: Path) -> Path:
    """
    Find the directory containing manifest.json.

    Supports:
      - zip with files at root
      - zip with a single top-level folder
    """
    if (extract_dir / "manifest.json").exists():
        return extract_dir

    matches = list(extract_dir.rglob("manifest.json"))
    if not matches:
        raise ValueError("manifest.json not found in zip")
    if len(matches) > 1:
        raise ValueError("multiple manifest.json found in zip (ambiguous)")
    return matches[0].parent


# ============================================================================
# Dance Pack Binding (business logic moved from sg-spec)
# ============================================================================


class AssignmentDefaults:
    """Conservative Mode-1 defaults derived from a Dance Pack."""

    def __init__(
        self,
        tempo_start_bpm: float,
        tempo_target_bpm: float,
        tempo_ceiling_bpm: float,
        bars_per_loop: int,
        strict_window_ms: float,
        ghost_vel_max: int,
        swing_ratio: float,
        subdivision: str,
        difficulty: str,
    ):
        self.tempo_start_bpm = tempo_start_bpm
        self.tempo_target_bpm = tempo_target_bpm
        self.tempo_ceiling_bpm = tempo_ceiling_bpm
        self.bars_per_loop = bars_per_loop
        self.strict_window_ms = strict_window_ms
        self.ghost_vel_max = ghost_vel_max
        self.swing_ratio = swing_ratio
        self.subdivision = subdivision
        self.difficulty = difficulty


def pack_to_assignment_defaults(pack: DancePackV1) -> AssignmentDefaults:
    """
    Derive conservative Coach Mode 1 assignment defaults from a Dance Pack.

    This binds groove constraints to practice parameters without authoring music.
    """
    tempo_min, tempo_max = pack.groove.tempo_range_bpm

    # Conservative defaults: start at lower tempo, target at comfortable middle
    tempo_start = tempo_min
    tempo_target = (tempo_min + tempo_max) / 2
    tempo_ceiling = tempo_max

    # Strict window based on subdivision
    if pack.groove.subdivision == "ternary":
        strict_window_ms = 50.0
    elif pack.groove.subdivision == "compound":
        strict_window_ms = 45.0
    else:  # binary
        strict_window_ms = 35.0

    return AssignmentDefaults(
        tempo_start_bpm=tempo_start,
        tempo_target_bpm=tempo_target,
        tempo_ceiling_bpm=tempo_ceiling,
        bars_per_loop=min(pack.groove.cycle_bars, 16),
        strict_window_ms=strict_window_ms,
        ghost_vel_max=pack.performance_profile.velocity_range.ghost_max,
        swing_ratio=pack.groove.swing_ratio,
        subdivision=pack.groove.subdivision,
        difficulty=pack.practice_mapping.difficulty_rating,
    )


def _plan_assignment_from_pack_defaults(
    pack_id: str,
    defaults: AssignmentDefaults,
    pack: DancePackV1,
) -> PracticeAssignment:
    """
    Create a PracticeAssignment directly from pack defaults.

    Used in pack-set mode where we don't have a session/evaluation.
    Creates deterministic IDs based on pack_id for reproducibility.
    """
    # Deterministic IDs from pack_id
    session_id = uuid5(NAMESPACE_DNS, f"pack-default-session:{pack_id}")
    assignment_id = uuid5(NAMESPACE_DNS, f"pack-default-assignment:{pack_id}")

    # Build constraints from pack defaults
    constraints = AssignmentConstraints(
        tempo_start=int(defaults.tempo_start_bpm),
        tempo_target=int(defaults.tempo_target_bpm),
        tempo_step=5,
        strict=True,
        strict_window_ms=defaults.strict_window_ms,
        bars_per_loop=defaults.bars_per_loop,
        repetitions=8,
    )

    # Use pack's primary focus
    primary_focus = "groove"
    if pack.practice_mapping.primary_focus:
        primary_focus = pack.practice_mapping.primary_focus[0]

    focus = AssignmentFocus(
        primary=primary_focus,
        secondary=None,
    )

    # Default success criteria
    success = SuccessCriteria(
        max_mean_error_ms=30.0,
        max_late_drops=3,
    )

    # Coach prompt for pack-based assignment
    prompt = CoachPrompt(
        mode="optional",
        message=f"Practice {pack.metadata.display_name} at comfortable tempo.",
    )

    # Create program ref for this pack
    program = ProgramRef(
        type=ProgramType.ztprog,
        name=pack_id,
    )

    return PracticeAssignment(
        assignment_id=assignment_id,
        session_id=session_id,
        program=program,
        constraints=constraints,
        focus=focus,
        success_criteria=success,
        coach_prompt=prompt,
        expires_after_sessions=5,
    )


# ============================================================================
# Commands: Export Bundle (JSON envelope)
# ============================================================================


def cmd_export_bundle(args: argparse.Namespace) -> int:
    """
    Build firmware envelope from session -> evaluation -> assignment.
    Outputs JSON to stdout or file.
    """
    session_json = _read_text(args.session)
    session = SessionRecord.model_validate_json(session_json)

    ev = evaluate_session(session)

    # Build program ref (use session's program if available)
    program = session.program_ref

    assignment = plan_assignment(ev, program)
    bundle = serialize_bundle(assignment)

    output = json.dumps(bundle, indent=2, sort_keys=True)

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"Written to {args.output}")
    else:
        print(output)

    return 0


# ============================================================================
# Commands: OTA Pack (HMAC signed JSON)
# ============================================================================


def cmd_ota_pack(args: argparse.Namespace) -> int:
    """
    Build HMAC-signed OTA payload from session.
    """
    session_json = _read_text(args.session)
    session = SessionRecord.model_validate_json(session_json)

    ev = evaluate_session(session)
    program = session.program_ref
    assignment = plan_assignment(ev, program)

    # Read secret if provided
    secret = None
    if args.secret:
        secret = args.secret.encode("utf-8")
    elif args.secret_file:
        secret = Path(args.secret_file).read_bytes().strip()

    payload = build_ota_payload(assignment, secret=secret)

    output = json.dumps(payload, indent=2, sort_keys=True)

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"Written to {args.output}")
    else:
        print(output)

    return 0


def cmd_ota_verify_hmac(args: argparse.Namespace) -> int:
    """
    Verify HMAC signature of OTA payload.
    """
    payload_json = _read_text(args.payload)
    payload = json.loads(payload_json)

    # Read secret
    if args.secret:
        secret = args.secret.encode("utf-8")
    elif args.secret_file:
        secret = Path(args.secret_file).read_bytes().strip()
    else:
        print("ERROR: --secret or --secret-file required", file=sys.stderr)
        return 1

    if verify_ota_payload(payload, secret=secret):
        print("OK: signature valid")
        return 0
    else:
        print("FAIL: signature invalid or missing")
        return 1


# ============================================================================
# Commands: OTA Bundle (folder/zip)
# ============================================================================


def cmd_ota_bundle(args: argparse.Namespace) -> int:
    """
    Build OTA bundle(s) from SessionRecord or single Dance Pack.

    Session mode: SessionRecord -> CoachEvaluation -> PracticeAssignment -> OTA bundle
    Single-pack mode: Dance Pack -> assignment defaults -> OTA bundle
    """
    started = time.time()
    make_zip = bool(args.zip)

    # HMAC secret if provided
    hmac_secret = None
    if args.secret:
        hmac_secret = args.secret.encode("utf-8")
    elif args.secret_file:
        hmac_secret = Path(args.secret_file).read_bytes().strip()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest) if args.manifest else out_dir / "ota_manifest.json"

    # Single-pack mode
    dance_pack_id = getattr(args, "dance_pack", None)
    dance_pack_path = getattr(args, "dance_pack_path", None)

    if dance_pack_id or dance_pack_path:
        if dance_pack_path:
            pack = load_pack_from_file(dance_pack_path)
            pack_id = pack.metadata.id
        else:
            pack = load_pack_by_id(dance_pack_id)
            pack_id = dance_pack_id

        # Get assignment defaults for this pack
        defaults = pack_to_assignment_defaults(pack)

        # Create assignment from pack defaults
        assignment = _plan_assignment_from_pack_defaults(pack_id, defaults, pack)

        # Build bundle
        bundle_name = args.name or f"ota_bundle__{pack_id}"

        res = build_assignment_ota_bundle(
            assignment=assignment,
            out_dir=str(out_dir),
            bundle_name=bundle_name,
            product=args.product,
            target_device_model=args.device_model,
            target_min_firmware=args.min_firmware,
            attachments=None,
            make_zip=make_zip,
            hmac_secret=hmac_secret,
        )

        # Write manifest
        manifest = {
            "schema_id": "ota_bundle_manifest",
            "schema_version": "v1",
            "mode": "single-pack",
            "generated_at_unix": int(started),
            "elapsed_s": round(time.time() - started, 3),
            "pack": {
                "pack_id": pack_id,
                "display_name": pack.metadata.display_name,
                "difficulty": pack.practice_mapping.difficulty_rating,
            },
            "outputs": [
                {
                    "dance_pack_id": pack_id,
                    "bundle_dir": str(res.bundle_dir),
                    "zip_path": str(res.zip_path) if res.zip_path else None,
                }
            ],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

        print(str(res.bundle_dir))
        if res.zip_path is not None:
            print(str(res.zip_path))
        print(f"Manifest: {manifest_path}")

        return 0

    # Session mode (original behavior)
    if not args.session:
        print("ERROR: --session required (or use --dance-pack)", file=sys.stderr)
        return 1

    session_json = _read_text(args.session)
    session = SessionRecord.model_validate_json(session_json)

    ev = evaluate_session(session)
    program = session.program_ref
    assignment = plan_assignment(ev, program)

    res = build_assignment_ota_bundle(
        assignment=assignment,
        out_dir=str(out_dir),
        bundle_name=args.name,
        product=args.product,
        target_device_model=args.device_model,
        target_min_firmware=args.min_firmware,
        attachments=None,
        make_zip=make_zip,
        hmac_secret=hmac_secret,
    )

    # Write manifest for single-session mode
    manifest = {
        "schema_id": "ota_bundle_manifest",
        "schema_version": "v1",
        "mode": "single-session",
        "generated_at_unix": int(started),
        "elapsed_s": round(time.time() - started, 3),
        "set": None,
        "outputs": [
            {
                "bundle_dir": str(res.bundle_dir),
                "zip_path": str(res.zip_path) if res.zip_path else None,
            }
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(str(res.bundle_dir))
    if res.zip_path is not None:
        print(str(res.zip_path))
    print(f"Manifest: {manifest_path}")

    return 0


def cmd_ota_verify_folder(args: argparse.Namespace) -> int:
    """
    Verify an OTA bundle directory (folder form).
    """
    bundle_dir = Path(args.bundle_dir)

    if not verify_bundle_integrity(bundle_dir):
        print("FAIL: bundle integrity check failed")
        return 1

    print("OK")
    return 0


def cmd_ota_verify_zip(args: argparse.Namespace) -> int:
    """
    Verify a bundle.zip by extracting to a temp dir and verifying.
    """
    zip_path = Path(args.zip_path)

    # Read secret if provided
    secret = None
    if args.secret:
        secret = args.secret.encode("utf-8")
    elif args.secret_file:
        secret = Path(args.secret_file).read_bytes().strip()

    success, error = verify_zip_bundle(zip_path, secret=secret)

    if success:
        print("OK")
        return 0
    else:
        print(f"FAIL: {error}")
        return 1


# ============================================================================
# Commands: Dance Pack Sets
# ============================================================================


def cmd_dance_pack_set_list(args: argparse.Namespace) -> int:
    """
    List all bundled dance pack sets.
    """
    sets = list_all_sets()

    if args.json:
        data = [
            {
                "id": s.id,
                "display_name": s.display_name,
                "tier": s.tier,
                "pack_count": len(s.packs),
            }
            for s in sets
        ]
        print(json.dumps(data, indent=2))
    else:
        for s in sets:
            print(f"{s.id}  ({s.tier})  {s.display_name}  [{len(s.packs)} packs]")

    return 0


def cmd_dance_pack_set_validate(args: argparse.Namespace) -> int:
    """
    Validate a pack set (bundled or from file).
    Checks that all referenced pack IDs exist.
    """
    try:
        if args.path:
            pack_set = load_set_from_file(args.path)
        else:
            pack_set = load_set_by_id(args.set_id)

        validate_set_references(pack_set)

        if not args.quiet:
            print(f"OK: {pack_set.id} ({len(pack_set.packs)} packs)")
            for pid in pack_set.packs:
                print(f"  - {pid}")

        return 0
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2


def cmd_dance_pack_list(args: argparse.Namespace) -> int:
    """
    List all bundled dance packs.
    """
    pack_ids = list_pack_ids()

    if args.json:
        print(json.dumps(pack_ids, indent=2))
    else:
        for pid in pack_ids:
            print(pid)

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    p = argparse.ArgumentParser(
        prog="sgc",
        description="Smart Guitar Coach CLI (Mode 1 / OTA tools)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # --- export-bundle ---
    p_e = sub.add_parser("export-bundle", help="Build firmware envelope JSON from SessionRecord.")
    p_e.add_argument("--session", required=True, help="Path to session.json (SessionRecord).")
    p_e.add_argument("--output", "-o", default=None, help="Output file (stdout if omitted).")
    p_e.set_defaults(func=cmd_export_bundle)

    # --- ota-pack ---
    p_p = sub.add_parser("ota-pack", help="Build HMAC-signed OTA payload JSON.")
    p_p.add_argument("--session", required=True, help="Path to session.json (SessionRecord).")
    p_p.add_argument("--secret", default=None, help="HMAC secret string.")
    p_p.add_argument("--secret-file", default=None, help="Path to file containing HMAC secret.")
    p_p.add_argument("--output", "-o", default=None, help="Output file (stdout if omitted).")
    p_p.set_defaults(func=cmd_ota_pack)

    # --- ota-verify (HMAC) ---
    p_vh = sub.add_parser("ota-verify", help="Verify HMAC signature of OTA payload JSON.")
    p_vh.add_argument("payload", help="Path to OTA payload JSON file.")
    p_vh.add_argument("--secret", default=None, help="HMAC secret string.")
    p_vh.add_argument("--secret-file", default=None, help="Path to file containing HMAC secret.")
    p_vh.set_defaults(func=cmd_ota_verify_hmac)

    # --- ota-bundle ---
    p_b = sub.add_parser("ota-bundle", help="Build OTA bundle from SessionRecord or Dance Pack.")
    p_b.add_argument("--session", default=None, help="Path to session.json (SessionRecord).")
    p_b.add_argument("--dance-pack", default=None, help="Single dance pack ID to build bundle from.")
    p_b.add_argument("--dance-pack-path", default=None, help="Path to single dance pack YAML file.")
    p_b.add_argument("--out", required=True, help="Output directory root.")
    p_b.add_argument("--manifest", default=None, help="Custom manifest path (default: <out>/ota_manifest.json).")
    p_b.add_argument("--name", default=None, help="Optional bundle folder name override.")
    p_b.add_argument("--product", default="smart-guitar", help="Product name (manifest routing).")
    p_b.add_argument("--device-model", default=None, help="Target device model.")
    p_b.add_argument("--min-firmware", default=None, help="Target minimum firmware.")
    p_b.add_argument("--zip", action="store_true", help="Also create bundle.zip.")
    p_b.add_argument("--secret", default=None, help="HMAC secret for signing.")
    p_b.add_argument("--secret-file", default=None, help="Path to file containing HMAC secret.")
    p_b.set_defaults(func=cmd_ota_bundle)

    # --- ota-verify-folder ---
    p_vf = sub.add_parser("ota-verify-folder", help="Verify bundle folder integrity against manifest.")
    p_vf.add_argument("bundle_dir", help="Path to bundle directory (folder).")
    p_vf.set_defaults(func=cmd_ota_verify_folder)

    # --- ota-verify-zip ---
    p_z = sub.add_parser("ota-verify-zip", help="Verify bundle.zip by extracting and verifying.")
    p_z.add_argument("zip_path", help="Path to bundle.zip")
    p_z.add_argument("--secret", default=None, help="HMAC secret for signature verification.")
    p_z.add_argument("--secret-file", default=None, help="Path to file containing HMAC secret.")
    p_z.set_defaults(func=cmd_ota_verify_zip)

    # --- dance-pack-list ---
    p_dpl = sub.add_parser("dance-pack-list", help="List all bundled dance packs.")
    p_dpl.add_argument("--json", action="store_true", help="Output as JSON.")
    p_dpl.set_defaults(func=cmd_dance_pack_list)

    # --- dance-pack-set-list ---
    p_dsl = sub.add_parser("dance-pack-set-list", help="List all bundled dance pack sets.")
    p_dsl.add_argument("--json", action="store_true", help="Output as JSON.")
    p_dsl.set_defaults(func=cmd_dance_pack_set_list)

    # --- dance-pack-set-validate ---
    p_dsv = sub.add_parser("dance-pack-set-validate", help="Validate pack set references.")
    p_dsv.add_argument("set_id", nargs="?", help="Pack set ID (bundled).")
    p_dsv.add_argument("--path", default=None, help="Path to pack set YAML file.")
    p_dsv.add_argument("--quiet", "-q", action="store_true", help="Suppress output on success.")
    p_dsv.set_defaults(func=cmd_dance_pack_set_validate)

    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130
    except FileNotFoundError as e:
        print(f"ERROR: file not found: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
