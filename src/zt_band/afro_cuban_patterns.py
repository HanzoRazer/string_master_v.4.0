"""
Afro-Cuban accompaniment patterns with clave alignment.

These patterns are designed for salsa, son, and other Afro-Cuban forms.
Each pattern declares its clave alignment (son_2_3, son_3_2, rumba_2_3, rumba_3_2).

Key concepts:
- Bombo notes: &2 and beat 4 in 2-3 son clave - where bass and piano MUST hit
- Montuno: syncopated piano ostinato that outlines harmony
- Tumbao: bass pattern locked to clave bombo notes
- Clave: 2-bar rhythmic key (3 hits in one bar, 2 in the other)

Reference: docs/LATIN_AFROCUBAN_TAXONOMY.md
"""
from __future__ import annotations

from .patterns import CompEventSpec, StylePattern


# ============================================================================
# SALSA / SON PATTERNS (2-3 Son Clave)
# ============================================================================

# Montuno básico (2-3 son clave aligned)
# Piano pattern that anticipates beat 1 and pushes on the 2-side
# In 16th notes: . . X . X . X . | X . X . X . . .
#                1 e & a 2 e & a | 3 e & a 4 e & a
SALSA_MONTUNO_BASIC = StylePattern(
    name="salsa_clave_2_3",  # CLI default name
    description="Basic salsa montuno: anticipates beat 1, syncopated push (2-3 son clave).",
    comp_hits=[
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=85),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=75),   # & of 2 (BOMBO - lighter comp)
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=80),   # 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=85),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=75),   # 4 (BOMBO - lighter comp)
        CompEventSpec(beat=3.75, length_beats=0.25, velocity=90),  # a of 4 (anticipation!)
    ],
    bass_pattern=[],  # bass handled separately by tumbao
    clave_pattern="son_2_3",
    clave_strict=True,
)


# Montuno 3-2 variant
SALSA_MONTUNO_3_2 = StylePattern(
    name="salsa_clave_3_2",
    description="Salsa montuno for 3-2 son clave orientation.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=85),   # 1 (3-side starts dense)
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=75),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=90),   # & of 2 (anticipation)
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=80),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=85),   # 4
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=75),   # & of 4
    ],
    bass_pattern=[],
    clave_pattern="son_3_2",
    clave_strict=True,
)


# Tumbao básico (2-3 son clave aligned)
# Bass pattern hitting the BOMBO notes: & of 2 and beat 4
TUMBAO_BASIC = StylePattern(
    name="tumbao_major",  # CLI example name
    description="Basic tumbao bass: hits on & of 2 and 4 (bombo alignment, 2-3 clave).",
    comp_hits=[],  # comp handled by montuno
    bass_pattern=[
        (1.5, 0.5, 90),    # & of 2 (BOMBO - strong)
        (3.0, 1.0, 85),    # beat 4 (BOMBO)
    ],
    clave_pattern="son_2_3",
    clave_strict=True,
)


# Tumbao with anticipation (adds & of 4 pickup)
TUMBAO_ANTICIPATED = StylePattern(
    name="tumbao_anticipated",
    description="Anticipated tumbao: adds & of 4 pickup into next bar.",
    comp_hits=[],
    bass_pattern=[
        (1.5, 0.5, 90),    # & of 2 (BOMBO)
        (3.0, 0.5, 85),    # beat 4 (BOMBO)
        (3.5, 0.5, 80),    # & of 4 (anticipation into next bar)
    ],
    clave_pattern="son_2_3",
    clave_strict=True,
)


# Full salsa groove (montuno + tumbao combined)
SALSA_FULL_2_3 = StylePattern(
    name="salsa_full_2_3",
    description="Complete salsa groove: montuno comp + tumbao bass (2-3 son clave).",
    comp_hits=[
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=85),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=75),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=80),   # 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=85),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=75),   # 4
        CompEventSpec(beat=3.75, length_beats=0.25, velocity=90),  # a of 4 (anticipation)
    ],
    bass_pattern=[
        (1.5, 0.5, 90),    # & of 2 (BOMBO)
        (3.0, 0.5, 85),    # beat 4 (BOMBO)
        (3.5, 0.5, 80),    # & of 4 (anticipation)
    ],
    clave_pattern="son_2_3",
    clave_strict=True,
)


