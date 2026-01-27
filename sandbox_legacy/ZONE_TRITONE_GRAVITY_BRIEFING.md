# Zone-Tritone Gravity Briefing

> Paste this into any chat that needs to understand the zone-tritone
> framework used in the string_master exercise system.

---

## Core Principle

All harmonic motion in tonal music can be explained by **tritone resolution**.
A tritone (6 semitones) is an unstable interval that wants to resolve — outward
to a minor 6th or inward to a major 3rd. Every dominant 7th chord contains
exactly one tritone (between its 3rd and 7th). That tritone IS the engine.

The "zone-tritone" framework makes this explicit and computable.

---

## 1. Zones (Whole-Tone Partitioning)

The 12 pitch classes split into two whole-tone zones by parity:

```
Zone 1 (even): C(0)  D(2)  E(4)  F#(6)  Ab(8)  Bb(10)
Zone 2 (odd):  C#(1) Eb(3) F(5)  G(7)   A(9)   B(11)
```

**Key property**: A half-step always crosses zones. A whole-step stays
in the same zone. This means:

- **Zone-crossing motion** = half-step resolution = strong gravity
- **Same-zone motion** = whole-step = weaker, scalar motion

Code: `zone(pc) = pc % 2` — that's the entire implementation.

---

## 2. Tritone Axes

A tritone pair always shares the same zone (both even or both odd).
There are exactly **6 unique tritone axes** in 12-TET:

```
Zone 1 axes:  {C, F#}    {D, Ab}    {E, Bb}
              (0,6)      (2,8)      (4,10)

Zone 2 axes:  {C#, G}    {Eb, A}    {F, B}
              (1,7)      (3,9)      (5,11)
```

Each axis is shared by exactly **two dominant 7th chords** a tritone apart
(the tritone-substitution pair). Example:

```
Axis {D, Ab} (2,8):
  Bb7 = Bb-D-F-Ab  → 3rd=D, 7th=Ab  ← contains this tritone
  E7  = E-G#-B-D   → 3rd=G#(=Ab), 7th=D  ← SAME tritone
```

Bb7 and E7 share the same gravitational engine. One is the "front door,"
the other is the "side entrance" (tritone substitution).

---

## 3. Gravity

"Gravity" = the pull of a tritone toward its resolution target.

The tritone {3rd, 7th} of a dominant chord resolves by half-step:

```
G7 contains B-F:
  B (3rd)  → C (root of target)    half-step UP
  F (7th)  → E (3rd of target)     half-step DOWN
  Target: C major (or C minor)
```

**Gravity is directional** — the tritone points AT a specific tonic.

**Dual gravity**: For any target chord, there are TWO tritone axes
that can resolve to it (from the V7 and from the bVII7/backdoor):

```
Target: Cm

Front door (V7):
  G7 contains B-F → B->C, F->Eb       axis {B, F} = (5,11)

Backdoor (bVII7):
  Bb7 contains D-Ab → D->Eb, Ab->G    axis {D, Ab} = (2,8)

Both axes pull to Cm from different directions.
```

---

## 4. Gravity Chain

Dominant chords chain by descending 5ths (the cycle of fifths = cycle
of dominant resolutions):

```
G7 → C7 → F7 → Bb7 → Eb7 → ...
```

Each link is a gravity event: the tritone of one chord resolves into
the next chord, which itself contains a NEW tritone that pulls forward.

Code: `gravity_chain(root, steps)` generates this by `r = (r - 7) % 12`.

---

## 5. Applied Examples in the Repo

### Gospel Backdoor (C minor)

```yaml
tritone_gravity:
  target: "Cm"
  axis_primary:
    name: "D-Ab"
    dominants: ["Bb7", "E7"]
    resolution: "D->Eb, Ab->G"
    role: "backdoor gravity"
  axis_secondary:
    name: "B-F"
    dominants: ["G7", "Db7"]
    resolution: "B->C, F->Eb"
    role: "front-door gravity"
```

The backdoor cadence (Fm → Bb7 → Cm) and the front door (G7 → Cm)
are not opposites — they are two faces of the same gravitational field.
The tritone subs (E7, Db7) give chromatic bass alternatives.

### Phrygian Gravity (flamenco)

Phrygian Dominant is the 5th mode of harmonic minor. It has DUAL gravity:

```
A Phrygian Dominant:
  1. bII → I  (Bb → A) = zone-crossing half-step = "Phrygian gravity"
  2. V7 → i   (A7 → Dm) = tritone resolution to parent minor

Zone map:
  A=9 (Z2), Bb=10 (Z1) → ZONE CROSS on the bII→I resolution
  A7 tritone: C#(1)-G(7) → resolves to Dm: C#→D, G→F
```

### Minor Gravity (jazz)

Over ii-V-i in minor:
- V7alt contains a tritone that resolves to i
- The tritone-sub moment = "same tension, new bass"
- Guide-tones (3rds & 7ths) are the tritone, everything else is color

---

## 6. Implementation

The zone-tritone system is implemented in `src/shared/zone_tritone/`:

| File | Purpose |
|------|---------|
| `types.py` | `PitchClass = int (0-11)`, `TritoneAxis = tuple[int,int]` |
| `zones.py` | `zone(pc)`, `is_zone_cross()`, `is_half_step()` |
| `tritones.py` | `tritone_axis(pc)`, `all_tritone_axes()`, `tritone_partner()` |
| `gravity.py` | `dominant_roots_from_tritone(axis)`, `gravity_chain(root, steps)` |
| `pc.py` | `pc_from_name("Bb") → 10`, `name_from_pc(10) → "Bb"` |

---

## 7. How It Connects to Exercises

Every exercise in the repo can be understood through this lens:

| Exercise Type | Zone-Tritone Concept |
|---------------|---------------------|
| Enclosures | Chromatic approach = zone-crossing half-step to chord tone |
| Pivot patterns | Pivot note is same-zone; resolution is zone-cross |
| Gospel backdoor | Dual-axis gravity (bVII7 + V7 both pull to tonic) |
| Phrygian gravity | bII→I zone-cross + parent minor tritone resolution |
| Barry Harris 6th dim scale | Interleaved chord tones + dim passing tones = zone-alternating pattern |
| Chromatic triplet chains | 3-note cells that cross zones to land on chord tones |
| Guide-tone voice-leading | 3rd and 7th = THE tritone; voice-leading IS gravity |

---

## 8. Rules for Applying Zone-Tritone Analysis

1. **Identify the tritone axis** in any dominant chord: 3rd and 7th
2. **Find both dominant roots** that share that axis (tritone-sub pair)
3. **Map the resolution**: each tritone member resolves by half-step (zone-cross)
4. **Name the gravity type**: front-door (V7→I) or backdoor (bVII7→I)
5. **Check for dual gravity**: does the target have both axes pointing at it?
6. **Zone-crossing = strong resolution**; same-zone = passing/scalar motion

When tagging exercises, use these fields:

```yaml
# In .ztex files:
tritone_gravity:
  target: "Cm"
  axis_primary:
    name: "D-Ab"
    dominants: ["Bb7", "E7"]
    resolution: "D->Eb, Ab->G"
    role: "backdoor gravity"

# In tags:
tags:
  zone_theory: zone_crossing | dual_gravity | tritone_resolution
  motion_type: gravity_cell
  harmony_type: phrygian_dominant | minor_gravity | backdoor
```
