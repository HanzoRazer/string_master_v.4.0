"""
Dance Pack v1 — Pydantic models for declarative dance form bundles.

A Dance Pack encodes a dance-derived musical form as groove, harmonic
constraints, behavioral nuance, and practice intelligence — without
embedding pedagogy or chord content.

Key properties:
- Groove-first (time and motion are primary)
- Harmony-constraining, not harmony-defining
- Deterministic and testable
- Composable and extensible
- Product-agnostic (Smart Guitar, String Master, Coach all consume)
"""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class DanceFamily(str, Enum):
    """Dance family classification for grouping and discovery."""

    AFRO_BRAZILIAN = "afro_brazilian"
    AFRO_CUBAN = "afro_cuban"
    CARIBBEAN = "caribbean"
    JAZZ_AMERICAN = "jazz_american"
    EUROPEAN_BALLROOM = "european_ballroom"
    LATIN_AMERICAN = "latin_american"
    AFRICAN = "african"
    BLUES_AMERICAN = "blues_american"
    ROCK_AMERICAN = "rock_american"
    COUNTRY_AMERICAN = "country_american"
    IBERIAN = "iberian"  # Flamenco, fado, and other Iberian Peninsula styles
    FUSION = "fusion"


class License(str, Enum):
    """License tier for monetization."""

    CORE = "core"
    PREMIUM = "premium"
    COMMUNITY = "community"
    CUSTOM = "custom"


class Subdivision(str, Enum):
    """Base subdivision type for timing quantization."""

    BINARY = "binary"
    TERNARY = "ternary"
    COMPOUND = "compound"


class ClaveType(str, Enum):
    """How clave operates in a dance form."""

    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    NONE = "none"


class ClaveDirection(str, Enum):
    """Clave direction constraint."""

    FORWARD = "forward"
    REVERSE = "reverse"
    EITHER = "either"


class ChangeOnStrongBeat(str, Enum):
    """Chord change alignment constraint."""

    REQUIRED = "required"
    PREFERRED = "preferred"
    ALLOWED = "allowed"
    FORBIDDEN = "forbidden"


class ResolutionStrength(str, Enum):
    """Dominant resolution strength."""

    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    NONE = "none"


class TritoneWeight(str, Enum):
    """Tritone substitution aggressiveness."""

    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"


class ModalInterchangeLevel(str, Enum):
    """Modal interchange freedom."""

    NONE = "none"
    DIATONIC_ONLY = "diatonic_only"
    COMMON_TONES = "common_tones"
    FREE = "free"


class OrnamentDensity(str, Enum):
    """Ornamental figure density."""

    NONE = "none"
    SPARSE = "sparse"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class RegisterBias(str, Enum):
    """Preferred pitch register."""

    LOW = "low"
    MID_LOW = "mid_low"
    MID = "mid"
    MID_HIGH = "mid_high"
    HIGH = "high"


class PracticeFocusArea(str, Enum):
    """Practice objective categories."""

    GROOVE_LOCK = "groove_lock"
    TIMING_ACCURACY = "timing_accuracy"
    DYNAMIC_CONTROL = "dynamic_control"
    HARMONIC_AWARENESS = "harmonic_awareness"
    SECONDARY_DOMINANTS = "secondary_dominants"
    TRITONE_SUBSTITUTION = "tritone_substitution"
    RHYTHMIC_VARIATION = "rhythmic_variation"
    CALL_RESPONSE = "call_response"
    SYNCOPATION = "syncopation"
    GHOST_NOTES = "ghost_notes"
    SWING_FEEL = "swing_feel"
    CLAVE_ALIGNMENT = "clave_alignment"


class CommonError(str, Enum):
    """Detectable practice errors."""

    LATE_RESOLUTION = "late_resolution"
    EARLY_RESOLUTION = "early_resolution"
    TRITONE_ON_STRONG_BEAT = "tritone_on_strong_beat"
    RUSHED_TEMPO = "rushed_tempo"
    DRAGGED_TEMPO = "dragged_tempo"
    GHOST_TOO_LOUD = "ghost_too_loud"
    ACCENT_TOO_SOFT = "accent_too_soft"
    WRONG_CLAVE_SIDE = "wrong_clave_side"
    MISSED_PICKUP = "missed_pickup"
    OVER_ORNAMENTATION = "over_ornamentation"
    LOST_PULSE = "lost_pulse"


class DifficultyRating(str, Enum):
    """Curriculum difficulty placement."""

    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADVANCED = "advanced"
    EXPERT = "expert"


# -----------------------------------------------------------------------------
# Section Models
# -----------------------------------------------------------------------------


class PackMetadata(BaseModel):
    """Identity, versioning, and packaging information."""

    id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*_v[0-9]+$")]
    display_name: Annotated[str, Field(min_length=1, max_length=64)]
    dance_family: DanceFamily
    version: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]
    author: str = "system"
    license: License = License.CORE
    engine_compatibility: Annotated[str, Field(pattern=r"^(>=|>|=|<|<=)?[0-9]+\.[0-9]+\.[0-9]+$")]
    tags: list[Annotated[str, Field(max_length=32)]] = Field(default_factory=list, max_length=10)


