"""
Flamenco accompaniment patterns with Phrygian/Andalusian alignment.

These patterns are designed for flamenco styles based on the Andalusian cadence:
    iv → ♭III → ♭II → I(♭2)

Key concepts:
- Compás: rhythmic cycle (12-beat for soleá/bulería, 4-beat for tangos)
- Rasgueado: strummed patterns
- Palmas: handclaps (accents)
- Phrygian gravity: ♭2 → 1 resolution (not V → I)

Styles by position:
- Por Medio (A): most common, 5th string bass
- Por Arriba (E): open position, 6th string bass
- Taranta (F#): free time, mining songs
- Granaina (B): free time, Granada style

Reference: docs/Por Medio_A flamenco_Andalusian cadence.txt
"""
from __future__ import annotations

from .patterns import CompEventSpec, StylePattern


# ============================================================================
# FLAMENCO 4/4 PATTERNS (Tangos, Tientos, Rumba)
# ============================================================================

# Tangos básico (4/4, syncopated)
# Strong accents on 1 and 3, anticipation into next bar
TANGOS_BASIC = StylePattern(
    name="tangos_basic",
    description="Flamenco tangos: 4/4 with Phrygian color, syncopated rasgueado.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=90),    # 1 (STRONG)
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=70),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=75),    # 2
        CompEventSpec(beat=2.0, length_beats=0.5, velocity=85),    # 3 (accent)
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=70),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=75),   # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=80),   # & of 4 (anticipation)
    ],
    bass_pattern=[
        (0.0, 1.0, 85),     # beat 1 (root)
        (2.0, 0.75, 80),    # beat 3
        (3.5, 0.5, 75),     # & of 4 (walking into next chord)
    ],
    clave_pattern="phrygian_4",
    clave_strict=False,
)


# Tientos (slow tangos, 4/4)
TIENTOS_BASIC = StylePattern(
    name="tientos_basic",
    description="Flamenco tientos: slow tangos with expressive rubato feel.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=1.0, velocity=85),    # 1 (held)
        CompEventSpec(beat=1.5, length_beats=0.5, velocity=70),    # & of 2
        CompEventSpec(beat=2.0, length_beats=1.0, velocity=80),    # 3 (held)
        CompEventSpec(beat=3.5, length_beats=0.5, velocity=75),    # & of 4
    ],
    bass_pattern=[
        (0.0, 1.5, 80),     # beat 1 (long)
        (2.0, 1.5, 75),     # beat 3 (long)
    ],
    clave_pattern="phrygian_4",
    clave_strict=False,
)


# Rumba flamenca (4/4, more driving)
RUMBA_FLAMENCA = StylePattern(
    name="rumba_flamenca",
    description="Rumba flamenca: driving 4/4 with strong backbeat.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=85),    # 1
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=70),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=90),    # 2 (backbeat)
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=70),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.5, velocity=85),    # 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=70),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=90),    # 4 (backbeat)
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=75),   # & of 4
    ],
    bass_pattern=[
        (0.0, 0.75, 85),    # beat 1
        (1.0, 0.75, 80),    # beat 2
        (2.0, 0.75, 85),    # beat 3
        (3.0, 0.75, 80),    # beat 4
    ],
    clave_pattern=None,  # rumba is backbeat-driven
    clave_strict=False,
)


# ============================================================================
# FLAMENCO 12-BEAT PATTERNS (Soleá, Bulería - simplified to 4/4 feel)
# ============================================================================
# Note: True soleá/bulería use 12-beat compás. These are 4/4 approximations
# that capture the accent pattern for engine compatibility.

