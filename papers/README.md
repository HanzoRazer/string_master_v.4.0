# Academic Papers Directory

*Formal academic papers and documentation for the Zone–Tritone System*

---

## 📄 **Papers**

### Primary Canon Paper

**File**: `zone_tritone_canon.tex`  
**Title**: *The Zone–Tritone System: A Formal Harmonic Framework in Modular Pitch Space*  
**Author**: Greg Brown  
**Status**: Compiled successfully (3 pages)

**Contents**:
- Formal mathematical framework in $\mathbb{Z}_{12}$
- Proofs for zone partition properties
- Theorem on chromatic tritone drift and descending fourths
- Analysis of melodic minor as dual-zone harmony
- Appendix with all five canonical axioms

**Output**: `zone_tritone_canon.pdf`

---

### Extended Academic Monograph

**File**: `zone_tritone_canon_extended.tex`  
**Title**: *The Zone–Tritone System: A Unified Harmonic Framework in Modular Pitch Space*  
**Author**: Greg Brown  
**Status**: Ready for compilation (conference/journal submission draft)

**Contents**:
- Comprehensive abstract with research summary
- Table of contents
- Expanded introduction with theoretical context
- Detailed pitch space formalization in $\mathbb{Z}_{12}$
- Zone stability proofs and propositions
- Tritone involution properties (order-2 elements)
- Chromatic drift theorem and cycle of fourths
- Dual-zone harmonic systems classification
- **Tritone rank classification framework**:
  - Rank 1: Major / Whole Tone (single-zone)
  - Rank 2: Melodic Minor / Altered (dual-zone)
  - Rank 4: Diminished (symmetry cloud)
- Discussion of theoretical implications
- Formal conclusion
- Complete proof appendix for canonical axioms

**Key Additions over Primary Paper**:
- Classification by tritone rank
- Symmetry cloud concept
- Involution property formalization
- Expanded discussion section
- More rigorous proof structure
- Conference-ready formatting

---

## 🛠 **Compilation Instructions**

### Quick Compilation

From this directory, run:

```bash
pdflatex zone_tritone_canon.tex
pdflatex zone_tritone_canon.tex  # Run twice for cross-references
```

This generates: `zone_tritone_canon.pdf`

### Alternative Methods

**Using XeLaTeX**:
```bash
xelatex zone_tritone_canon.tex
```

**Using Overleaf**:
1. Upload `zone_tritone_canon.tex` to [Overleaf](https://www.overleaf.com)
2. Click "Recompile"
3. Download PDF

**Using VS Code**:
- Install LaTeX Workshop extension
- Open the `.tex` file
- Press `Ctrl+Alt+B` (Windows/Linux) or `Cmd+Option+B` (Mac)

For detailed compilation instructions, see [../LATEX_COMPILATION_GUIDE.md](../LATEX_COMPILATION_GUIDE.md)

---

## 📦 **Required LaTeX Distribution**

**macOS**:
```bash
brew install --cask mactex
```

**Ubuntu/Debian**:
```bash
sudo apt install texlive-full
```

**Windows**:  
Download and install [MiKTeX](https://miktex.org/)

---

## 📐 **Paper Structure**

The paper follows standard academic format:

1. **Abstract** — Overview and key results
2. **Section 1-2**: Pitch space and zone definitions
3. **Section 3-4**: Half-step motion and tritones
4. **Section 5**: Chromatic drift theorem
5. **Section 6**: Melodic minor analysis
6. **Appendix**: Canonical axiom proofs

All theorems numbered sequentially with formal proofs.

---

## 🎨 **Customization**

### Adding Figures

Place diagram files in `figures/` directory:

```latex
\begin{figure}[h]
  \centering
  \includegraphics[width=0.8\textwidth]{figures/zone-diagram.pdf}
  \caption{The two whole-tone zones}
\end{figure}
```

### Adding References

Create `refs.bib` file:

```bibtex
@article{example2025,
  author = {Author Name},
  title = {Article Title},
  journal = {Music Theory Journal},
  year = {2025}
}
```

Then in the `.tex` file:

```latex
\bibliographystyle{plain}
\bibliography{refs}
```

---

## 🔄 **Version Control**

### Versioning Scheme

When updating the paper, create versioned PDFs:

```
zone_tritone_canon_v1.0.pdf  (Initial canonical version)
zone_tritone_canon_v1.1.pdf  (Minor revisions)
zone_tritone_canon_v2.0.pdf  (Major extensions)
```

### Governance

All changes to the academic paper must:
- Align with [../CANON.md](../CANON.md)
- Use terminology from [../GLOSSARY.md](../GLOSSARY.md)
- Follow governance process in [../GOVERNANCE.md](../GOVERNANCE.md)

---

## 📤 **Distribution & Citation**

### Generated Files

After compilation, you'll have:
- `zone_tritone_canon.pdf` — Main paper
- `zone_tritone_canon.aux` — Auxiliary file (can delete)
- `zone_tritone_canon.log` — Compilation log (can delete)

### Citation Format

**BibTeX**:
```bibtex
@article{brown2025zone,
  author = {Greg Brown},
  title = {The Zone--Tritone System: A Formal Harmonic Framework in Modular Pitch Space},
  year = {2025},
  note = {Zone-Tritone Theory Canon v1.0}
}
```

---

## 🎯 **Target Journals**

This paper is formatted for submission to:

- *Music Theory Spectrum*
- *Journal of Music Theory*
- *Music Theory Online*
- *Music Analysis*
- *Contemporary Music Review*

Minor formatting adjustments may be needed per journal guidelines.

---

## 📊 **Future Additions**

Planned documents for this directory:

- [ ] Conference paper (6-8 pages)
- [ ] Extended monograph version
- [ ] Pedagogical applications paper
- [ ] Software implementation paper
- [ ] Cognitive neuroscience study

---

## ✅ **Quality Checklist**

Before submission or distribution:

- [ ] PDF compiles without errors
- [ ] All theorems have proofs
- [ ] Notation is consistent throughout
- [ ] Cross-references resolve correctly
- [ ] Attribution to Greg Brown present
- [ ] Aligns with canonical axioms
- [ ] Governance approval obtained

---

## 📚 **Related Documentation**

- [../CANON.md](../CANON.md) — Source axioms
- [../FORMAL_PROOFS.md](../FORMAL_PROOFS.md) — Extended proofs
- [../ACADEMIC_PAPER.md](../ACADEMIC_PAPER.md) — Paper planning
- [../LATEX_COMPILATION_GUIDE.md](../LATEX_COMPILATION_GUIDE.md) — Detailed compilation guide

---

## 🚀 **Getting Started**

1. Ensure LaTeX is installed
2. Navigate to `papers/` directory
3. Run: `pdflatex zone_tritone_canon.tex`
4. View generated PDF
5. Commit both `.tex` and `.pdf` to repository

---

**This directory establishes the Zone–Tritone System as peer-reviewable academic work.**
