"""
Unit tests for Dance Pack v1 schema and validation.

Tests ensure:
- All required sections present
- No unknown fields accepted
- Numeric ranges enforced
- Groove grids internally consistent
- Practice weights sum to 1.0
- Strict validation (no soft failures)
"""

from pathlib import Path

import pytest

from zt_band.dance_pack import (
    DancePackV1,
    DancePackLoadError,
    load_dance_pack,
    load_dance_pack_dict,
    # Enums
    DanceFamily,
    Subdivision,
    ClaveType,
    DifficultyRating,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


PACKS_DIR = Path(__file__).parent.parent / "packs"


@pytest.fixture
def minimal_valid_pack() -> dict:
    """Minimal valid Dance Pack for testing."""
    return {
        "schema_id": "dance_pack",
        "schema_version": "v1",
        "metadata": {
            "id": "test_form_v1",
            "display_name": "Test Form",
            "dance_family": "jazz_american",
            "version": "1.0.0",
            "engine_compatibility": ">=0.2.0",
        },
        "groove": {
            "meter": "4/4",
            "cycle_bars": 4,
            "subdivision": "binary",
            "tempo_range_bpm": [100, 140],
            "accent_grid": {
                "strong_beats": [1, 3],
                "secondary_beats": [2, 4],
            },
        },
        "harmony_constraints": {
            "harmonic_rhythm": {
                "max_changes_per_cycle": 4,
            },
        },
        "performance_profile": {
            "velocity_range": {
                "min": 40,
                "max": 100,
            },
        },
        "practice_mapping": {
            "primary_focus": ["groove_lock"],
            "evaluation_weights": {
                "timing_accuracy": 0.4,
                "harmonic_choice": 0.4,
                "dynamic_control": 0.2,
            },
            "difficulty_rating": "medium",
        },
    }


# -----------------------------------------------------------------------------
# Basic Validation Tests
# -----------------------------------------------------------------------------


def test_load_minimal_valid_pack(minimal_valid_pack: dict) -> None:
    """Minimal valid pack should load successfully."""
    pack = load_dance_pack_dict(minimal_valid_pack)
    assert pack.schema_id == "dance_pack"
    assert pack.schema_version == "v1"
    assert pack.metadata.id == "test_form_v1"


def test_missing_required_section_fails() -> None:
    """Missing required section should fail validation."""
    incomplete = {
        "schema_id": "dance_pack",
        "schema_version": "v1",
        "metadata": {
            "id": "test_v1",
            "display_name": "Test",
            "dance_family": "jazz_american",
            "version": "1.0.0",
            "engine_compatibility": ">=0.2.0",
        },
        # Missing groove, harmony_constraints, performance_profile, practice_mapping
    }
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(incomplete)


def test_unknown_field_rejected(minimal_valid_pack: dict) -> None:
    """Unknown fields at root level should be rejected."""
    minimal_valid_pack["unknown_field"] = "should fail"
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_schema_id_must_be_dance_pack(minimal_valid_pack: dict) -> None:
    """schema_id must be exactly 'dance_pack'."""
    minimal_valid_pack["schema_id"] = "wrong_schema"
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_schema_version_must_be_v1(minimal_valid_pack: dict) -> None:
    """schema_version must be exactly 'v1'."""
    minimal_valid_pack["schema_version"] = "v2"
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


# -----------------------------------------------------------------------------
# Metadata Validation
# -----------------------------------------------------------------------------


def test_metadata_id_format(minimal_valid_pack: dict) -> None:
    """Pack ID must match pattern: lowercase, underscores, ending with _vN."""
    # Valid
    minimal_valid_pack["metadata"]["id"] = "samba_traditional_v1"
    pack = load_dance_pack_dict(minimal_valid_pack)
    assert pack.metadata.id == "samba_traditional_v1"

    # Invalid - no version suffix
    minimal_valid_pack["metadata"]["id"] = "samba_traditional"
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)

    # Invalid - uppercase
    minimal_valid_pack["metadata"]["id"] = "Samba_v1"
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_metadata_version_semver(minimal_valid_pack: dict) -> None:
    """Version must be semantic version format."""
    minimal_valid_pack["metadata"]["version"] = "1.0"  # Missing patch
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_metadata_dance_family_enum(minimal_valid_pack: dict) -> None:
    """Dance family must be valid enum value."""
    minimal_valid_pack["metadata"]["dance_family"] = "invalid_family"
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


