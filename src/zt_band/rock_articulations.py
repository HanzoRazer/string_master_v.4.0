"""
Rock articulation probability engine.

Drop-in probability-curve layer for rock library articulation tags.
Designed to be:
- Stable (no name drift)
- Tunable (style + difficulty + density)
- Engine-friendly (pure numbers + simple combinators)
- Composable (base -> style multiplier -> difficulty gate -> curve -> budget)

Usage:
    from zt_band.rock_articulations import (
        p_final,
        sample_tags_for_bar,
        Difficulty,
        RockStyle,
    )

    # Get final probability for a tag
    prob = p_final(
        tag="articulation.left_hand.bend_half",
        style=RockStyle.SRV,
        difficulty=Difficulty.INTERMEDIATE,
        density=0.5,
        aggression=0.7,
        legato_bias=0.3,
    )

    # Sample tags for a bar
    tags = sample_tags_for_bar(
        note_count=8,
        difficulty=Difficulty.INTERMEDIATE,
        style=RockStyle.HENDRIX,
        density=0.6,
        aggression=0.5,
        legato_bias=0.4,
        seed=42,
    )
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


# =============================================================================
# ENUMS
# =============================================================================

class Difficulty(str, Enum):
    """Difficulty level for articulation gating."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class RockStyle(str, Enum):
    """Rock style for articulation multipliers."""
    NEUTRAL = "NEUTRAL"
    ZEPPELIN = "ZEPPELIN"
    HENDRIX = "HENDRIX"
    SRV = "SRV"


# =============================================================================
# BASE PROBABILITIES (global defaults; neutral style)
# =============================================================================

BASE_PROBABILITIES: dict[str, dict[str, float]] = {
    # --- Left hand ---
    "articulation.left_hand.hammer_on": {"p": 0.12, "scope": "note"},
    "articulation.left_hand.pull_off": {"p": 0.10, "scope": "note"},
    "articulation.left_hand.slide_legato": {"p": 0.07, "scope": "note"},
    "articulation.left_hand.slide_up": {"p": 0.03, "scope": "note"},
    "articulation.left_hand.slide_down": {"p": 0.03, "scope": "note"},
    "articulation.left_hand.bend_quarter": {"p": 0.02, "scope": "note"},
    "articulation.left_hand.bend_half": {"p": 0.06, "scope": "note"},
    "articulation.left_hand.bend_whole": {"p": 0.04, "scope": "note"},
    "articulation.left_hand.bend_extended": {"p": 0.01, "scope": "note"},
    "articulation.left_hand.bend_release": {"p": 0.05, "scope": "note"},
    "articulation.left_hand.pre_bend": {"p": 0.01, "scope": "note"},
    "articulation.left_hand.pre_bend_release": {"p": 0.01, "scope": "note"},
    "articulation.left_hand.trill": {"p": 0.02, "scope": "note"},
    # --- Right hand ---
    "articulation.right_hand.palm_mute": {"p": 0.10, "scope": "note"},
    "articulation.right_hand.rake": {"p": 0.04, "scope": "note"},
    "articulation.right_hand.sweep": {"p": 0.01, "scope": "note"},
    "articulation.right_hand.tremolo_pick": {"p": 0.02, "scope": "note"},
    "articulation.right_hand.pick_slide": {"p": 0.005, "scope": "bar"},
    "articulation.right_hand.tap": {"p": 0.01, "scope": "note"},
    # --- Modulation ---
    "articulation.modulation.vibrato_finger": {"p": 0.08, "scope": "note"},
    "articulation.modulation.vibrato_wide": {"p": 0.03, "scope": "note"},
    "articulation.modulation.vibrato_bar": {"p": 0.01, "scope": "note"},
    "articulation.modulation.bar_dip": {"p": 0.01, "scope": "bar"},
    "articulation.modulation.bar_dive": {"p": 0.005, "scope": "bar"},
    "articulation.modulation.bar_flutter": {"p": 0.002, "scope": "bar"},
    "articulation.modulation.bar_release": {"p": 0.01, "scope": "bar"},
    # --- Harmonics ---
    "articulation.harmonics.harmonic_natural": {"p": 0.01, "scope": "note"},
    "articulation.harmonics.harmonic_artificial": {"p": 0.004, "scope": "note"},
    "articulation.harmonics.harmonic_pinch": {"p": 0.008, "scope": "note"},
    "articulation.harmonics.harmonic_bent": {"p": 0.002, "scope": "note"},
    "articulation.harmonics.harmonic_bar": {"p": 0.001, "scope": "bar"},
    # --- Percussive ---
    "articulation.percussive.ghost_note": {"p": 0.06, "scope": "note"},
    "articulation.percussive.muted_hit": {"p": 0.02, "scope": "note"},
    "articulation.percussive.percussive_slash": {"p": 0.01, "scope": "bar"},
    # --- Sustain / texture ---
    "articulation.sustain.let_ring": {"p": 0.05, "scope": "bar"},
    "articulation.sustain.choke": {"p": 0.01, "scope": "bar"},
}


