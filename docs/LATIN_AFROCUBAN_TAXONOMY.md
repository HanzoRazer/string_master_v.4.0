# Latin & Afro-Cuban Dance Taxonomy

**Date:** 2025-01-28
**Status:** Gap Analysis + Specification
**Purpose:** Document the complete Latin/Afro-Cuban rhythmic taxonomy, identify implementation gaps, and provide specifications for missing components.

---

## Executive Summary

### The Problem: Spaghetti Code Alert

The codebase has **fragmented Latin/Afro-Cuban support**:

| Location | Claims | Reality |
|----------|--------|---------|
| `DanceFamily` enum | Defines `AFRO_CUBAN`, `LATIN_AMERICAN`, `CARIBBEAN` | **0 packs implemented** |
| `patterns.py` STYLE_REGISTRY | 13 patterns listed | **All Brazilian, 0 Afro-Cuban** |
| CLI default style | `salsa_clave_2_3` | **Pattern doesn't exist** |
| CLI example | `tumbao_major` bass | **Pattern doesn't exist** |
| `clave.py` | `son_2_3`, `son_3_2` timing grids | Timing only, no accompaniment |

### Current State

```
IMPLEMENTED:
├── Afro-Brazilian (13 patterns)
│   ├── samba_basic, samba_2_4, samba_4_4
│   ├── samba_funk, samba_brazil_full
│   ├── bossa_basic
│   └── (well-developed with ghost/pickup/contour)
│
└── Afro-Cuban (0 patterns)
    ├── salsa_clave_2_3    ← REFERENCED BUT MISSING
    ├── tumbao_major       ← REFERENCED BUT MISSING
    └── (nothing implemented)
```

---

## Part 1: The Afro-Cuban Rhythmic Family Tree

### Overview

```
AFRO-CUBAN RHYTHMS
│
├── RUMBA (sacred/secular roots)
│   ├── Guaguancó (medium, flirtatious)
│   ├── Yambú (slow, elderly dance)
│   └── Columbia (fast, male solo)
│
├── SON (foundational popular music)
│   ├── Son Montuno (call-response, faster)
│   ├── Son Tradicional (slower, rural)
│   └── Changüí (Guantánamo variant)
│
├── SALSA (NYC/PR evolution of son)
│   ├── Salsa Dura (hard, brass-heavy)
│   ├── Salsa Romántica (softer, ballad-like)
│   └── Salsa en Clave (strictly clave-locked)
│
├── TIMBA (Cuban fusion, 1990s+)
│   ├── Complex gear shifts
│   ├── Heavy bass tumbaos
│   └── Breaks and "bombas"
│
├── CHA-CHA-CHÁ (1950s ballroom derivative)
│   ├── Strict 4/4 with syncopated güiro
│   └── "One-two-cha-cha-cha" count
│
├── MAMBO (big band era)
│   ├── Fast, brass-driven
│   └── Precursor to salsa
│
├── BOLERO (slow romantic)
│   ├── Cuban bolero (syncopated)
│   └── Mexican bolero (straighter)
│
└── DANZÓN (formal, classical-influenced)
    ├── Cinquillo rhythm
    └── Precursor to mambo/cha-cha
```

---

## Part 2: The Clave - Rhythmic DNA

### What is Clave?

Clave is the **rhythmic key** that organizes all Afro-Cuban music. It's a 2-bar pattern with asymmetric distribution: one bar has 3 hits, one has 2.

### Son Clave (most common)

```
2-3 Son Clave (starts sparse):
Bar 1: X . . X . . X .    (2 hits)
Bar 2: . . X . X . . .    (3 hits)
       1 & 2 & 3 & 4 &

3-2 Son Clave (starts dense):
Bar 1: . . X . X . . .    (3 hits)
Bar 2: X . . X . . X .    (2 hits)
       1 & 2 & 3 & 4 &
```

### Rumba Clave (shifted third hit)

```
2-3 Rumba Clave:
Bar 1: X . . X . . . X    (2 hits, last hit on "and of 4")
Bar 2: . . X . X . . .    (3 hits)

3-2 Rumba Clave:
Bar 1: . . X . X . . .    (3 hits)
Bar 2: X . . X . . . X    (2 hits)
```

### 6/8 Clave (Afro/Bembe)

```
6/8 Clave:
X . X . X . X . X . . .
1   2   3   4   5   6
```

