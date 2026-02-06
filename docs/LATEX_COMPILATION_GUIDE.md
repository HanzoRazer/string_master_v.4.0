# LaTeX Compilation Guide for Zone–Tritone Academic Documents

*Instructions for compiling and working with the formal mathematical paper*

---

## 📄 **Document Files**

### Primary LaTeX Document

**File**: `zone-tritone-formal.tex`

This is a complete, self-contained LaTeX document containing:
- Formal mathematical framework
- Theorems with proofs
- Appendix with canonical axiom proofs
- Ready for compilation and submission

---

## 🛠 **Compilation Instructions**

### Option 1: Using pdfLaTeX (Recommended)

```bash
pdflatex zone-tritone-formal.tex
pdflatex zone-tritone-formal.tex  # Run twice for cross-references
```

### Option 2: Using XeLaTeX (For Unicode Support)

```bash
xelatex zone-tritone-formal.tex
```

### Option 3: Using Overleaf

1. Upload `zone-tritone-formal.tex` to [Overleaf](https://www.overleaf.com)
2. Click "Recompile"
3. Download PDF

### Option 4: Using VS Code with LaTeX Workshop

1. Install LaTeX Workshop extension
2. Open `zone-tritone-formal.tex`
3. Press `Ctrl+Alt+B` (or `Cmd+Option+B` on Mac)
4. PDF generates automatically

---

## 📦 **Required LaTeX Packages**

The document uses standard packages included in most distributions:

- `amsmath` — Mathematical typesetting
- `amssymb` — Mathematical symbols
- `amsthm` — Theorem environments
- `geometry` — Page layout
- `hyperref` — Hyperlinks and cross-references

### Installation

**TeX Live** (Linux/Mac):
```bash
sudo apt-get install texlive-full  # Ubuntu/Debian
brew install --cask mactex          # macOS
```

**MiKTeX** (Windows):
Download from [miktex.org](https://miktex.org/download)

---

## 📐 **Document Structure**

### Main Sections

1. **Abstract** — Overview of formal framework
2. **Section 1**: Formal Framework
   - Pitch space and modular arithmetic
   - Whole-tone zones
   - Half-step motion
   - Tritones as internal axes
3. **Section 2**: Chromatic Tritone Drift
   - Proof of descending fourth cycles
4. **Section 3**: Dual-Zone Structure of Melodic Minor
   - Two tritone anchors
   - Definition of dual-zone harmony
5. **Appendix**: Formal proofs for all five canonical axioms

### Theorem Environments

The document defines:
- `\begin{theorem}...\end{theorem}`
- `\begin{proposition}...\end{proposition}`
- `\begin{corollary}...\end{corollary}`
- `\begin{definition}...\end{definition}`
- `\begin{proof}...\end{proof}`

All numbered sequentially within sections.

---

## ✏️ **Customization & Extension**

### Adding Musical Notation

To include staff notation, add these packages:

```latex
\usepackage{musixtex}      % Traditional music notation
\usepackage{lilyglyphs}    % Musical symbols
```

### Adding Diagrams

For zone diagrams and visual representations:

```latex
\usepackage{tikz}
\usepackage{pgfplots}

\begin{tikzpicture}
  % Zone 1 visualization
  \draw[thick, blue] (0,0) circle (1cm);
  \node at (0,0) {Zone 1};
\end{tikzpicture}
```

### Adding Bibliography

Replace the references section with:

```latex
\bibliographystyle{plain}
\bibliography{zone-tritone-refs}
```

Then create `zone-tritone-refs.bib` with BibTeX entries.

---

## 🎨 **Formatting Standards**

### Journal Submission Variants

**Music Theory Spectrum**:
```latex
\documentclass[12pt]{article}
\usepackage{mts-style}  % If provided by journal
```

**Journal of Music Theory**:
```latex
\documentclass[11pt,twocolumn]{article}
```

**Music Theory Online**:
- HTML + MathJax format preferred
- Use Pandoc to convert from LaTeX

---

## 🧪 **Testing & Validation**

### Check Mathematical Correctness

All proofs have been reviewed for:
✔ Logical consistency
✔ Alignment with canonical axioms ([CANON.md](CANON.md))
✔ Formal rigor
✔ Clear notation

### Verify Theorem Numbering

After compilation, check that:
- Theorem numbers are sequential
- Cross-references resolve correctly
- Appendix numbering is correct

---

## 📤 **Export & Distribution**

### PDF Generation

Standard compilation produces `zone-tritone-formal.pdf`

### Converting to Other Formats

**HTML with MathJax**:
```bash
pandoc zone-tritone-formal.tex -o zone-tritone-formal.html --mathjax
```

**Word Document** (for collaboration):
```bash
pandoc zone-tritone-formal.tex -o zone-tritone-formal.docx
```

**Markdown** (for GitHub):
```bash
pandoc zone-tritone-formal.tex -o zone-tritone-formal.md
```

---

## 🔗 **Integration with Documentation**

### Cross-References to Canonical Files

While LaTeX cannot directly link to markdown files, your supporting documentation includes:

- [CANON.md](CANON.md) — Source axioms
- [GLOSSARY.md](GLOSSARY.md) — Terminology definitions
- [FORMAL_PROOFS.md](FORMAL_PROOFS.md) — Extended proof repository
- [ACADEMIC_PAPER.md](ACADEMIC_PAPER.md) — Paper planning document

### Alignment Checklist

Before submission, verify:
- [ ] All axioms match [CANON.md](CANON.md) exactly
- [ ] Terminology uses canonical terms from [GLOSSARY.md](GLOSSARY.md)
- [ ] Mathematical formulations are consistent
- [ ] Proofs support all claims
- [ ] Attribution to Greg Brown is present
- [ ] Governance approval obtained ([GOVERNANCE.md](GOVERNANCE.md))

---

## 🚀 **Next Steps**

### For Immediate Use

1. Compile the LaTeX document
2. Review the generated PDF
3. Check all mathematical notation
4. Verify proof logic

### For Publication

1. Add musical examples using TikZ or musixtex
2. Include bibliography and references
3. Add author affiliations and acknowledgments
4. Format according to target journal style
5. Submit for peer review

### For Software Implementation

The mathematical formulations can be directly translated to:
- Python (`sympy` for symbolic math)
- JavaScript/TypeScript
- Haskell (for formal verification)
- Lean/Coq (for proof assistants)

---

## 📚 **Resources**

### LaTeX References

- [Overleaf Documentation](https://www.overleaf.com/learn)
- [The Not So Short Introduction to LaTeX](https://tobi.oetiker.ch/lshort/lshort.pdf)
- [LaTeX Mathematics Guide](https://en.wikibooks.org/wiki/LaTeX/Mathematics)

### Music Theory in LaTeX

- [musixtex Documentation](http://icking-music-archive.org/software/musixtex/)
- [lilyglyphs Package](https://ctan.org/pkg/lilyglyphs)

### Mathematical Typesetting

- [AMS-LaTeX Guide](ftp://ftp.ams.org/pub/tex/doc/amsmath/amsldoc.pdf)
- [Comprehensive LaTeX Symbol List](http://tug.ctan.org/info/symbols/comprehensive/symbols-a4.pdf)

---

## 🛡️ **Version Control**

This is **LaTeX Document v1.0** — First complete formal version.

Changes require governance approval (see [GOVERNANCE.md](GOVERNANCE.md)).

---

## 📞 **Support**

For questions about:
- **Mathematical content**: Refer to [FORMAL_PROOFS.md](FORMAL_PROOFS.md)
- **Canonical alignment**: Check [CANON.md](CANON.md)
- **Terminology**: See [GLOSSARY.md](GLOSSARY.md)
- **LaTeX compilation**: Consult Overleaf documentation

---

**Formal mathematics serves as the rigorous foundation for intuitive understanding.**
