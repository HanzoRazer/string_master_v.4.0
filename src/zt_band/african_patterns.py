"""
African accompaniment patterns with bell/timeline alignment.

These patterns cover major African popular music styles:
- Soukous (Congolese rumba / "African rumba")
- Afrobeat (Nigerian, Fela Kuti style)
- Highlife (Ghanaian)
- Mbalax (Senegalese)
- Jùjú (Nigerian Yoruba)

Key concepts:
- Standard bell pattern: the African equivalent of clave
  12/8: X.X.XX.X.XX. (standard pattern / "clave")
  4/4:  X..X..X.X..X..X. (16th-note grid)
- Timeline: organizing rhythmic key (like clave in Afro-Cuban)
- Cross-rhythm: multiple rhythmic layers interlocking

Reference: docs/AFRICAN_RHYTHM_TAXONOMY.md (to be created)
"""
from __future__ import annotations

from .patterns import CompEventSpec, StylePattern


# ============================================================================
# SOUKOUS / CONGOLESE RUMBA PATTERNS
# ============================================================================

# Soukous basic (Congolese rumba - medium tempo)
# Bell pattern in 4/4: hits on 1, &1, 2, &2, 3, &3, 4 (adapted from 12/8 standard)
# Bass: syncopated root-fifth movement
SOUKOUS_BASIC = StylePattern(
    name="soukous_basic",
    description="Congolese soukous: rolling guitar feel, syncopated bass (standard bell).",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=85),   # 1
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=75),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=80),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=70),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=85),   # 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=75),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=80),   # 4
    ],
    bass_pattern=[
        (0.0, 0.75, 85),    # beat 1 (root)
        (1.5, 0.5, 80),     # & of 2 (fifth)
        (2.5, 0.5, 75),     # & of 3 (root)
        (3.5, 0.5, 80),     # & of 4 (pickup)
    ],
    clave_pattern="standard_bell",
    clave_strict=False,
)


# Soukous sebene (fast guitar-driven section)
# More driving, 16th-note guitar patterns
SOUKOUS_SEBENE = StylePattern(
    name="soukous_sebene",
    description="Soukous sebene: fast, driving guitar section with rolling bass.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=90),   # 1
        CompEventSpec(beat=0.25, length_beats=0.25, velocity=70),  # e of 1
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=85),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=75),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=90),   # 3
        CompEventSpec(beat=2.25, length_beats=0.25, velocity=70),  # e of 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=80),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=85),   # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=75),   # & of 4
    ],
    bass_pattern=[
        (0.0, 0.5, 90),     # beat 1
        (1.0, 0.5, 85),     # beat 2
        (1.5, 0.5, 80),     # & of 2
        (2.5, 0.5, 85),     # & of 3
        (3.0, 0.5, 80),     # beat 4
        (3.5, 0.5, 75),     # & of 4 (rolling pickup)
    ],
    clave_pattern="standard_bell",
    clave_strict=False,
)


# ============================================================================
# AFROBEAT PATTERNS (Nigerian - Fela Kuti / Tony Allen style)
# ============================================================================

# Afrobeat basic (medium groove)
# Strong emphasis on 1 and the "one drop" feel
# Tony Allen-inspired: "the beat is on 1, everything else is conversation"
AFROBEAT_BASIC = StylePattern(
    name="afrobeat_basic",
    description="Nigerian afrobeat: heavy 1, syncopated horns, Tony Allen feel.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=95),    # 1 (STRONG - the ONE)
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=75),   # 2 (lighter)
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=80),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.5, velocity=85),    # 3 (secondary accent)
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=70),   # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=80),   # & of 4 (anticipation)
    ],
    bass_pattern=[
        (0.0, 1.0, 95),     # beat 1 (root, STRONG)
        (2.0, 0.75, 85),    # beat 3
        (3.5, 0.5, 80),     # & of 4 (anticipation into 1)
    ],
    clave_pattern="afrobeat_one",
    clave_strict=False,
)


# Afrobeat driving (up-tempo, more horn stabs)
AFROBEAT_DRIVING = StylePattern(
    name="afrobeat_driving",
    description="Afrobeat driving: up-tempo with horn stab rhythm.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=95),   # 1 (STRONG)
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=70),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=85),   # & of 2 (horn stab)
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=90),   # 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=80),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=70),   # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=85),   # & of 4 (horn stab)
    ],
    bass_pattern=[
        (0.0, 0.75, 95),    # beat 1 (root)
        (1.5, 0.5, 85),     # & of 2
        (2.0, 0.75, 90),    # beat 3
        (3.5, 0.5, 80),     # & of 4
    ],
    clave_pattern="afrobeat_one",
    clave_strict=False,
)


# ============================================================================
# HIGHLIFE PATTERNS (Ghanaian)
# ============================================================================

# Highlife basic (relaxed, guitar-driven)
# More laid-back than afrobeat, swung 8th notes
HIGHLIFE_BASIC = StylePattern(
    name="highlife_basic",
    description="Ghanaian highlife: relaxed guitar groove, swung feel.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.75, velocity=85),   # 1 (held)
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=80),    # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=70),   # & of 2 (ghost)
        CompEventSpec(beat=2.0, length_beats=0.75, velocity=85),   # 3 (held)
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=80),    # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=75),   # & of 4
    ],
    bass_pattern=[
        (0.0, 1.5, 85),     # beat 1 (long)
        (2.0, 1.0, 80),     # beat 3
        (3.5, 0.5, 75),     # & of 4 (pickup)
    ],
    clave_pattern="highlife_bell",
    clave_strict=False,
)


