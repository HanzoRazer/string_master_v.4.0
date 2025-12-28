"""
Accompaniment style patterns (swing, latin, rock, etc.)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class HitSpec:
    """Specification for a single comping hit."""
    beat: float  # Beat position in the bar (0.0 = downbeat)
    length_beats: float  # Duration in beats
    velocity: int  # MIDI velocity (0-127)


@dataclass
class StylePattern:
    """
    Defines a complete accompaniment style.
    
    Attributes:
        name: Style name
        comp_hits: List of comping chord hits per bar
        bass_pattern: List of (beat, duration, velocity) for bass notes per bar
    """
    name: str
    comp_hits: List[HitSpec]
    bass_pattern: List[Tuple[float, float, int]]  # (beat, duration, velocity)


# Swing / Jazz comping patterns
SWING_BASIC = StylePattern(
    name="swing_basic",
    comp_hits=[
        HitSpec(beat=0.0, length_beats=0.5, velocity=80),   # Downbeat
        HitSpec(beat=2.0, length_beats=0.5, velocity=75),   # Beat 3
    ],
    bass_pattern=[
        (0.0, 0.8, 90),  # Root on 1
        (2.0, 0.8, 85),  # Root on 3
    ],
)

SWING_UPBEAT = StylePattern(
    name="swing_upbeat",
    comp_hits=[
        HitSpec(beat=0.5, length_beats=0.4, velocity=70),   # & of 1
        HitSpec(beat=2.5, length_beats=0.4, velocity=75),   # & of 3
    ],
    bass_pattern=[
        (0.0, 0.8, 95),  # Root on 1
        (2.0, 0.8, 90),  # Root on 3
    ],
)

# Bossa Nova pattern
BOSSA_NOVA = StylePattern(
    name="bossa_nova",
    comp_hits=[
        HitSpec(beat=0.0, length_beats=0.3, velocity=70),
        HitSpec(beat=1.5, length_beats=0.3, velocity=65),
        HitSpec(beat=2.5, length_beats=0.3, velocity=68),
    ],
    bass_pattern=[
        (0.0, 0.7, 85),
        (1.0, 0.7, 80),
        (2.0, 0.7, 85),
        (3.0, 0.7, 80),
    ],
)

# Rock / Pop pattern
ROCK_BASIC = StylePattern(
    name="rock_basic",
    comp_hits=[
        HitSpec(beat=0.0, length_beats=0.8, velocity=90),
        HitSpec(beat=1.0, length_beats=0.8, velocity=85),
        HitSpec(beat=2.0, length_beats=0.8, velocity=90),
        HitSpec(beat=3.0, length_beats=0.8, velocity=85),
    ],
    bass_pattern=[
        (0.0, 0.9, 100),  # Strong root
        (2.0, 0.9, 95),
    ],
)

# Ballad pattern
BALLAD = StylePattern(
    name="ballad",
    comp_hits=[
        HitSpec(beat=0.0, length_beats=1.5, velocity=60),
        HitSpec(beat=2.0, length_beats=1.5, velocity=58),
    ],
    bass_pattern=[
        (0.0, 1.8, 70),  # Sustained bass
    ],
)

# Walking bass jazz pattern
WALKING_BASS = StylePattern(
    name="walking_bass",
    comp_hits=[
        HitSpec(beat=1.0, length_beats=0.4, velocity=75),
        HitSpec(beat=3.0, length_beats=0.4, velocity=72),
    ],
    bass_pattern=[
        (0.0, 0.9, 90),  # Root
        (1.0, 0.9, 85),  # 5th or passing tone
        (2.0, 0.9, 88),  # 3rd
        (3.0, 0.9, 87),  # Approach tone
    ],
)

# Registry of all available styles
STYLE_REGISTRY = {
    "swing_basic": SWING_BASIC,
    "swing_upbeat": SWING_UPBEAT,
    "bossa_nova": BOSSA_NOVA,
    "rock_basic": ROCK_BASIC,
    "ballad": BALLAD,
    "walking_bass": WALKING_BASS,
}


def get_style(name: str) -> StylePattern:
    """Get a style pattern by name."""
    if name not in STYLE_REGISTRY:
        raise ValueError(f"Unknown style: {name}. Available: {list(STYLE_REGISTRY.keys())}")
    return STYLE_REGISTRY[name]