# ============================================================================
# SON TRADICIONAL PATTERNS
# ============================================================================

# Son montuno (traditional, slightly different from salsa)
SON_MONTUNO_BASIC = StylePattern(
    name="son_montuno_basic",
    description="Traditional son piano guajeo (2-3 clave).",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=75),    # 1 (softer)
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # & of 1
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=85),   # & of 2 (BOMBO area)
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=80),   # 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=85),   # 4 (BOMBO)
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=75),   # & of 4
    ],
    bass_pattern=[],
    clave_pattern="son_2_3",
    clave_strict=False,  # son is more relaxed than salsa
)


# Son tumbao (traditional)
SON_TUMBAO_BASIC = StylePattern(
    name="son_tumbao_basic",
    description="Traditional son bass pattern (2-3 clave).",
    comp_hits=[],
    bass_pattern=[
        (0.0, 0.75, 70),   # beat 1 (root, light)
        (1.5, 0.5, 85),    # & of 2 (BOMBO)
        (3.0, 1.0, 80),    # beat 4 (BOMBO)
    ],
    clave_pattern="son_2_3",
    clave_strict=False,
)


# ============================================================================
# CHA-CHA-CHÁ PATTERNS (less strict clave)
# ============================================================================

# Cha-cha-chá comp (güiro-driven, not strictly clave)
CHACHA_BASIC = StylePattern(
    name="chacha_basic",
    description="Cha-cha-chá comping: 'one-two-cha-cha-cha' syncopation.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=80),    # 1
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=80),    # 2
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=85),   # 3 (cha)
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=80),   # & of 3 (cha)
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=85),    # 4 (cha)
    ],
    bass_pattern=[],
    clave_pattern=None,  # cha-cha is güiro-driven, not clave-strict
    clave_strict=False,
)


# Cha-cha-chá bass (on 1 and 3)
CHACHA_BASS = StylePattern(
    name="chacha_bass",
    description="Cha-cha-chá bass: strong on 1 and 3.",
    comp_hits=[],
    bass_pattern=[
        (0.0, 1.0, 85),    # beat 1
        (2.0, 1.0, 85),    # beat 3
    ],
    clave_pattern=None,
    clave_strict=False,
)


# ============================================================================
# BOLERO PATTERNS (slow romantic, relaxed clave)
# ============================================================================

# Bolero comp (sparse, romantic)
BOLERO_COMP = StylePattern(
    name="bolero_comp",
    description="Cuban bolero: slow, romantic comping with syncopation.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=1.5, velocity=70),    # 1 (long)
        CompEventSpec(beat=2.0, length_beats=1.0, velocity=65),    # 3 (soft re-hit)
        CompEventSpec(beat=3.5, length_beats=0.5, velocity=75),    # & of 4 (anticipation)
    ],
    bass_pattern=[],
    clave_pattern=None,  # bolero has melodic freedom
    clave_strict=False,
)


# Bolero bass (sparse)
BOLERO_BASS = StylePattern(
    name="bolero_bass",
    description="Cuban bolero bass: sparse, melodic.",
    comp_hits=[],
    bass_pattern=[
        (0.0, 2.0, 70),    # beat 1 (whole note feel)
        (2.0, 1.5, 65),    # beat 3
    ],
    clave_pattern=None,
    clave_strict=False,
)


# ============================================================================
# RUMBA PATTERNS (2-3 Rumba Clave)
# ============================================================================

# Guaguancó comp (rumba clave - shifted 3rd hit)
GUAGUANCO_COMP = StylePattern(
    name="guaguanco_comp",
    description="Guaguancó comping: rumba clave aligned (2-3).",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=85),   # 1
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=80),   # & of 2
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=85),   # & of 3
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=90),   # & of 4 (rumba's shifted hit)
    ],
    bass_pattern=[],
    clave_pattern="rumba_2_3",
    clave_strict=True,
)