# =============================================================================
# BUDGETS (hard guardrails: max technique events per bar)
# =============================================================================

BUDGETS_PER_BAR: dict[Difficulty, dict[str, int]] = {
    Difficulty.BEGINNER: {"min": 0, "max": 2},
    Difficulty.INTERMEDIATE: {"min": 1, "max": 4},
    Difficulty.ADVANCED: {"min": 2, "max": 6},
}

BUDGETS_PER_BAR_BY_CLASS: dict[Difficulty, dict[str, int]] = {
    Difficulty.BEGINNER: {
        "articulation.left_hand": 2,
        "articulation.right_hand": 1,
        "articulation.modulation": 1,
        "articulation.harmonics": 0,
        "articulation.percussive": 1,
        "articulation.sustain": 1,
    },
    Difficulty.INTERMEDIATE: {
        "articulation.left_hand": 3,
        "articulation.right_hand": 2,
        "articulation.modulation": 2,
        "articulation.harmonics": 1,
        "articulation.percussive": 2,
        "articulation.sustain": 2,
    },
    Difficulty.ADVANCED: {
        "articulation.left_hand": 4,
        "articulation.right_hand": 3,
        "articulation.modulation": 3,
        "articulation.harmonics": 2,
        "articulation.percussive": 3,
        "articulation.sustain": 3,
    },
}


# =============================================================================
# DIFFICULTY GATES (hard allow/deny lists)
# =============================================================================

