# Zone-Tritone Python Package

**Production-grade Python implementation of the Zone-Tritone harmonic framework.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE-THEORY.md)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 What Is This?

The `zone-tritone` package provides computational tools for the **Zone-Tritone System** — a unified music theory framework that explains harmony through:

- **Whole-tone zones** (color families)
- **Tritone gravity** (dominant function)
- **Chromatic motion** (zone-crossing)
- **Markov models** (probabilistic harmonic sequences)

---

## 📦 Installation

### From Source (Editable)

```bash
git clone https://github.com/your-user/zone-tritone
cd zone-tritone
pip install -e .
```

### For Development

```bash
pip install -e .
pip install pytest
pytest
```

---

## 🚀 Quick Start

### Import Core Functions

```python
from zone_tritone import (
    pc_from_name,
    name_from_pc,
    zone,
    is_zone_cross,
    all_tritone_axes,
    dominant_roots_from_tritone,
    gravity_chain,
    build_transition_counts,
    normalize_transition_matrix,
)
```

---

## 📚 API Reference

### Pitch Classes (`zone_tritone.pc`)

```python
# Convert note names to pitch classes (0-11)
pc = pc_from_name("C#")  # → 1
name = name_from_pc(6)   # → "F#"

# Canonical note names
from zone_tritone import NOTES
# ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
```

### Zones (`zone_tritone.zones`)

```python
# Get zone index (0 or 1)
z = zone(0)  # C → Zone 0 (Zone 1 in theory docs)

# Check zone relationships
is_same_zone(0, 2)     # C and D → True (both Zone 1)
is_zone_cross(0, 1)    # C and C# → True (half-step crossing)
is_half_step(4, 5)     # E and F → True
is_whole_step(0, 2)    # C and D → True
```

### Tritones (`zone_tritone.tritones`)

```python
# Get tritone partner
tritone_partner(0)  # C → 6 (F#)

# Get canonical tritone axis (sorted pair)
tritone_axis(11)    # B → (5, 11) = F-B

# Check if two notes form a tritone
is_tritone_pair(0, 6)  # C-F# → True

# List all six tritone axes
axes = all_tritone_axes()
# [(0, 6), (1, 7), (2, 8), (3, 9), (4, 10), (5, 11)]
```

### Dominant Gravity (`zone_tritone.gravity`)

```python
# Find dominant chords with a given tritone
roots = dominant_roots_from_tritone((5, 11))  # F-B
# → [1, 7] = Db7 and G7 (tritone substitution pair)

# Generate descending-fourths chain
chain = gravity_chain(7, steps=4)
# G(7) → C(0) → F(5) → Bb(10) → Eb(3)
```

### Markov Models (`zone_tritone.markov`)

```python
# Build transition matrix from chord progressions
from zone_tritone.corpus import chord_sequence_to_roots

chords = ["Dm7", "G7", "Cmaj7", "Fmaj7", "Dm7", "G7", "Cmaj7"]
roots = chord_sequence_to_roots(chords)

counts = build_transition_counts(roots)
matrix = normalize_transition_matrix(counts, smoothing=0.1)

# Sample next root probabilistically
next_root = sample_next_root(current=7, matrix=matrix)
```

---

## 🧪 Testing

Run the test suite:

```bash
pytest
```

All tests should pass:

```
tests/test_pc.py ................. [7 tests]
tests/test_zones.py .............. [8 tests]
tests/test_tritones.py ........... [6 tests]
tests/test_gravity.py ............ [5 tests]
tests/test_markov.py ............. [3 tests]

29 tests passed
```

---

## 🎼 Musical Examples

### Analyze a ii-V-I Progression

```python
from zone_tritone import pc_from_name, zone, is_zone_cross

# Dm7 → G7 → Cmaj7
dm_root = pc_from_name("D")  # 2
g_root = pc_from_name("G")   # 7
c_root = pc_from_name("C")   # 0

print(f"Dm7 zone: {zone(dm_root)}")  # Zone 0 (even)
print(f"G7 zone:  {zone(g_root)}")   # Zone 1 (odd)
print(f"C zone:   {zone(c_root)}")   # Zone 0 (even)

# Check zone-crossing at resolution
print(is_zone_cross(g_root, c_root))  # True → half-step B-C creates direction
```