# Highlife palm wine (acoustic, slower)
HIGHLIFE_PALMWINE = StylePattern(
    name="highlife_palmwine",
    description="Palm wine highlife: acoustic, fingerpicking style.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=1.0, velocity=80),    # 1
        CompEventSpec(beat=1.5, length_beats=0.5, velocity=70),    # & of 2
        CompEventSpec(beat=2.0, length_beats=1.0, velocity=80),    # 3
        CompEventSpec(beat=3.5, length_beats=0.5, velocity=70),    # & of 4
    ],
    bass_pattern=[
        (0.0, 2.0, 75),     # beat 1 (whole bar feel)
        (2.0, 1.5, 70),     # beat 3
    ],
    clave_pattern="highlife_bell",
    clave_strict=False,
)


# ============================================================================
# MBALAX PATTERNS (Senegalese)
# ============================================================================

# Mbalax basic (sabar drum-influenced)
# Complex polyrhythms, strong offbeat emphasis
MBALAX_BASIC = StylePattern(
    name="mbalax_basic",
    description="Senegalese mbalax: sabar-influenced, polyrhythmic.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=90),   # 1
        CompEventSpec(beat=0.75, length_beats=0.25, velocity=80),  # a of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=75),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=85),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=90),   # 3
        CompEventSpec(beat=2.75, length_beats=0.25, velocity=80),  # a of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=75),   # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=85),   # & of 4
    ],
    bass_pattern=[
        (0.0, 0.5, 90),     # beat 1
        (1.5, 0.5, 85),     # & of 2
        (2.0, 0.5, 85),     # beat 3
        (3.5, 0.5, 80),     # & of 4
    ],
    clave_pattern="sabar_timeline",
    clave_strict=False,
)


# ============================================================================
# JÙJÚ PATTERNS (Nigerian Yoruba)
# ============================================================================

# Jùjú basic (talking drum influenced)
# Call-response structure, relaxed groove
JUJU_BASIC = StylePattern(
    name="juju_basic",
    description="Nigerian jùjú: talking drum feel, call-response.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=85),    # 1 (call)
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=70),   # & of 1 (response)
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=80),    # 2
        CompEventSpec(beat=2.0, length_beats=0.5, velocity=85),    # 3 (call)
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=70),   # & of 3 (response)
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=80),    # 4
    ],
    bass_pattern=[
        (0.0, 1.0, 85),     # beat 1
        (2.0, 1.0, 80),     # beat 3
        (3.5, 0.5, 75),     # & of 4 (anticipation)
    ],
    clave_pattern="juju_bell",
    clave_strict=False,
)


# Jùjú up-tempo (party feel)
JUJU_PARTY = StylePattern(
    name="juju_party",
    description="Jùjú party: up-tempo, dancing feel.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=90),   # 1
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=75),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=85),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=90),   # 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=80),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=75),   # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=85),   # & of 4
    ],
    bass_pattern=[
        (0.0, 0.75, 90),    # beat 1
        (1.5, 0.5, 85),     # & of 2
        (2.0, 0.75, 85),    # beat 3
        (3.5, 0.5, 80),     # & of 4
    ],
    clave_pattern="juju_bell",
    clave_strict=False,
)


# ============================================================================
# AFRO-HOUSE / AMAPIANO PATTERNS (South African)
# ============================================================================

# Amapiano basic (South African house)
# Log drum bass, syncopated piano stabs
AMAPIANO_BASIC = StylePattern(
    name="amapiano_basic",
    description="South African amapiano: log drum bass, piano stabs.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=80),   # 1
        CompEventSpec(beat=0.75, length_beats=0.25, velocity=85),  # a of 1
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=90),   # & of 2 (stab)
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=80),   # 3
        CompEventSpec(beat=2.75, length_beats=0.25, velocity=85),  # a of 3
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=90),   # & of 4 (stab)
    ],
    bass_pattern=[
        (0.0, 0.5, 95),     # beat 1 (log drum)
        (0.75, 0.25, 80),   # a of 1
        (2.0, 0.5, 90),     # beat 3 (log drum)
        (2.75, 0.25, 80),   # a of 3
    ],
    clave_pattern="amapiano_log",
    clave_strict=False,
)


# ============================================================================
# KWAITO PATTERNS (South African)
# ============================================================================

# Kwaito basic (slowed house)
KWAITO_BASIC = StylePattern(
    name="kwaito_basic",
    description="South African kwaito: slowed house, heavy bass.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=85),    # 1
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=90),    # 2
        CompEventSpec(beat=2.0, length_beats=0.5, velocity=85),    # 3
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=90),    # 4
    ],
    bass_pattern=[
        (0.0, 1.0, 95),     # beat 1 (heavy)
        (2.0, 1.0, 90),     # beat 3 (heavy)
    ],
    clave_pattern=None,  # 4-on-floor derived
    clave_strict=False,
)


# ============================================================================
# REGISTRY EXPORT
# ============================================================================

AFRICAN_PATTERNS = {
    # Soukous (Congolese)
    "soukous_basic": SOUKOUS_BASIC,
    "soukous_sebene": SOUKOUS_SEBENE,
    # Afrobeat (Nigerian)
    "afrobeat_basic": AFROBEAT_BASIC,
    "afrobeat_driving": AFROBEAT_DRIVING,
    # Highlife (Ghanaian)
    "highlife_basic": HIGHLIFE_BASIC,
    "highlife_palmwine": HIGHLIFE_PALMWINE,
    # Mbalax (Senegalese)
    "mbalax_basic": MBALAX_BASIC,
    # Jùjú (Nigerian Yoruba)
    "juju_basic": JUJU_BASIC,
    "juju_party": JUJU_PARTY,
    # Amapiano (South African)
    "amapiano_basic": AMAPIANO_BASIC,
    # Kwaito (South African)
    "kwaito_basic": KWAITO_BASIC,
}