DIFFICULTY_GATES: dict[Difficulty, dict[str, list[str]]] = {
    Difficulty.BEGINNER: {
        "allow": [
            "articulation.left_hand.hammer_on",
            "articulation.left_hand.pull_off",
            "articulation.left_hand.slide_legato",
            "articulation.left_hand.slide_up",
            "articulation.left_hand.slide_down",
            "articulation.right_hand.palm_mute",
            "articulation.modulation.vibrato_finger",
            "articulation.percussive.ghost_note",
            "articulation.percussive.muted_hit",
            "articulation.sustain.let_ring",
        ],
        "deny": [
            "articulation.left_hand.bend_quarter",
            "articulation.left_hand.bend_half",
            "articulation.left_hand.bend_whole",
            "articulation.left_hand.bend_extended",
            "articulation.left_hand.bend_release",
            "articulation.left_hand.pre_bend",
            "articulation.left_hand.pre_bend_release",
            "articulation.left_hand.trill",
            "articulation.right_hand.rake",
            "articulation.right_hand.sweep",
            "articulation.right_hand.tremolo_pick",
            "articulation.right_hand.pick_slide",
            "articulation.right_hand.tap",
            "articulation.modulation.vibrato_wide",
            "articulation.modulation.vibrato_bar",
            "articulation.modulation.bar_dip",
            "articulation.modulation.bar_dive",
            "articulation.modulation.bar_flutter",
            "articulation.modulation.bar_release",
            "articulation.harmonics.harmonic_natural",
            "articulation.harmonics.harmonic_artificial",
            "articulation.harmonics.harmonic_pinch",
            "articulation.harmonics.harmonic_bent",
            "articulation.harmonics.harmonic_bar",
            "articulation.sustain.choke",
        ],
    },
    Difficulty.INTERMEDIATE: {
        "allow": [
            "articulation.left_hand.hammer_on",
            "articulation.left_hand.pull_off",
            "articulation.left_hand.slide_legato",
            "articulation.left_hand.slide_up",
            "articulation.left_hand.slide_down",
            "articulation.left_hand.bend_half",
            "articulation.left_hand.bend_release",
            "articulation.left_hand.bend_quarter",
            "articulation.right_hand.palm_mute",
            "articulation.right_hand.rake",
            "articulation.right_hand.tremolo_pick",
            "articulation.modulation.vibrato_finger",
            "articulation.modulation.vibrato_wide",
            "articulation.harmonics.harmonic_natural",
            "articulation.harmonics.harmonic_pinch",
            "articulation.percussive.ghost_note",
            "articulation.percussive.muted_hit",
            "articulation.percussive.percussive_slash",
            "articulation.sustain.let_ring",
            "articulation.sustain.choke",
        ],
        "deny": [
            "articulation.left_hand.bend_extended",
            "articulation.left_hand.pre_bend",
            "articulation.left_hand.pre_bend_release",
            "articulation.right_hand.sweep",
            "articulation.right_hand.tap",
            "articulation.modulation.vibrato_bar",
            "articulation.modulation.bar_flutter",
            "articulation.harmonics.harmonic_artificial",
            "articulation.harmonics.harmonic_bent",
            "articulation.harmonics.harmonic_bar",
        ],
    },
    Difficulty.ADVANCED: {
        "allow": list(BASE_PROBABILITIES.keys()),
        "deny": [],
    },
}


# =============================================================================
# PROBABILITY CURVES (density-sensitive multipliers)
# =============================================================================

@dataclass(frozen=True)
class CurvePoint:
    """A point on a piecewise curve."""
    density: float
    m: float  # multiplier


# Piecewise curves defined as lists of (density, multiplier) points
CURVES: dict[str, list[CurvePoint]] = {
    "gentle_up": [
        CurvePoint(0.0, 0.70),
        CurvePoint(0.3, 0.90),
        CurvePoint(0.6, 1.05),
        CurvePoint(1.0, 1.15),
    ],
    "complexity_down": [
        CurvePoint(0.0, 1.20),
        CurvePoint(0.4, 1.00),
        CurvePoint(0.7, 0.80),
        CurvePoint(1.0, 0.60),
    ],
    "percussive_up": [
        CurvePoint(0.0, 0.60),
        CurvePoint(0.5, 1.10),
        CurvePoint(1.0, 1.35),
    ],
    "sustain_down": [
        CurvePoint(0.0, 1.25),
        CurvePoint(0.5, 1.00),
        CurvePoint(1.0, 0.75),
    ],
}


def curve_multiplier(curve_name: str, density: float) -> float:
    """
    Compute the density-based curve multiplier for a given curve.

    Parameters:
        curve_name: Name of the curve ("gentle_up", "complexity_down", etc.)
        density: Density value 0.0 to 1.0

    Returns:
        Multiplier value (typically 0.6 to 1.4)
    """
    if curve_name not in CURVES:
        return 1.0

    points = CURVES[curve_name]
    density = max(0.0, min(1.0, density))  # clamp

    # Find surrounding points for interpolation
    for i in range(len(points) - 1):
        if points[i].density <= density <= points[i + 1].density:
            d0, m0 = points[i].density, points[i].m
            d1, m1 = points[i + 1].density, points[i + 1].m
            # Linear interpolation
            t = (density - d0) / (d1 - d0) if d1 != d0 else 0.0
            return m0 + t * (m1 - m0)

    # Fallback: return last point's multiplier
    return points[-1].m