---

## Part 3: Instrument Patterns (What's Missing)

### Piano (Montuno)

The montuno is the **piano guajeo** - a syncopated ostinato that outlines the harmony.

```python
# MISSING: Basic montuno patterns

# Montuno básico (anticipates beat 1)
# In 16th notes: . . X . X . X . | X . X . X . . .
#                1 e & a 2 e & a | 3 e & a 4 e & a

MONTUNO_BASIC = StylePattern(
    name="montuno_basic",
    description="Basic piano montuno: anticipates beat 1, syncopated push on 2-side",
    comp_hits=[
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # & of 1
        CompEventSpec(beat=1.0, length_beats=0.25, velocity=85),   # 2
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=75),   # & of 2
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=80),   # 3
        CompEventSpec(beat=2.5, length_beats=0.25, velocity=85),   # & of 3
        CompEventSpec(beat=3.0, length_beats=0.25, velocity=75),   # 4
        CompEventSpec(beat=3.75, length_beats=0.25, velocity=90),  # a of 4 (anticipation)
    ],
    bass_pattern=[],
)
```

### Bass (Tumbao)

The tumbao is the **bass pattern** - typically plays the "and of 2" and beat 4 (the "bombo" notes that lock with clave).

```python
# MISSING: Tumbao patterns

# Tumbao básico (2-3 son clave aligned)
# Hits: & of 2, 4 (bombo notes)

TUMBAO_BASIC = StylePattern(
    name="tumbao_basic",
    description="Basic tumbao: hits on & of 2 and 4 (bombo alignment)",
    comp_hits=[],
    bass_pattern=[
        (1.5, 0.5, 90),    # & of 2 (strong)
        (3.0, 1.0, 85),    # beat 4 (bombo)
    ],
)

# Tumbao anticipado (anticipates beat 1)
TUMBAO_ANTICIPATED = StylePattern(
    name="tumbao_anticipated",
    description="Anticipated tumbao: adds & of 4 pickup into next bar",
    comp_hits=[],
    bass_pattern=[
        (1.5, 0.5, 90),    # & of 2
        (3.0, 0.5, 85),    # beat 4
        (3.5, 0.5, 80),    # & of 4 (anticipation)
    ],
)
```

### Congas (Tumbadora)

```
Tumbao pattern (basic):
Beat:  1   &   2   &   3   &   4   &
       O   .   S   T   O   .   S   T

O = Open tone (resonant)
S = Slap (sharp)
T = Touch/tap (ghost)
```

### Bongó

```
Martillo pattern (basic):
Beat:  1   e   &   a   2   e   &   a
       H   .   L   .   H   .   L   L

H = High drum
L = Low drum
```

---

## Part 4: Required Patterns for Minimum Viable Afro-Cuban

### Priority 1: Core Salsa (6 patterns)

| Pattern ID | Type | Clave | Description |
|------------|------|-------|-------------|
| `salsa_montuno_basic` | comp | 2-3 son | Basic piano montuno |
| `salsa_montuno_3_2` | comp | 3-2 son | 3-2 oriented montuno |
| `salsa_tumbao_basic` | bass | 2-3 son | Basic bass tumbao |
| `salsa_tumbao_anticipated` | bass | 2-3 son | Tumbao with anticipation |
| `salsa_full_2_3` | both | 2-3 son | Complete salsa groove |
| `salsa_full_3_2` | both | 3-2 son | Complete 3-2 groove |

### Priority 2: Son/Cha-Cha-Chá (4 patterns)

| Pattern ID | Type | Clave | Description |
|------------|------|-------|-------------|
| `son_montuno_basic` | comp | 2-3 son | Traditional son piano |
| `son_tumbao_basic` | bass | 2-3 son | Traditional son bass |
| `chacha_basic` | comp | none | Cha-cha-chá comping |
| `chacha_bass` | bass | none | Cha-cha bass (on 1 & 3) |

### Priority 3: Mambo/Bolero (4 patterns)

| Pattern ID | Type | Clave | Description |
|------------|------|-------|-------------|
| `mambo_montuno` | comp | 2-3 son | Fast mambo piano |
| `mambo_bass` | bass | 2-3 son | Mambo bass line |
| `bolero_comp` | comp | none | Slow romantic bolero |
| `bolero_bass` | bass | none | Bolero bass (sparse) |

### Priority 4: Rumba (3 patterns)

