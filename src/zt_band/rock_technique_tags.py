"""
Rock technique tag layer for legend parsing and section-aware articulation sampling.

This module provides:
1. Canonical technique tags (flat strings for serialization)
2. Legend symbol → tag mapping (for PDF/OCR parsing)
3. Section-position-aware probability curves
4. Event attachment API for post-processing generated etudes

Complements rock_articulations.py:
- rock_articulations.py: hierarchical tags, style multipliers, difficulty gates, budgets
- rock_technique_tags.py: flat tags, legend parsing, section_pos curves, event attachment

Usage:
    from zt_band.rock_technique_tags import (
        normalize_legend_tokens,
        probability_for_tag,
        sample_tags_for_event,
        attach_event_tags,
        TECHNIQUE_TAGS,
        SYMBOL_TO_TAG,
    )

    # Parse legend symbols from PDF/OCR
    tags = normalize_legend_tokens(["H", "P.M.", "1/2", "vib"])
    # -> ["hammer_on", "palm_mute", "bend_half", "vibrato"]

    # Attach technique tags to generated events
    events = attach_event_tags(events, density=2, seed=42)
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Optional


# =============================================================================
# CANONICAL TECHNIQUE TAGS (flat strings for easy serialization)
# =============================================================================

TECHNIQUE_TAGS = [
    # left hand
    "hammer_on",
    "pull_off",
    "slide_picked",
    "slide_legato",
    "bend_quarter",
    "bend_half",
    "bend_whole",
    "bend_extended",
    "bend_release",
    "bend_prebend",
    "unison_bend",

    # right hand / articulation
    "palm_mute",
    "rake",
    "sweep",
    "tremolo_picking",
    "pick_slide",
    "vibrato",
    "vibrato_bar",
    "bar_dive",
    "bar_dip",
    "bar_flutter",

    # harmonics / tapping / percussive
    "natural_harmonic",
    "artificial_harmonic",
    "tapping_right_hand",
    "percussive_tone",
    "ghost_note",

    # sustain treatment
    "let_ring",
]


# =============================================================================
# LEGEND SYMBOL → TAG MAPPING (for PDF/OCR parsing)
# =============================================================================

SYMBOL_TO_TAG = {
    # basic legato
    "H": "hammer_on",
    "h": "hammer_on",
    "P": "pull_off",
    "p": "pull_off",

    # slides
    "s": "slide_legato",
    "S": "slide_picked",
    "/": "slide_picked",
    "\\": "slide_picked",

    # bends
    "1/4": "bend_quarter",
    "1/2": "bend_half",
    "full": "bend_whole",
    "whole": "bend_whole",
    "ext": "bend_extended",
    "pre": "bend_prebend",
    "release": "bend_release",
    "unison": "unison_bend",

    # muting / feel
    "P.M.": "palm_mute",
    "PM": "palm_mute",
    "let ring": "let_ring",
    "LR": "let_ring",

    # pick articulation
    "rake": "rake",
    "sweep": "sweep",
    "trem": "tremolo_picking",
    "pick slide": "pick_slide",

    # vibrato
    "vib": "vibrato",
    "vib.": "vibrato",
    "vib bar": "vibrato_bar",
    "bar vib": "vibrato_bar",

    # whammy / bar effects
    "dive": "bar_dive",
    "dip": "bar_dip",
    "flutter": "bar_flutter",

    # harmonics / tapping
    "harm": "natural_harmonic",
    "harm.": "natural_harmonic",
    "A.H.": "artificial_harmonic",
    "AH": "artificial_harmonic",
    "tap": "tapping_right_hand",

    # percussive / "no pitch"
    "x": "ghost_note",
    "X": "ghost_note",
    "perc": "percussive_tone",
}


# =============================================================================
# PROBABILITY CURVE PRIMITIVES
# =============================================================================

def clamp01(x: float) -> float:
    """Clamp value to [0.0, 1.0]."""
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def ramp_up(section_pos: float, power: float = 1.0) -> float:
    """Rising curve 0..1, steeper with higher power."""
    return clamp01(section_pos) ** power


def bell(section_pos: float, center: float = 0.5, width: float = 0.22) -> float:
    """Gaussian bump around center (0..1 normalized)."""
    p = clamp01(section_pos)
    return math.exp(-((p - center) ** 2) / (2 * (width ** 2)))


def logistic(x: float, k: float = 10.0, x0: float = 0.5) -> float:
    """S-curve from 0 to 1."""
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))


# =============================================================================
# TAG PROBABILITY PROFILES
# =============================================================================

@dataclass(frozen=True)
class TagProfile:
    """
    Probability profile for a technique tag.

    Attributes:
        base: Baseline probability at density=0
        per_density: Added probability per density step (0..3)
        shape: Optional multiplier function f(section_pos) -> [0..2]
        max_p: Safety cap on final probability
    """
    base: float
    per_density: float
    shape: Optional[Callable[[float], float]] = None
    max_p: float = 0.85


def _shape_none(_: float) -> float:
    """Default shape: constant 1.0."""
    return 1.0


DEFAULT_PROFILES: dict[str, TagProfile] = {
    # Very common rock vocabulary
    "hammer_on": TagProfile(
        base=0.02, per_density=0.06,
        shape=lambda p: 0.7 + 0.6 * bell(p, 0.45, 0.25)
    ),
    "pull_off": TagProfile(
        base=0.02, per_density=0.06,
        shape=lambda p: 0.7 + 0.6 * bell(p, 0.55, 0.25)
    ),
    "slide_legato": TagProfile(
        base=0.01, per_density=0.05,
        shape=lambda p: 0.8 + 0.4 * bell(p, 0.50, 0.30)
    ),
    "slide_picked": TagProfile(
        base=0.01, per_density=0.04,
        shape=lambda p: 0.8 + 0.4 * bell(p, 0.50, 0.30)
    ),

    # Bends + vibrato (more "cadential / vocal" — rise toward end)
    "bend_quarter": TagProfile(
        base=0.00, per_density=0.01,
        shape=lambda p: 0.6 + 0.8 * ramp_up(p, 2.0)
    ),
    "bend_half": TagProfile(
        base=0.01, per_density=0.05,
        shape=lambda p: 0.6 + 0.9 * ramp_up(p, 1.6)
    ),
    "bend_whole": TagProfile(
        base=0.00, per_density=0.04,
        shape=lambda p: 0.5 + 1.0 * ramp_up(p, 1.7)
    ),
    "bend_release": TagProfile(
        base=0.00, per_density=0.02,
        shape=lambda p: 0.6 + 0.8 * ramp_up(p, 1.2)
    ),
    "bend_prebend": TagProfile(
        base=0.00, per_density=0.01,
        shape=lambda p: 0.4 + 0.9 * ramp_up(p, 2.0)
    ),
    "bend_extended": TagProfile(
        base=0.00, per_density=0.01,
        shape=lambda p: 0.3 + 0.9 * ramp_up(p, 2.2)
    ),
    "unison_bend": TagProfile(
        base=0.00, per_density=0.01,
        shape=lambda p: 0.3 + 0.9 * ramp_up(p, 2.0)
    ),
    "vibrato": TagProfile(
        base=0.03, per_density=0.07,
        shape=lambda p: 0.7 + 0.8 * ramp_up(p, 1.4)
    ),
    "vibrato_bar": TagProfile(
        base=0.00, per_density=0.01,
        shape=lambda p: 0.3 + 0.8 * ramp_up(p, 1.7)
    ),

    # Riff feel (palm mute clusters in middle/driving sections)
    "palm_mute": TagProfile(
        base=0.05, per_density=0.10,
        shape=lambda p: 0.6 + 0.8 * bell(p, 0.45, 0.22),
        max_p=0.90
    ),
    "tremolo_picking": TagProfile(
        base=0.00, per_density=0.02,
        shape=lambda p: 0.4 + 0.8 * bell(p, 0.55, 0.18)
    ),
    "pick_slide": TagProfile(
        base=0.00, per_density=0.01,
        shape=lambda p: 0.3 + 0.7 * ramp_up(p, 2.5)
    ),
    "rake": TagProfile(
        base=0.00, per_density=0.02,
        shape=lambda p: 0.4 + 0.7 * bell(p, 0.60, 0.22)
    ),
    "sweep": TagProfile(
        base=0.00, per_density=0.01,
        shape=lambda p: 0.3 + 0.6 * bell(p, 0.60, 0.18)
    ),

    # "Color" devices (rare unless explicitly pushed)
    "natural_harmonic": TagProfile(
        base=0.00, per_density=0.01,
        shape=lambda p: 0.3 + 0.7 * ramp_up(p, 3.0),
        max_p=0.25
    ),
    "artificial_harmonic": TagProfile(
        base=0.00, per_density=0.005,
        shape=lambda p: 0.2 + 0.8 * ramp_up(p, 3.0),
        max_p=0.15
    ),
    "tapping_right_hand": TagProfile(
        base=0.00, per_density=0.005,
        shape=lambda p: 0.2 + 0.8 * ramp_up(p, 3.0),
        max_p=0.12
    ),

    # Percussive / no pitch
    "ghost_note": TagProfile(
        base=0.00, per_density=0.02,
        shape=lambda p: 0.7 + 0.6 * bell(p, 0.40, 0.25),
        max_p=0.35
    ),
    "percussive_tone": TagProfile(
        base=0.00, per_density=0.01,
        shape=lambda p: 0.6 + 0.6 * bell(p, 0.40, 0.22),
        max_p=0.25
    ),

    # Sustain treatment
    "let_ring": TagProfile(
        base=0.01, per_density=0.02,
        shape=lambda p: 0.7 + 0.8 * ramp_up(p, 1.2),
        max_p=0.35
    ),

    # Whammy specials (very rare by default)
    "bar_dive": TagProfile(
        base=0.00, per_density=0.003,
        shape=lambda p: 0.2 + 0.9 * ramp_up(p, 3.0),
        max_p=0.08
    ),
    "bar_dip": TagProfile(
        base=0.00, per_density=0.004,
        shape=lambda p: 0.2 + 0.9 * ramp_up(p, 2.6),
        max_p=0.10
    ),
    "bar_flutter": TagProfile(
        base=0.00, per_density=0.002,
        shape=lambda p: 0.2 + 0.9 * ramp_up(p, 3.0),
        max_p=0.06
    ),
}


# =============================================================================
# PUBLIC API
# =============================================================================

def normalize_legend_tokens(tokens: Iterable[str]) -> list[str]:
    """
    Convert raw legend tokens (OCR fragments or human-entered) into canonical tags.

    Strategy: longest-token-first substring match.

    Parameters:
        tokens: Iterable of raw string tokens (e.g., ["H", "P.M.", "1/2"])

    Returns:
        List of canonical tag strings, unique and order-preserved

    Example:
        >>> normalize_legend_tokens(["H", "P.M.", "1/2", "vib"])
        ['hammer_on', 'palm_mute', 'bend_half', 'vibrato']
    """
    raw = [t.strip() for t in tokens if t and t.strip()]
    # Sort by length desc so "let ring" hits before "ring"
    raw.sort(key=len, reverse=True)

    found: list[str] = []
    for t in raw:
        # Exact match first
        if t in SYMBOL_TO_TAG:
            found.append(SYMBOL_TO_TAG[t])
            continue

        # Case-insensitive / substring heuristics
        tl = t.lower()
        for sym, tag in SYMBOL_TO_TAG.items():
            if sym.lower() in tl:
                found.append(tag)
                break

    # Unique preserving order
    seen: set[str] = set()
    out: list[str] = []
    for tag in found:
        if tag not in seen:
            seen.add(tag)
            out.append(tag)
    return out


def probability_for_tag(
    tag: str,
    density: int,
    section_pos: float = 0.5,
    profiles: dict[str, TagProfile] | None = None,
) -> float:
    """
    Compute p(tag) given density (0..3) and section position (0..1).

    Parameters:
        tag: Canonical technique tag
        density: Density level 0 (sparse) to 3 (dense)
        section_pos: Position in phrase 0.0 (start) to 1.0 (end)
        profiles: Tag profiles dict (defaults to DEFAULT_PROFILES)

    Returns:
        Final probability capped by max_p

    Example:
        >>> probability_for_tag("bend_half", density=2, section_pos=0.8)
        0.156  # Higher at end of phrase due to ramp_up shape
    """
    if profiles is None:
        profiles = DEFAULT_PROFILES

    d = max(0, min(3, int(density)))
    prof = profiles.get(tag)
    if prof is None:
        return 0.0

    shape = prof.shape if prof.shape is not None else _shape_none
    p = (prof.base + prof.per_density * d) * shape(clamp01(section_pos))
    return max(0.0, min(prof.max_p, p))


def sample_tags_for_event(
    density: int,
    section_pos: float,
    rng: random.Random,
    allow: set[str] | None = None,
    deny: set[str] | None = None,
    profiles: dict[str, TagProfile] | None = None,
    max_tags: int = 2,
) -> list[str]:
    """
    Sample 0..max_tags technique tags for one note/event.

    Uses independent Bernoulli sampling then trims to max_tags by highest probability.

    Parameters:
        density: Density level 0..3
        section_pos: Position in phrase 0.0..1.0
        rng: Random instance for reproducibility
        allow: Set of allowed tags (None = all)
        deny: Set of denied tags (None = none)
        profiles: Tag profiles dict
        max_tags: Maximum tags per event

    Returns:
        List of selected tag strings (0 to max_tags)
    """
    if profiles is None:
        profiles = DEFAULT_PROFILES

    allow_set = allow if allow is not None else set(profiles.keys())
    deny_set = deny if deny is not None else set()

    candidates: list[tuple[str, float]] = []
    for tag in profiles.keys():
        if tag not in allow_set or tag in deny_set:
            continue
        p = probability_for_tag(tag, density=density, section_pos=section_pos, profiles=profiles)
        if p <= 0:
            continue
        if rng.random() < p:
            candidates.append((tag, p))

    # Keep the most "intended" ones if we got too many
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [t for (t, _) in candidates[:max_tags]]


def attach_event_tags(
    events: list[dict],
    density: int,
    seed: int = 0,
    profiles: dict[str, TagProfile] | None = None,
    allow: set[str] | None = None,
    deny: set[str] | None = None,
    max_tags_per_event: int = 2,
) -> list[dict]:
    """
    Attach technique_tags to a list of engine events.

    Mutates/copies events by adding event["technique_tags"] = [...].
    Uses normalized section_pos across the event list.

    Parameters:
        events: List of event dicts (with at least midi/start/dur)
        density: Density level 0..3
        seed: Random seed for reproducibility
        profiles: Tag profiles dict
        allow: Set of allowed tags
        deny: Set of denied tags
        max_tags_per_event: Max tags per event

    Returns:
        New list of event dicts with technique_tags added

    Example:
        >>> events = [{"midi": 64, "start": 0, "dur": 480}, ...]
        >>> events = attach_event_tags(events, density=2, seed=42)
        >>> events[0]
        {"midi": 64, "start": 0, "dur": 480, "technique_tags": ["hammer_on"]}
    """
    if profiles is None:
        profiles = DEFAULT_PROFILES

    rng = random.Random(seed)
    n = max(1, len(events))
    out: list[dict] = []

    for i, ev in enumerate(events):
        section_pos = 0.0 if n == 1 else (i / (n - 1))
        tags = sample_tags_for_event(
            density=density,
            section_pos=section_pos,
            rng=rng,
            allow=allow,
            deny=deny,
            profiles=profiles,
            max_tags=max_tags_per_event,
        )
        ev2 = dict(ev)
        if tags:
            ev2["technique_tags"] = tags
        out.append(ev2)

    return out


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Tag lists
    "TECHNIQUE_TAGS",
    "SYMBOL_TO_TAG",
    # Curve primitives
    "clamp01",
    "ramp_up",
    "bell",
    "logistic",
    # Profile class
    "TagProfile",
    "DEFAULT_PROFILES",
    # Public API
    "normalize_legend_tokens",
    "probability_for_tag",
    "sample_tags_for_event",
    "attach_event_tags",
]