# =============================================================================
# CURVE BINDINGS (which curve each tag uses)
# =============================================================================

CURVE_BINDINGS: dict[str, str] = {
    # Left hand
    "articulation.left_hand.hammer_on": "gentle_up",
    "articulation.left_hand.pull_off": "gentle_up",
    "articulation.left_hand.slide_legato": "gentle_up",
    "articulation.left_hand.slide_up": "gentle_up",
    "articulation.left_hand.slide_down": "gentle_up",
    "articulation.left_hand.bend_quarter": "gentle_up",
    "articulation.left_hand.bend_half": "gentle_up",
    "articulation.left_hand.bend_whole": "gentle_up",
    "articulation.left_hand.bend_extended": "complexity_down",
    "articulation.left_hand.bend_release": "gentle_up",
    "articulation.left_hand.pre_bend": "complexity_down",
    "articulation.left_hand.pre_bend_release": "complexity_down",
    "articulation.left_hand.trill": "complexity_down",
    # Right hand
    "articulation.right_hand.palm_mute": "percussive_up",
    "articulation.right_hand.rake": "percussive_up",
    "articulation.right_hand.sweep": "complexity_down",
    "articulation.right_hand.tremolo_pick": "percussive_up",
    "articulation.right_hand.pick_slide": "complexity_down",
    "articulation.right_hand.tap": "complexity_down",
    # Modulation
    "articulation.modulation.vibrato_finger": "gentle_up",
    "articulation.modulation.vibrato_wide": "gentle_up",
    "articulation.modulation.vibrato_bar": "complexity_down",
    "articulation.modulation.bar_dip": "complexity_down",
    "articulation.modulation.bar_dive": "complexity_down",
    "articulation.modulation.bar_flutter": "complexity_down",
    "articulation.modulation.bar_release": "complexity_down",
    # Harmonics
    "articulation.harmonics.harmonic_natural": "complexity_down",
    "articulation.harmonics.harmonic_artificial": "complexity_down",
    "articulation.harmonics.harmonic_pinch": "complexity_down",
    "articulation.harmonics.harmonic_bent": "complexity_down",
    "articulation.harmonics.harmonic_bar": "complexity_down",
    # Percussive
    "articulation.percussive.ghost_note": "percussive_up",
    "articulation.percussive.muted_hit": "percussive_up",
    "articulation.percussive.percussive_slash": "percussive_up",
    # Sustain
    "articulation.sustain.let_ring": "sustain_down",
    "articulation.sustain.choke": "sustain_down",
}


# =============================================================================
# STYLE MULTIPLIERS (Page / Hendrix / SRV etc.)
# =============================================================================

STYLE_MULTIPLIERS: dict[RockStyle, dict[str, float]] = {
    RockStyle.NEUTRAL: {},
    RockStyle.ZEPPELIN: {
        "articulation.left_hand.slide_legato": 1.30,
        "articulation.left_hand.hammer_on": 1.20,
        "articulation.left_hand.pull_off": 1.15,
        "articulation.left_hand.bend_half": 1.05,
        "articulation.left_hand.bend_whole": 0.90,
        "articulation.right_hand.rake": 1.25,
        "articulation.right_hand.palm_mute": 1.05,
        "articulation.right_hand.tremolo_pick": 0.85,
        "articulation.modulation.vibrato_finger": 1.10,
        "articulation.modulation.vibrato_wide": 0.95,
        "articulation.harmonics.harmonic_natural": 1.15,
        "articulation.harmonics.harmonic_artificial": 1.10,
        "articulation.percussive.ghost_note": 1.15,
    },
    RockStyle.HENDRIX: {
        "articulation.left_hand.bend_quarter": 1.60,
        "articulation.left_hand.bend_half": 1.25,
        "articulation.left_hand.bend_release": 1.20,
        "articulation.left_hand.slide_legato": 1.10,
        "articulation.right_hand.rake": 1.35,
        "articulation.right_hand.palm_mute": 0.95,
        "articulation.modulation.vibrato_wide": 1.30,
        "articulation.modulation.bar_dip": 1.20,
        "articulation.modulation.bar_dive": 1.10,
        "articulation.percussive.ghost_note": 1.30,
    },
    RockStyle.SRV: {
        "articulation.left_hand.bend_half": 1.20,
        "articulation.left_hand.bend_whole": 1.35,
        "articulation.left_hand.bend_release": 1.30,
        "articulation.left_hand.pre_bend_release": 1.10,
        "articulation.right_hand.rake": 1.20,
        "articulation.right_hand.tremolo_pick": 1.25,
        "articulation.right_hand.palm_mute": 0.95,
        "articulation.modulation.vibrato_wide": 1.35,
        "articulation.modulation.vibrato_finger": 1.05,
        "articulation.harmonics.harmonic_artificial": 0.70,
        "articulation.harmonics.harmonic_bent": 0.70,
    },
}