| Pattern ID | Type | Clave | Description |
|------------|------|-------|-------------|
| `guaguanco_comp` | comp | 2-3 rumba | Guaguancó feel |
| `guaguanco_bass` | bass | 2-3 rumba | Guaguancó bass |
| `rumba_clave_click` | click | 2-3 rumba | Rumba clave metronome |

---

## Part 5: Implementation Checklist

### Immediate Fixes (CLI lies)

- [ ] Add `salsa_clave_2_3` to STYLE_REGISTRY (or change CLI default)
- [ ] Add `tumbao_major` to STYLE_REGISTRY (or remove from examples)
- [ ] Verify all CLI-referenced styles exist

### Phase 1: Core Salsa Pack

```
packs/
└── salsa_clave_locked_v1.dpack.json
    ├── dance_family: "afro_cuban"
    ├── subdivision: "binary"
    ├── clave: { type: "explicit", pattern: "son", direction: "2_3" }
    └── patterns: [montuno_basic, tumbao_basic, salsa_full]
```

### Phase 2: Son & Traditional

```
packs/
├── son_tradicional_v1.dpack.json
├── chacha_classic_v1.dpack.json
└── bolero_romantico_v1.dpack.json
```

### Phase 3: Advanced/Fusion

```
packs/
├── timba_cubana_v1.dpack.json
├── mambo_big_band_v1.dpack.json
└── guaguanco_rumba_v1.dpack.json
```

---

## Part 6: Taxonomy Alignment

### Problem: Multiple Taxonomies

| File | Taxonomy Field | Values Used |
|------|----------------|-------------|
| `dance_pack.py` | `DanceFamily` enum | `AFRO_CUBAN`, `LATIN_AMERICAN`, etc. |
| `*_canonical.json` | `style_family` string | `"latin"`, `"jazz"`, `"blues"` |
| `patterns.py` | (none) | Just pattern names |
| CLI | `--style` flag | References undefined patterns |

### Solution: Single Source of Truth

1. **DanceFamily enum** is the canonical taxonomy for rhythm packs
2. **style_family** in canonicals should map to DanceFamily values
3. **STYLE_REGISTRY** keys should follow `{family}_{variant}_{clave}` convention

### Proposed Naming Convention

```
{family}_{form}_{variant}_{clave_direction}

Examples:
- salsa_montuno_basic_2_3
- son_tumbao_anticipated_3_2
- chacha_comp_basic
- bolero_bass_sparse
```

---

## Part 7: Clave Integration

### Current: clave.py (timing only)

```python
# Only defines WHEN clave hits occur
ClaveType = Literal["son_2_3", "son_3_2"]
def clave_hit_steps(grid: Grid, clave: ClaveType) -> list[int]
```

### Needed: Clave-aware accompaniment

```python
# Patterns should declare clave alignment
@dataclass
class StylePattern:
    name: str
    clave_alignment: ClaveType | None  # NEW
    clave_strict: bool = False          # NEW: reject notes off clave?
    ...

# Example: Montuno is clave-aligned
SALSA_MONTUNO_BASIC = StylePattern(
    name="salsa_montuno_basic",
    clave_alignment="son_2_3",
    clave_strict=True,  # All hits must align with clave grid
    ...
)
```

---

## Part 8: Reference - Cuban Rhythm Cheat Sheet

### The "Bombo" Notes

In 2-3 son clave, the **bombo** notes are:
- **& of 2** (beat 2.5)
- **Beat 4**

These are where bass and piano MUST hit for proper clave alignment.

### Common Tempo Ranges

| Form | BPM | Feel |
|------|-----|------|
| Bolero | 60-90 | Slow, romantic |
| Son | 90-120 | Medium, danceable |
| Cha-cha-chá | 110-130 | Medium, precise |
| Salsa | 140-200 | Fast, energetic |
| Mambo | 160-220 | Fast, driving |
| Timba | 140-180 | Variable (gear shifts) |

### Clave Direction Rules

| Form | Typical Direction | Notes |
|------|-------------------|-------|
| Son | 2-3 | Traditional, "forward" |
| Salsa | Both | Depends on song |
| Rumba | 2-3 | Almost always |
| Cha-cha | No strict clave | Güiro-driven instead |
| Bolero | Relaxed clave | Melodic freedom |

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-28 | Claude | Initial taxonomy and gap analysis |
