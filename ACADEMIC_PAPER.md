# Zone–Tritone System: Academic Paper

*LaTeX-formatted academic paper sections for formal publication*

---

## 🎯 **Purpose**

This document contains formal academic paper sections written in LaTeX format, suitable for submission to music theory journals, conferences, and academic publications.

**Status**: Placeholder — Content to be developed

---

## Planned Sections

### 1. Abstract

*To be written*

### 2. Introduction

*To be written*

- Historical context of harmonic theory
- Limitations of traditional approaches
- Introduction to the Zone–Tritone framework
- Paper structure overview

### 3. Theoretical Foundation

*To be written*

**Subsections**:
- 3.1 The Whole-Tone Zone Model
- 3.2 Tritone Anchors and Dominant Function
- 3.3 Half-Step Motion and Zone-Crossing
- 3.4 Chromatic Tritone Drift

### 4. Axiomatization

*To be written*

Formal statement of the four canonical axioms with mathematical precision.

### 5. Applications

*To be written*

**Subsections**:
- 5.1 Analysis of Standard Progressions (ii-V-I)
- 5.2 Tritone Substitution Mechanism
- 5.3 Melodic Minor as Dual-Zone System
- 5.4 Dominant Cycles and Circle of Fifths

### 6. Pedagogical Framework

*To be written*

Overview of the six-level teaching sequence and its theoretical justification.

### 7. Comparison with Existing Theories

*To be written*

- Schenkerian analysis
- Neo-Riemannian theory
- Jazz theory approaches
- Set theory

### 8. Empirical Validation

*To be written*

Analysis of corpus data and perceptual studies (future work).

### 9. Conclusion

*To be written*

### 10. References

*To be compiled*

---

## LaTeX Setup

### Required Packages

```latex
\documentclass[12pt]{article}
\usepackage{amsmath, amssymb}
\usepackage{musicography}
\usepackage{lilyglyphs}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{tikz}
\usepackage{hyperref}
```

### Custom Commands

```latex
% Zone notation
\newcommand{\zoneone}{Z_1}
\newcommand{\zonetwo}{Z_2}

% Tritone anchor
\newcommand{\tritone}[2]{#1 \leftrightarrow #2}

% Zone-crossing
\newcommand{\crossing}{\rightarrow_{\text{cross}}}
```

---

## Mathematical Notation Conventions

### Sets

- **Chromatic Set**: $C = \{c_0, c_1, ..., c_{11}\}$ (12-tone equal temperament)
- **Zone 1**: $Z_1 = \{c_0, c_2, c_4, c_6, c_8, c_{10}\}$
- **Zone 2**: $Z_2 = \{c_1, c_3, c_5, c_7, c_9, c_{11}\}$

### Functions

- **Tritone Function**: $T: C \rightarrow C$, where $T(c_i) = c_{(i+6) \mod 12}$
- **Half-step Function**: $H: C \rightarrow C$, where $H(c_i) = c_{(i+1) \mod 12}$

### Properties

- **Partition Property**: $Z_1 \cap Z_2 = \emptyset$ and $Z_1 \cup Z_2 = C$
- **Zone-Crossing**: $\forall c_i \in Z_1, H(c_i) \in Z_2$ and vice versa

---

## Figures & Diagrams

### Figure List (To Be Created)

1. **Figure 1**: The two whole-tone zones as complementary partitions
2. **Figure 2**: The six tritone pairs in chromatic space
3. **Figure 3**: Zone-crossing via half-step motion
4. **Figure 4**: Dominant resolution as dual zone-crossing (G7→C)
5. **Figure 5**: Chromatic tritone drift producing descending fourths
6. **Figure 6**: Melodic minor dual-zone structure
7. **Figure 7**: Comparison with traditional circle of fifths

All figures should follow [THEORY_DIAGRAMS.md](THEORY_DIAGRAMS.md) standards.

---

## Tables

### Table List (To Be Created)

1. **Table 1**: Zone membership for all 12 pitches
2. **Table 2**: The six tritone pairs and their dominant functions
3. **Table 3**: Common progressions analyzed by zone-crossing
4. **Table 4**: Pedagogical sequence and learning objectives

---

## Notes for Authors

### Voice & Style

- **Formal academic tone** — Precise, technical, rigorous
- **Avoid colloquialisms** — No jazz slang or casual language
- **Mathematical rigor** — Formal definitions and proofs
- **Clear examples** — Musical illustrations for each concept
- **Comparative analysis** — Position within existing theoretical frameworks

### Citation Requirements

All materials must cite:
- Original Zone–Tritone framework by Greg Brown
- Relevant music theory literature
- Historical harmonic theory sources

### Peer Review Considerations

- Anticipate objections from traditional theorists
- Address "is this just repackaged theory?" question
- Demonstrate novelty and explanatory power
- Provide empirical or analytical support

---

## Development Checklist

- [ ] Complete abstract (150-250 words)
- [ ] Write full introduction section
- [ ] Formalize all four axioms mathematically
- [ ] Create all figures and diagrams
- [ ] Develop musical examples
- [ ] Write proofs for key theorems (see [FORMAL_PROOFS.md](FORMAL_PROOFS.md))
- [ ] Complete literature review
- [ ] Add bibliography and references
- [ ] Review for terminology consistency with [GLOSSARY.md](GLOSSARY.md)
- [ ] Obtain governance approval before submission

---

## Target Journals

**Primary Targets**:
- *Music Theory Spectrum*
- *Journal of Music Theory*
- *Music Theory Online*
- *Music Analysis*

**Secondary Targets**:
- *Journal of Jazz Studies*
- *Contemporary Music Review*

---

## Version Control

This is **Academic Paper v0.1** (placeholder stage).

Actual content development requires governance approval (see [GOVERNANCE.md](GOVERNANCE.md)).

---

**This document will contain formal, peer-reviewable academic exposition of the Zone–Tritone System.**