# -----------------------------------------------------------------------------
# Groove Validation
# -----------------------------------------------------------------------------


def test_groove_meter_format(minimal_valid_pack: dict) -> None:
    """Meter must be valid time signature."""
    # Valid meters
    for meter in ["2/4", "3/4", "4/4", "6/8", "12/8"]:
        minimal_valid_pack["groove"]["meter"] = meter
        pack = load_dance_pack_dict(minimal_valid_pack)
        assert pack.groove.meter == meter

    # Invalid meter
    minimal_valid_pack["groove"]["meter"] = "5/3"  # Invalid denominator
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_groove_tempo_range_bounds(minimal_valid_pack: dict) -> None:
    """Tempo range must have min <= max and be within 20-300 BPM."""
    # Valid
    minimal_valid_pack["groove"]["tempo_range_bpm"] = [80, 120]
    pack = load_dance_pack_dict(minimal_valid_pack)
    assert pack.groove.tempo_range_bpm == [80, 120]

    # Invalid - min > max
    minimal_valid_pack["groove"]["tempo_range_bpm"] = [150, 100]
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)

    # Invalid - out of range
    minimal_valid_pack["groove"]["tempo_range_bpm"] = [10, 100]  # min too low
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_groove_swing_ratio_bounds(minimal_valid_pack: dict) -> None:
    """Swing ratio must be 0.0-1.0."""
    minimal_valid_pack["groove"]["swing_ratio"] = 1.5
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_groove_accent_grid_beats_positive(minimal_valid_pack: dict) -> None:
    """Accent grid beat numbers must be >= 1."""
    minimal_valid_pack["groove"]["accent_grid"]["strong_beats"] = [0, 2]
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_groove_clave_explicit_requires_pattern(minimal_valid_pack: dict) -> None:
    """Explicit clave type requires non-empty pattern."""
    minimal_valid_pack["groove"]["clave"] = {
        "type": "explicit",
        "pattern": [],  # Empty pattern with explicit type
    }
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


# -----------------------------------------------------------------------------
# Harmony Constraints Validation
# -----------------------------------------------------------------------------


def test_harmony_max_changes_bounds(minimal_valid_pack: dict) -> None:
    """max_changes_per_cycle must be 1-16."""
    minimal_valid_pack["harmony_constraints"]["harmonic_rhythm"]["max_changes_per_cycle"] = 0
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)

    minimal_valid_pack["harmony_constraints"]["harmonic_rhythm"]["max_changes_per_cycle"] = 20
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_tritone_forbidden_beats_positive(minimal_valid_pack: dict) -> None:
    """Forbidden beats must be >= 1."""
    minimal_valid_pack["harmony_constraints"]["tritone_usage"] = {
        "allowed": True,
        "weight": "light",
        "forbidden_on_beats": [0, 1],  # 0 is invalid
    }
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


# -----------------------------------------------------------------------------
# Performance Profile Validation
# -----------------------------------------------------------------------------


def test_velocity_range_min_max(minimal_valid_pack: dict) -> None:
    """Velocity min must be <= max."""
    minimal_valid_pack["performance_profile"]["velocity_range"] = {
        "min": 100,
        "max": 50,  # Invalid: min > max
    }
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_velocity_midi_bounds(minimal_valid_pack: dict) -> None:
    """Velocity values must be valid MIDI (1-127)."""
    minimal_valid_pack["performance_profile"]["velocity_range"] = {
        "min": 0,  # Invalid: MIDI velocity starts at 1
        "max": 100,
    }
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


# -----------------------------------------------------------------------------
# Practice Mapping Validation
# -----------------------------------------------------------------------------


def test_practice_weights_sum_to_one(minimal_valid_pack: dict) -> None:
    """Evaluation weights must sum to 1.0."""
    minimal_valid_pack["practice_mapping"]["evaluation_weights"] = {
        "timing_accuracy": 0.5,
        "harmonic_choice": 0.3,
        "dynamic_control": 0.1,
        # Sum = 0.9, not 1.0
    }
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