# =============================================================================
# AGGRESSION / LEGATO MULTIPLIERS
# =============================================================================

# Tags affected by aggression multiplier
AGGRESSION_TAGS: set[str] = {
    "articulation.left_hand.bend_half",
    "articulation.left_hand.bend_whole",
    "articulation.left_hand.bend_release",
    "articulation.modulation.vibrato_wide",
    "articulation.right_hand.rake",
    "articulation.right_hand.tremolo_pick",
}

# Tags boosted by legato_bias
LEGATO_TAGS: set[str] = {
    "articulation.left_hand.hammer_on",
    "articulation.left_hand.pull_off",
    "articulation.left_hand.slide_legato",
}

# Tags reduced by legato_bias (anti-legato)
ANTI_LEGATO_TAGS: set[str] = {
    "articulation.right_hand.tremolo_pick",
    "articulation.right_hand.rake",
    "articulation.right_hand.palm_mute",
}


def aggression_multiplier(aggression: float) -> float:
    """Compute aggression multiplier: m = 0.85 + 0.60 * aggression -> [0.85, 1.45]"""
    return 0.85 + 0.60 * max(0.0, min(1.0, aggression))


def legato_multiplier(legato_bias: float) -> float:
    """Compute legato multiplier: m = 0.80 + 0.80 * legato_bias -> [0.80, 1.60]"""
    return 0.80 + 0.80 * max(0.0, min(1.0, legato_bias))


def anti_legato_multiplier(legato_bias: float) -> float:
    """Compute anti-legato multiplier: m = 1.20 - 0.50 * legato_bias -> [0.70, 1.20]"""
    return 1.20 - 0.50 * max(0.0, min(1.0, legato_bias))


# =============================================================================
# STYLE_ENERGY / LEADNESS KNOBS (single-knob feel changers)
# =============================================================================

# Tags affected by style_energy (right-hand aggression / rhythmic attack)
STYLE_ENERGY_TAGS: set[str] = {
    "articulation.right_hand.palm_mute",
    "articulation.right_hand.rake",
    "articulation.right_hand.tremolo_pick",
    "articulation.right_hand.pick_slide",
}

# Tags affected by leadness (lead/vocal expressiveness)
LEADNESS_TAGS: set[str] = {
    # Bends
    "articulation.left_hand.bend_quarter",
    "articulation.left_hand.bend_half",
    "articulation.left_hand.bend_whole",
    "articulation.left_hand.bend_extended",
    "articulation.left_hand.bend_release",
    "articulation.left_hand.pre_bend",
    "articulation.left_hand.pre_bend_release",
    # Vibrato
    "articulation.modulation.vibrato_finger",
    "articulation.modulation.vibrato_wide",
    "articulation.modulation.vibrato_bar",
    # Slides
    "articulation.left_hand.slide_legato",
    "articulation.left_hand.slide_up",
    "articulation.left_hand.slide_down",
}


