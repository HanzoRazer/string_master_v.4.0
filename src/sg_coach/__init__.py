"""
Smart Guitar Coach — Mode 1 (deterministic coaching spine).

Pipeline: SessionRecord → CoachEvaluation → PracticeAssignment

This module provides:
- Pydantic v2 models for session data, evaluations, and assignments
- Deterministic evaluation policy (facts → findings → focus)
- Deterministic assignment planner (focus → constraints → success criteria)
- OTA bundle builder + verifier (manifest, HMAC signing, zip packaging)
- CLI tools: sgc export-bundle, ota-pack, ota-verify, ota-bundle, ota-verify-zip
"""

from .contract import COACH_CONTRACT_VERSION
from .schemas import (
    # Enums
    ProgramType,
    Severity,
    ClaveKind,
    CoachMode,
    # Shared
    ProgramRef,
    # Session layer
    SessionTiming,
    TimingErrorStats,
    PerformanceSummary,
    SessionEvents,
    SessionRecord,
    # Coach layer
    FindingEvidence,
    CoachFinding,
    FocusRecommendation,
    CoachEvaluation,
    # Assignment layer
    AssignmentConstraints,
    AssignmentFocus,
    SuccessCriteria,
    CoachPrompt,
    PracticeAssignment,
    # Validators
    validate_coach_references_session,
    validate_assignment_program_exists,
)
from .coach_policy import evaluate_session, COACH_VERSION
from .assignment_policy import plan_assignment, AssignmentPolicyConfig
from .assignment_serializer import (
    FirmwareEnvelope,
    serialize_bundle,
    deserialize_bundle,
)
from .ota_payload import (
    # Constants
    OTA_BUNDLE_CONTRACT_VERSION,
    HMAC_ALGORITHM,
    # Manifest
    OtaArtifact,
    OtaBundleManifest,
    # Envelope
    OtaEnvelope,
    # Functions
    hmac_sha256_hex,
    sha256_file,
    sha256_bytes,
    build_ota_payload,
    verify_ota_payload,
    build_assignment_ota_bundle,
    verify_bundle_integrity,
    verify_bundle_signature,
    verify_zip_bundle,
    BundleBuildResult,
)
from .cli import main

__all__ = [
    # Contract
    "COACH_CONTRACT_VERSION",
    "COACH_VERSION",
    # Enums
    "ProgramType",
    "Severity",
    "ClaveKind",
    "CoachMode",
    # Shared
    "ProgramRef",
    # Session layer
    "SessionTiming",
    "TimingErrorStats",
    "PerformanceSummary",
    "SessionEvents",
    "SessionRecord",
    # Coach layer
    "FindingEvidence",
    "CoachFinding",
    "FocusRecommendation",
    "CoachEvaluation",
    # Assignment layer
    "AssignmentConstraints",
    "AssignmentFocus",
    "SuccessCriteria",
    "CoachPrompt",
    "PracticeAssignment",
    # Validators
    "validate_coach_references_session",
    "validate_assignment_program_exists",
    # Policies
    "evaluate_session",
    "plan_assignment",
    "AssignmentPolicyConfig",
    # Serialization
    "FirmwareEnvelope",
    "serialize_bundle",
    "deserialize_bundle",
    # OTA
    "OTA_BUNDLE_CONTRACT_VERSION",
    "HMAC_ALGORITHM",
    "OtaArtifact",
    "OtaBundleManifest",
    "OtaEnvelope",
    "hmac_sha256_hex",
    "sha256_file",
    "sha256_bytes",
    "build_ota_payload",
    "verify_ota_payload",
    "build_assignment_ota_bundle",
    "verify_bundle_integrity",
    "verify_bundle_signature",
    "verify_zip_bundle",
    "BundleBuildResult",
    # CLI
    "main",
]