def test_practice_weights_sum_exactly_one(minimal_valid_pack: dict) -> None:
    """Weights summing to exactly 1.0 should pass."""
    minimal_valid_pack["practice_mapping"]["evaluation_weights"] = {
        "timing_accuracy": 0.33,
        "harmonic_choice": 0.33,
        "dynamic_control": 0.34,
    }
    pack = load_dance_pack_dict(minimal_valid_pack)
    total = (
        pack.practice_mapping.evaluation_weights.timing_accuracy
        + pack.practice_mapping.evaluation_weights.harmonic_choice
        + pack.practice_mapping.evaluation_weights.dynamic_control
    )
    assert abs(total - 1.0) < 0.01


def test_practice_primary_focus_count(minimal_valid_pack: dict) -> None:
    """Primary focus must have 1-4 items."""
    # Too many
    minimal_valid_pack["practice_mapping"]["primary_focus"] = [
        "groove_lock",
        "timing_accuracy",
        "dynamic_control",
        "harmonic_awareness",
        "ghost_notes",  # 5th item
    ]
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)

    # Empty
    minimal_valid_pack["practice_mapping"]["primary_focus"] = []
    with pytest.raises(DancePackLoadError):
        load_dance_pack_dict(minimal_valid_pack)


# -----------------------------------------------------------------------------
# File Loading Tests
# -----------------------------------------------------------------------------


@pytest.mark.skipif(not PACKS_DIR.exists(), reason="packs directory not found")
def test_load_samba_pack_from_file() -> None:
    """Load the reference Samba pack from file."""
    samba_path = PACKS_DIR / "samba_traditional_v1.dpack.json"
    if not samba_path.exists():
        pytest.skip("Samba pack not found")

    pack = load_dance_pack(samba_path)
    assert pack.metadata.id == "samba_traditional_v1"
    assert pack.metadata.dance_family == DanceFamily.AFRO_BRAZILIAN
    assert pack.groove.meter == "2/4"
    assert pack.groove.subdivision == Subdivision.BINARY
    assert pack.practice_mapping.difficulty_rating == DifficultyRating.MEDIUM


@pytest.mark.skipif(not PACKS_DIR.exists(), reason="packs directory not found")
def test_load_all_reference_packs() -> None:
    """All .dpack.json files in packs/ should load without error."""
    pack_files = list(PACKS_DIR.glob("*.dpack.json"))
    assert len(pack_files) > 0, "No pack files found"

    for pack_file in pack_files:
        pack = load_dance_pack(pack_file)
        assert pack.schema_id == "dance_pack"
        assert pack.schema_version == "v1"


def test_load_nonexistent_file() -> None:
    """Loading nonexistent file should raise DancePackLoadError."""
    with pytest.raises(DancePackLoadError, match="not found"):
        load_dance_pack("/nonexistent/path/pack.dpack.json")


# -----------------------------------------------------------------------------
# Enum Coverage Tests
# -----------------------------------------------------------------------------


def test_all_dance_families_valid(minimal_valid_pack: dict) -> None:
    """All DanceFamily enum values should be accepted."""
    for family in DanceFamily:
        minimal_valid_pack["metadata"]["dance_family"] = family.value
        pack = load_dance_pack_dict(minimal_valid_pack)
        assert pack.metadata.dance_family == family


def test_all_subdivisions_valid(minimal_valid_pack: dict) -> None:
    """All Subdivision enum values should be accepted."""
    for subdiv in Subdivision:
        minimal_valid_pack["groove"]["subdivision"] = subdiv.value
        pack = load_dance_pack_dict(minimal_valid_pack)
        assert pack.groove.subdivision == subdiv


def test_all_clave_types_valid(minimal_valid_pack: dict) -> None:
    """All ClaveType enum values should be accepted."""
    for ctype in ClaveType:
        clave_def = {"type": ctype.value}
        if ctype == ClaveType.EXPLICIT:
            clave_def["pattern"] = [1, 0, 1, 0]
        minimal_valid_pack["groove"]["clave"] = clave_def
        pack = load_dance_pack_dict(minimal_valid_pack)
        assert pack.groove.clave.type == ctype


def test_all_difficulty_ratings_valid(minimal_valid_pack: dict) -> None:
    """All DifficultyRating enum values should be accepted."""
    for diff in DifficultyRating:
        minimal_valid_pack["practice_mapping"]["difficulty_rating"] = diff.value
        pack = load_dance_pack_dict(minimal_valid_pack)
        assert pack.practice_mapping.difficulty_rating == diff