# Soleá feel (4/4 approximation)
# True soleá accents: 3, 6, 8, 10, 12 in 12-beat cycle
# 4/4 approximation: emphasize beats 1 and 3 with syncopation
SOLEA_FEEL = StylePattern(
    name="solea_feel",
    description="Soleá feel: 4/4 approximation of 12-beat flamenco compás.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.75, velocity=90),   # 1 (STRONG)
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=70),    # 2 (ghost)
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=80),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.75, velocity=85),   # 3 (accent)
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=70),   # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=80),   # & of 4 (cierre)
    ],
    bass_pattern=[
        (0.0, 1.0, 85),     # beat 1
        (2.0, 1.0, 80),     # beat 3
    ],
    clave_pattern="solea_feel",
    clave_strict=False,
)


# Bulería feel (4/4 approximation, faster)
BULERIA_FEEL = StylePattern(
    name="buleria_feel",
    description="Bulería feel: fast 4/4 approximation with driving syncopation.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=90),   # 1
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=75),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=85),   # & of 2 (accent)
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=90),   # 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=80),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=75),   # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=85),   # & of 4
    ],
    bass_pattern=[
        (0.0, 0.5, 90),     # beat 1
        (1.5, 0.5, 85),     # & of 2
        (2.0, 0.5, 85),     # beat 3
        (3.5, 0.5, 80),     # & of 4
    ],
    clave_pattern="buleria_feel",
    clave_strict=False,
)


# ============================================================================
# FREE TIME PATTERNS (Taranta, Granaina - rubato, no strict meter)
# ============================================================================

# Taranta/Granaina (sparse, free feel)
TARANTA_FREE = StylePattern(
    name="taranta_free",
    description="Taranta/Granaina: sparse, rubato feel for libre styles.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=2.0, velocity=80),    # 1 (long hold)
        CompEventSpec(beat=2.0, length_beats=1.5, velocity=75),    # 3 (re-articulate)
        CompEventSpec(beat=3.75, length_beats=0.25, velocity=85),  # pickup into next
    ],
    bass_pattern=[
        (0.0, 3.0, 75),     # very long bass note
    ],
    clave_pattern=None,  # free time
    clave_strict=False,
)


# ============================================================================
# ANDALUSIAN CADENCE ACCOMPANIMENT
# ============================================================================

# Generic Andalusian cadence comp (iv → ♭III → ♭II → I)
# Designed for the descending bass motion
ANDALUSIAN_COMP = StylePattern(
    name="andalusian_comp",
    description="Andalusian cadence comping: iv → ♭III → ♭II → I Phrygian pattern.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=85),    # 1 (chord hit)
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=70),   # & of 1 (rasgueado)
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=80),    # 2
        CompEventSpec(beat=2.0, length_beats=0.5, velocity=85),    # 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=70),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=80),    # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=75),   # & of 4 (anticipation)
    ],
    bass_pattern=[
        (0.0, 0.75, 85),    # beat 1 (root of current chord)
        (2.0, 0.75, 80),    # beat 3
        (3.5, 0.5, 75),     # & of 4 (walking bass into next)
    ],
    clave_pattern="andalusian",
    clave_strict=False,
)


# Andalusian cadence bass only
ANDALUSIAN_BASS = StylePattern(
    name="andalusian_bass",
    description="Andalusian cadence bass: descending tetrachord pattern.",
    comp_hits=[],
    bass_pattern=[
        (0.0, 1.0, 85),     # beat 1 (root)
        (2.0, 0.75, 80),    # beat 3
        (3.5, 0.5, 75),     # & of 4 (step down)
    ],
    clave_pattern="andalusian",
    clave_strict=False,
)


# ============================================================================
# REGISTRY EXPORT
# ============================================================================

FLAMENCO_PATTERNS = {
    # 4/4 forms
    "tangos_basic": TANGOS_BASIC,
    "tientos_basic": TIENTOS_BASIC,
    "rumba_flamenca": RUMBA_FLAMENCA,
    # 12-beat approximations
    "solea_feel": SOLEA_FEEL,
    "buleria_feel": BULERIA_FEEL,
    # Free time
    "taranta_free": TARANTA_FREE,
    # Andalusian cadence
    "andalusian_comp": ANDALUSIAN_COMP,
    "andalusian_bass": ANDALUSIAN_BASS,
}