### Generate Dominant Chains

```python
from zone_tritone import gravity_chain, name_from_pc

# Classic jazz turnaround starting on G7
chain = gravity_chain(7, steps=7)
chords = [name_from_pc(r) + "7" for r in chain]
print(" → ".join(chords))
# G7 → C7 → F7 → Bb7 → Eb7 → Ab7 → C#7 → F#7
```

### Find Tritone Substitutions

```python
from zone_tritone import dominant_roots_from_tritone, name_from_pc

# B-F tritone can function as two different dominants
roots = dominant_roots_from_tritone((5, 11))
for r in roots:
    print(f"{name_from_pc(r)}7")
# C#7 (Db7)
# G7
# → These are tritone substitutes!
```

---

## 📊 Data Structures

### Type Aliases (`zone_tritone.types`)

```python
from zone_tritone.types import (
    PitchClass,      # int (0-11)
    TritoneAxis,     # Tuple[int, int] (sorted pair)
    RootSequence,    # Sequence[int]
    Matrix,          # List[List[float]] (12x12 probability matrix)
)
```

---

## 🛠 Advanced Usage

### Building Corpus Statistics

```python
from zone_tritone import build_transition_counts, normalize_transition_matrix
from zone_tritone.corpus import chord_sequence_to_roots

# Load jazz standards corpus (example)
songs = [
    ["Dm7", "G7", "Cmaj7"],
    ["Cm7", "F7", "Bbmaj7"],
    ["Em7", "A7", "Dmaj7"],
]

all_roots = []
for song in songs:
    all_roots.extend(chord_sequence_to_roots(song))

counts = build_transition_counts(all_roots)
P = normalize_transition_matrix(counts, smoothing=1.0)

# Now P is a 12x12 stochastic matrix
# P[i][j] = probability of moving from root i to root j
```

### Zone-Conditioned Analysis

```python
from zone_tritone import zone, is_zone_cross

def analyze_transitions(roots):
    same_zone = 0
    cross_zone = 0
    
    for i in range(len(roots) - 1):
        if is_zone_cross(roots[i], roots[i+1]):
            cross_zone += 1
        else:
            same_zone += 1
    
    return {
        "same_zone": same_zone,
        "cross_zone": cross_zone,
        "cross_ratio": cross_zone / (same_zone + cross_zone),
    }

# Analyze a progression
roots = [2, 7, 0]  # D → G → C
stats = analyze_transitions(roots)
print(f"Zone-crossing ratio: {stats['cross_ratio']:.2%}")
```

---

## 📖 Documentation

Full documentation available in the repository:

- [CANON.md](../CANON.md) — Foundational axioms
- [GLOSSARY.md](../GLOSSARY.md) — Terminology reference
- [PEDAGOGY.md](../PEDAGOGY.md) — Teaching sequence
- [papers/](../papers/) — Academic formalization

---

## 🤝 Contributing

Contributions are welcome following canonical guidelines:

1. All code must align with [CANON.md](../CANON.md)
2. Use frozen terminology from [GLOSSARY.md](../GLOSSARY.md)
3. Maintain test coverage (run `pytest`)
4. Follow PEP 8 style conventions
5. Add docstrings for public functions

See [GOVERNANCE.md](../GOVERNANCE.md) for approval process.

---

## 📄 License

This package is released under the **MIT License** for software.

The theoretical framework itself is protected intellectual property (see [LICENSE-THEORY.md](../LICENSE-THEORY.md)).

**Attribution required:** "Based on the Zone-Tritone System by Greg Brown"

---

## 🎯 Roadmap

### v0.2.0 (Planned)
- [ ] CLI tools (`zt-analyze`, `zt-gravity`)
- [ ] iRealPro corpus parser
- [ ] Visualization functions (matplotlib)
- [ ] Jupyter notebook examples

### v0.3.0 (Planned)
- [ ] MIDI I/O integration
- [ ] MusicXML parsing
- [ ] FastAPI backend service
- [ ] React frontend demo

---

## 📧 Contact

- **Author:** Greg Brown
- **Repository:** [github.com/your-user/zone-tritone](https://github.com/your-user/zone-tritone)
- **Theory Documentation:** See main [README.md](../README.md)

---

**Built with canonical precision. Ready for production.**