class AccentGrid(BaseModel):
    """Defines where musical weight lives within the cycle."""

    strong_beats: Annotated[list[int], Field(min_length=1)]
    secondary_beats: list[int] = Field(default_factory=list)
    ghost_allowed: bool = True
    offbeat_emphasis: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0

    @field_validator("strong_beats", "secondary_beats")
    @classmethod
    def beats_positive(cls, v: list[int]) -> list[int]:
        if any(b < 1 for b in v):
            raise ValueError("Beat numbers must be >= 1")
        return v


class Clave(BaseModel):
    """Clave pattern definition."""

    type: ClaveType = ClaveType.NONE
    pattern: list[Literal[0, 1]] = Field(default_factory=list)
    direction: ClaveDirection = ClaveDirection.FORWARD

    @model_validator(mode="after")
    def explicit_requires_pattern(self) -> "Clave":
        if self.type == ClaveType.EXPLICIT and not self.pattern:
            raise ValueError("Clave type 'explicit' requires a non-empty pattern")
        return self


class GrooveDefinition(BaseModel):
    """Primary identity of the dance form. The heart of the pack."""

    meter: Annotated[str, Field(pattern=r"^[1-9][0-9]*/[124816]$")]
    cycle_bars: Annotated[int, Field(ge=1, le=16)]
    subdivision: Subdivision
    tempo_range_bpm: Annotated[list[float], Field(min_length=2, max_length=2)]
    swing_ratio: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    accent_grid: AccentGrid
    clave: Clave = Field(default_factory=Clave)

    @field_validator("tempo_range_bpm")
    @classmethod
    def tempo_range_valid(cls, v: list[float]) -> list[float]:
        if len(v) != 2:
            raise ValueError("tempo_range_bpm must have exactly 2 elements")
        if not (20 <= v[0] <= 300 and 20 <= v[1] <= 300):
            raise ValueError("Tempo values must be between 20 and 300 BPM")
        if v[0] > v[1]:
            raise ValueError("tempo_range_bpm[0] must be <= tempo_range_bpm[1]")
        return v


class HarmonicRhythm(BaseModel):
    """Timing constraints on chord changes."""

    max_changes_per_cycle: Annotated[int, Field(ge=1, le=16)]
    min_beats_between_changes: Annotated[float, Field(ge=0.5, le=16)] = 1.0
    change_on_strong_beat: ChangeOnStrongBeat = ChangeOnStrongBeat.PREFERRED


class DominantBehavior(BaseModel):
    """Rules for dominant chord usage and resolution."""

    allowed: bool = True
    resolution_strength: ResolutionStrength = ResolutionStrength.MEDIUM
    secondary_dominants: bool = False


class TritoneUsage(BaseModel):
    """Tritone substitution behavior constraints."""

    allowed: bool = False
    weight: TritoneWeight = TritoneWeight.NONE
    forbidden_on_beats: list[int] = Field(default_factory=list)

    @field_validator("forbidden_on_beats")
    @classmethod
    def beats_positive(cls, v: list[int]) -> list[int]:
        if any(b < 1 for b in v):
            raise ValueError("Beat numbers must be >= 1")
        return v


class ChromaticDrift(BaseModel):
    """Rules for chromatic voice movement."""

    allowed: bool = False
    max_semitones: Annotated[int, Field(ge=0, le=4)] = 0


class ModalConstraints(BaseModel):
    """Modal mixture and interchange rules."""

    parallel_minor_allowed: bool = False
    modal_interchange_level: ModalInterchangeLevel = ModalInterchangeLevel.DIATONIC_ONLY


class HarmonyConstraints(BaseModel):
    """Constraints on harmonic motion. Never defines chords, only motion rules."""

    harmonic_rhythm: HarmonicRhythm
    dominant_behavior: DominantBehavior = Field(default_factory=DominantBehavior)
    tritone_usage: TritoneUsage = Field(default_factory=TritoneUsage)
    chromatic_drift: ChromaticDrift = Field(default_factory=ChromaticDrift)
    modal_constraints: ModalConstraints = Field(default_factory=ModalConstraints)


class VelocityRange(BaseModel):
    """MIDI velocity bounds for dynamics."""

    min: Annotated[int, Field(ge=1, le=127)]
    max: Annotated[int, Field(ge=1, le=127)]
    ghost_max: Annotated[int, Field(ge=1, le=64)] = 24
    accent_min: Annotated[int, Field(ge=64, le=127)] = 78

    @model_validator(mode="after")
    def min_less_than_max(self) -> "VelocityRange":
        if self.min > self.max:
            raise ValueError("velocity_range.min must be <= velocity_range.max")
        return self


class PickupBias(BaseModel):
    """Anticipation/pickup note behavior."""

    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    max_offset_beats: Annotated[float, Field(ge=0.0, le=1.0)] = 0.25