def style_energy_multiplier(style_energy: float) -> float:
    """
    Compute style_energy multiplier for right-hand aggression tags.

    Parameters:
        style_energy: 0.0 (clean/soft) to 1.0 (aggressive/driving)

    Returns:
        Multiplier in range [0.50, 1.50]

    Formula: m = 0.50 + 1.00 * style_energy
    - style_energy=0.0 -> 0.50 (halves probability)
    - style_energy=0.5 -> 1.00 (neutral)
    - style_energy=1.0 -> 1.50 (50% boost)
    """
    return 0.50 + 1.00 * max(0.0, min(1.0, style_energy))


def leadness_multiplier(leadness: float) -> float:
    """
    Compute leadness multiplier for lead/vocal expressive tags.

    Parameters:
        leadness: 0.0 (rhythm/backing) to 1.0 (lead/melody)

    Returns:
        Multiplier in range [0.40, 1.60]

    Formula: m = 0.40 + 1.20 * leadness
    - leadness=0.0 -> 0.40 (rhythm guitar feel)
    - leadness=0.5 -> 1.00 (neutral)
    - leadness=1.0 -> 1.60 (60% boost for lead lines)
    """
    return 0.40 + 1.20 * max(0.0, min(1.0, leadness))


# =============================================================================
# CONSTRAINTS (dependencies, mutual exclusions)
# =============================================================================

@dataclass
class Dependency:
    """If `if_tag` is present, then at least one of `require_any` must also be present."""
    if_tag: str
    require_any: list[str]


@dataclass
class Forbid:
    """If `if_tag` is present, then none of `forbid_any` can be present."""
    if_tag: str
    forbid_any: list[str]


DEPENDENCIES: list[Dependency] = [
    Dependency(
        if_tag="articulation.left_hand.pre_bend",
        require_any=[
            "articulation.left_hand.bend_release",
            "articulation.left_hand.pre_bend_release",
        ],
    ),
    Dependency(
        if_tag="articulation.harmonics.harmonic_bent",
        require_any=[
            "articulation.left_hand.bend_half",
            "articulation.modulation.bar_dip",
            "articulation.modulation.bar_dive",
        ],
    ),
]

FORBIDS: list[Forbid] = [
    Forbid(
        if_tag="articulation.modulation.bar_dive",
        forbid_any=["articulation.sustain.let_ring"],
    ),
]

MUTUAL_EXCLUSIONS: list[tuple[str, str]] = [
    ("articulation.right_hand.sweep", "articulation.right_hand.rake"),
    ("articulation.modulation.vibrato_bar", "articulation.modulation.vibrato_finger"),
    ("articulation.percussive.muted_hit", "articulation.sustain.let_ring"),
]

# Soft limits for same tag repeats per bar
COOCCURRENCE_SOFT_LIMITS: dict[str, int] = {
    "articulation.percussive.ghost_note": 6,
    "articulation.left_hand.bend_half": 3,
    "articulation.right_hand.rake": 3,
}

PER_NOTE_MAX_TAGS: int = 2


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def get_tag_class(tag: str) -> str:
    """Extract the class from a tag (e.g., 'articulation.left_hand' from 'articulation.left_hand.hammer_on')."""
    parts = tag.split(".")
    if len(parts) >= 2:
        return ".".join(parts[:2])
    return tag


def is_tag_allowed(tag: str, difficulty: Difficulty) -> bool:
    """Check if a tag is allowed at the given difficulty level."""
    gates = DIFFICULTY_GATES.get(difficulty)
    if not gates:
        return True

    deny_list = gates.get("deny", [])
    if tag in deny_list:
        return False

    allow_list = gates.get("allow", [])
    if allow_list and tag not in allow_list:
        return False

    return True