# Guaguancó bass
GUAGUANCO_BASS = StylePattern(
    name="guaguanco_bass",
    description="Guaguancó bass: rumba clave locked.",
    comp_hits=[],
    bass_pattern=[
        (1.5, 0.5, 85),    # & of 2
        (3.5, 0.5, 90),    # & of 4 (rumba shift)
    ],
    clave_pattern="rumba_2_3",
    clave_strict=True,
)


# ============================================================================
# BOOGALOO PATTERNS (1960s NYC Latin Soul fusion)
# ============================================================================
# Latin boogaloo fuses son clave with R&B backbeat.
# Looser clave feel than strict salsa, strong 2 & 4 backbeat (soul influence).
# Artists: Joe Cuba, Pete Rodriguez, Ricardo Ray

# Boogaloo comp (piano/organ - soul-influenced)
# Backbeat emphasis + Latin syncopation
BOOGALOO_BASIC = StylePattern(
    name="boogaloo_basic",
    description="Latin boogaloo: soul backbeat meets Latin syncopation (loose clave).",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=80),    # 1
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=90),    # 2 (BACKBEAT - soul)
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=75),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.5, velocity=80),    # 3
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=90),    # 4 (BACKBEAT - soul)
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=80),   # & of 4 (anticipation)
    ],
    bass_pattern=[],
    clave_pattern="son_2_3",
    clave_strict=False,  # boogaloo is LOOSE clave
)


# Boogaloo bass (funky, syncopated)
BOOGALOO_BASS = StylePattern(
    name="boogaloo_bass",
    description="Boogaloo bass: funky Latin with R&B influence.",
    comp_hits=[],
    bass_pattern=[
        (0.0, 0.5, 85),     # beat 1 (root)
        (1.0, 0.5, 90),     # beat 2 (backbeat lock)
        (1.5, 0.5, 80),     # & of 2 (Latin push)
        (2.5, 0.5, 75),     # & of 3 (funk fill)
        (3.0, 0.5, 90),     # beat 4 (backbeat lock)
        (3.5, 0.5, 80),     # & of 4 (anticipation)
    ],
    clave_pattern="son_2_3",
    clave_strict=False,
)


# Boogaloo full groove (comp + bass)
BOOGALOO_FULL = StylePattern(
    name="boogaloo_full",
    description="Full Latin boogaloo groove: soul backbeat + Latin clave fusion.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=80),    # 1
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=90),    # 2 (BACKBEAT)
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=75),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.5, velocity=80),    # 3
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=90),    # 4 (BACKBEAT)
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=80),   # & of 4
    ],
    bass_pattern=[
        (0.0, 0.5, 85),     # beat 1
        (1.0, 0.5, 90),     # beat 2
        (1.5, 0.5, 80),     # & of 2
        (2.5, 0.5, 75),     # & of 3
        (3.0, 0.5, 90),     # beat 4
        (3.5, 0.5, 80),     # & of 4
    ],
    clave_pattern="son_2_3",
    clave_strict=False,
)


# ============================================================================
# REGISTRY EXPORT
# ============================================================================

AFRO_CUBAN_PATTERNS = {
    # Salsa (2-3)
    "salsa_clave_2_3": SALSA_MONTUNO_BASIC,  # CLI default
    "salsa_clave_3_2": SALSA_MONTUNO_3_2,
    "tumbao_major": TUMBAO_BASIC,            # CLI example
    "tumbao_anticipated": TUMBAO_ANTICIPATED,
    "salsa_full_2_3": SALSA_FULL_2_3,
    # Son
    "son_montuno_basic": SON_MONTUNO_BASIC,
    "son_tumbao_basic": SON_TUMBAO_BASIC,
    # Cha-cha-chá
    "chacha_basic": CHACHA_BASIC,
    "chacha_bass": CHACHA_BASS,
    # Bolero
    "bolero_comp": BOLERO_COMP,
    "bolero_bass": BOLERO_BASS,
    # Rumba
    "guaguanco_comp": GUAGUANCO_COMP,
    "guaguanco_bass": GUAGUANCO_BASS,
    # Boogaloo (Latin Soul)
    "boogaloo_basic": BOOGALOO_BASIC,
    "boogaloo_bass": BOOGALOO_BASS,
    "boogaloo_full": BOOGALOO_FULL,
}