class ContourPreference(BaseModel):
    """Melodic contour tendencies."""

    stepwise_weight: Annotated[float, Field(ge=0.0, le=1.0)] = 0.6
    leap_weight: Annotated[float, Field(ge=0.0, le=1.0)] = 0.4
    max_leap_interval: Annotated[int, Field(ge=2, le=12)] = 7


class Articulation(BaseModel):
    """Note length and separation."""

    default_duration_ratio: Annotated[float, Field(ge=0.1, le=1.0)] = 0.8
    staccato_probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    legato_probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0


class PerformanceProfile(BaseModel):
    """How notes are played, not which notes are chosen."""

    velocity_range: VelocityRange
    pickup_bias: PickupBias = Field(default_factory=PickupBias)
    contour_preference: ContourPreference = Field(default_factory=ContourPreference)
    ornament_density: OrnamentDensity = OrnamentDensity.LOW
    register_bias: RegisterBias = RegisterBias.MID
    articulation: Articulation = Field(default_factory=Articulation)


class EvaluationWeights(BaseModel):
    """Weights for scoring. Must sum to 1.0."""

    timing_accuracy: Annotated[float, Field(ge=0.0, le=1.0)]
    harmonic_choice: Annotated[float, Field(ge=0.0, le=1.0)]
    dynamic_control: Annotated[float, Field(ge=0.0, le=1.0)]
    groove_feel: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "EvaluationWeights":
        total = self.timing_accuracy + self.harmonic_choice + self.dynamic_control + self.groove_feel
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"evaluation_weights must sum to 1.0 (got {total:.3f})")
        return self


class PracticeMapping(BaseModel):
    """Bridge to Coach Mode. Practice intelligence emerges from form definition."""

    primary_focus: Annotated[list[PracticeFocusArea], Field(min_length=1, max_length=4)]
    evaluation_weights: EvaluationWeights
    common_errors: list[CommonError] = Field(default_factory=list)
    difficulty_rating: DifficultyRating
    prerequisite_forms: list[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Root Model
# -----------------------------------------------------------------------------


class DancePackV1(BaseModel):
    """
    Dance Pack v1 — declarative, executable bundle encoding a dance-derived
    musical form as groove, harmonic constraints, behavioral nuance, and
    practice intelligence.

    This is the contract between culture and computation.
    """

    schema_id: Literal["dance_pack"] = "dance_pack"
    schema_version: Literal["v1"] = "v1"
    metadata: PackMetadata
    groove: GrooveDefinition
    harmony_constraints: HarmonyConstraints
    performance_profile: PerformanceProfile
    practice_mapping: PracticeMapping
    extensions: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------
# Loader
# -----------------------------------------------------------------------------


class DancePackLoadError(Exception):
    """Raised when a Dance Pack fails to load or validate."""

    pass


def load_dance_pack(path: str | Path) -> DancePackV1:
    """
    Load and validate a Dance Pack from a JSON file.

    If validation fails, raises DancePackLoadError.
    No soft failures. No silent fallback behavior.

    Args:
        path: Path to the .dpack.json file

    Returns:
        Validated DancePackV1 instance

    Raises:
        DancePackLoadError: If file not found, invalid JSON, or validation fails
    """
    path = Path(path)
    if not path.exists():
        raise DancePackLoadError(f"Dance Pack not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DancePackLoadError(f"Invalid JSON in {path}: {e}") from e

    try:
        pack = DancePackV1.model_validate(data)
    except Exception as e:
        raise DancePackLoadError(f"Dance Pack validation failed for {path}: {e}") from e

    return pack


def load_dance_pack_dict(data: dict) -> DancePackV1:
    """
    Validate a Dance Pack from a dictionary.

    Args:
        data: Pack data as dictionary

    Returns:
        Validated DancePackV1 instance

    Raises:
        DancePackLoadError: If validation fails
    """
    try:
        return DancePackV1.model_validate(data)
    except Exception as e:
        raise DancePackLoadError(f"Dance Pack validation failed: {e}") from e


__all__ = [
    # Enums
    "DanceFamily",
    "License",
    "Subdivision",
    "ClaveType",
    "ClaveDirection",
    "ChangeOnStrongBeat",
    "ResolutionStrength",
    "TritoneWeight",
    "ModalInterchangeLevel",
    "OrnamentDensity",
    "RegisterBias",
    "PracticeFocusArea",
    "CommonError",
    "DifficultyRating",
    # Section models
    "PackMetadata",
    "AccentGrid",
    "Clave",
    "GrooveDefinition",
    "HarmonicRhythm",
    "DominantBehavior",
    "TritoneUsage",
    "ChromaticDrift",
    "ModalConstraints",
    "HarmonyConstraints",
    "VelocityRange",
    "PickupBias",
    "ContourPreference",
    "Articulation",
    "PerformanceProfile",
    "EvaluationWeights",
    "PracticeMapping",
    # Root model
    "DancePackV1",
    # Loader
    "DancePackLoadError",
    "load_dance_pack",
    "load_dance_pack_dict",
]