def p_final(
    tag: str,
    style: RockStyle = RockStyle.NEUTRAL,
    difficulty: Difficulty = Difficulty.INTERMEDIATE,
    density: float = 0.5,
    aggression: float = 0.5,
    legato_bias: float = 0.5,
    style_energy: float = 0.5,
    leadness: float = 0.5,
) -> float:
    """
    Compute the final probability for a given articulation tag.

    Recipe:
    1. Start with base_p(tag)
    2. Multiply by style_multiplier(tag) default 1.0
    3. Multiply by curve_multiplier(tag, density)
    4. Multiply by aggression / legato multipliers when applicable
    5. Multiply by style_energy / leadness knobs when applicable
    6. Apply difficulty gate (deny => p=0, allow => unchanged)

    Parameters:
        tag: Full articulation tag (e.g., "articulation.left_hand.bend_half")
        style: Rock style (NEUTRAL, ZEPPELIN, HENDRIX, SRV)
        difficulty: Difficulty level (BEGINNER, INTERMEDIATE, ADVANCED)
        density: Note density 0.0 to 1.0
        aggression: Aggression bias 0.0 to 1.0
        legato_bias: Legato bias 0.0 to 1.0
        style_energy: Right-hand aggression 0.0 (clean) to 1.0 (driving)
        leadness: Lead expressiveness 0.0 (rhythm) to 1.0 (lead)

    Returns:
        Final probability (0.0 to ~0.3 typically)
    """
    # 1. Base probability
    if tag not in BASE_PROBABILITIES:
        return 0.0
    base_p = BASE_PROBABILITIES[tag]["p"]

    # 2. Style multiplier
    style_mults = STYLE_MULTIPLIERS.get(style, {})
    style_m = style_mults.get(tag, 1.0)

    # 3. Curve multiplier (density-based)
    curve_name = CURVE_BINDINGS.get(tag, "gentle_up")
    curve_m = curve_multiplier(curve_name, density)

    # 4. Aggression / legato multipliers
    extra_m = 1.0
    if tag in AGGRESSION_TAGS:
        extra_m *= aggression_multiplier(aggression)
    if tag in LEGATO_TAGS:
        extra_m *= legato_multiplier(legato_bias)
    if tag in ANTI_LEGATO_TAGS:
        extra_m *= anti_legato_multiplier(legato_bias)

    # 5. Style_energy / leadness knobs (single-knob feel changers)
    if tag in STYLE_ENERGY_TAGS:
        extra_m *= style_energy_multiplier(style_energy)
    if tag in LEADNESS_TAGS:
        extra_m *= leadness_multiplier(leadness)

    # 6. Difficulty gate
    if not is_tag_allowed(tag, difficulty):
        return 0.0

    return base_p * style_m * curve_m * extra_m


def enforce_constraints(tags: list[str]) -> list[str]:
    """
    Enforce dependency and mutual exclusion constraints on a list of tags.
    Drops lowest-priority (last-added) tags to fix violations.

    Parameters:
        tags: List of selected tags

    Returns:
        Cleaned list of tags
    """
    result = tags.copy()

    # 1. Check mutual exclusions
    for tag_a, tag_b in MUTUAL_EXCLUSIONS:
        if tag_a in result and tag_b in result:
            # Drop the one that appears later
            if result.index(tag_a) > result.index(tag_b):
                result.remove(tag_a)
            else:
                result.remove(tag_b)

    # 2. Check forbid rules
    for forbid in FORBIDS:
        if forbid.if_tag in result:
            for forbidden in forbid.forbid_any:
                if forbidden in result:
                    result.remove(forbidden)

    # 3. Check dependencies (drop the dependent tag if requirement not met)
    for dep in DEPENDENCIES:
        if dep.if_tag in result:
            has_required = any(req in result for req in dep.require_any)
            if not has_required:
                result.remove(dep.if_tag)

    return result


def sample_tags_for_bar(
    note_count: int,
    difficulty: Difficulty = Difficulty.INTERMEDIATE,
    style: RockStyle = RockStyle.NEUTRAL,
    density: float = 0.5,
    aggression: float = 0.5,
    legato_bias: float = 0.5,
    style_energy: float = 0.5,
    leadness: float = 0.5,
    seed: int | None = None,
) -> list[str]:
    """
    Sample articulation tags for a bar of music.

    Parameters:
        note_count: Number of notes in the bar (affects sampling opportunities)
        difficulty: Difficulty level
        style: Rock style
        density: Note density 0.0 to 1.0
        aggression: Aggression bias 0.0 to 1.0
        legato_bias: Legato bias 0.0 to 1.0
        style_energy: Right-hand aggression 0.0 (clean) to 1.0 (driving)
        leadness: Lead expressiveness 0.0 (rhythm) to 1.0 (lead)
        seed: Random seed for reproducibility

    Returns:
        List of selected articulation tags
    """
    if seed is not None:
        random.seed(seed)

    # Get budgets for this difficulty
    total_budget = BUDGETS_PER_BAR[difficulty]
    class_budgets = BUDGETS_PER_BAR_BY_CLASS[difficulty].copy()

    # Track usage
    selected: list[str] = []
    class_usage: dict[str, int] = {k: 0 for k in class_budgets}
    tag_usage: dict[str, int] = {}

    # All candidate tags
    all_tags = list(BASE_PROBABILITIES.keys())
    random.shuffle(all_tags)

    # Separate note-scope and bar-scope tags
    note_scope_tags = [t for t in all_tags if BASE_PROBABILITIES[t].get("scope") == "note"]
    bar_scope_tags = [t for t in all_tags if BASE_PROBABILITIES[t].get("scope") == "bar"]

    # Sample bar-scope tags (once per bar)
    for tag in bar_scope_tags:
        if len(selected) >= total_budget["max"]:
            break

        tag_class = get_tag_class(tag)
        if class_usage.get(tag_class, 0) >= class_budgets.get(tag_class, 0):
            continue

        prob = p_final(tag, style, difficulty, density, aggression, legato_bias, style_energy, leadness)
        if random.random() < prob:
            selected.append(tag)
            class_usage[tag_class] = class_usage.get(tag_class, 0) + 1
            tag_usage[tag] = tag_usage.get(tag, 0) + 1

    # Sample note-scope tags (opportunity per note)
    for _ in range(note_count):
        if len(selected) >= total_budget["max"]:
            break

        note_tags = 0
        for tag in note_scope_tags:
            if note_tags >= PER_NOTE_MAX_TAGS:
                break
            if len(selected) >= total_budget["max"]:
                break

            tag_class = get_tag_class(tag)
            if class_usage.get(tag_class, 0) >= class_budgets.get(tag_class, 0):
                continue

            # Check soft limits
            soft_limit = COOCCURRENCE_SOFT_LIMITS.get(tag.split(".")[-1])
            if soft_limit and tag_usage.get(tag, 0) >= soft_limit:
                continue

            prob = p_final(tag, style, difficulty, density, aggression, legato_bias, style_energy, leadness)
            if random.random() < prob:
                selected.append(tag)
                class_usage[tag_class] = class_usage.get(tag_class, 0) + 1
                tag_usage[tag] = tag_usage.get(tag, 0) + 1
                note_tags += 1

    # Enforce constraints
    selected = enforce_constraints(selected)

    return selected


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "Difficulty",
    "RockStyle",
    # Core functions
    "curve_multiplier",
    "p_final",
    "sample_tags_for_bar",
    "enforce_constraints",
    "is_tag_allowed",
    # Multiplier functions
    "aggression_multiplier",
    "legato_multiplier",
    "anti_legato_multiplier",
    "style_energy_multiplier",
    "leadness_multiplier",
    # Data (for inspection/extension)
    "BASE_PROBABILITIES",
    "BUDGETS_PER_BAR",
    "BUDGETS_PER_BAR_BY_CLASS",
    "DIFFICULTY_GATES",
    "CURVES",
    "CURVE_BINDINGS",
    "STYLE_MULTIPLIERS",
    "STYLE_ENERGY_TAGS",
    "LEADNESS_TAGS",
    "DEPENDENCIES",
    "FORBIDS",
    "MUTUAL_EXCLUSIONS",
]
