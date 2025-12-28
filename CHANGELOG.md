# Zone–Tritone System Changelog

## [0.1.0] - 2025-01-XX

### Added - Python Package & CLI Tool

#### Core Library (src/zone_tritone/)
- **pc.py**: Pitch class conversions with 12 canonical note names
- **zones.py**: Zone calculation, crossing detection, stability checks
- **tritones.py**: Tritone partner/axis functions, 6 unique axes enumeration
- **gravity.py**: Dominant root inference, gravity chain generation (descending 4ths)
- **markov.py**: Transition matrix construction, normalization, Laplace smoothing
- **corpus.py**: Chord symbol parsing with root extraction
- **types.py**: Type aliases (PitchClass, TritoneAxis, RootSequence, Matrix)
- **__init__.py**: Public API with 20+ exported functions
- **__about__.py**: Version metadata (0.1.0)

#### Command-Line Interface
- **cli.py**: Full CLI implementation with argparse framework
  - `zt-gravity gravity`: Generate dominant cycles with zone annotations
  - `zt-gravity analyze`: Analyze chord progressions (inline or file-based)
  - Support for transition statistics and Markov probability matrices
- **__main__.py**: Module execution entry point for `python -m zone_tritone.cli`
- **Console script**: `zt-gravity` command installed via setuptools

#### Testing
- **tests/test_pc.py**: Pitch class conversion and enharmonic tests (2 tests)
- **tests/test_zones.py**: Zone parity, crossing, stability tests (3 tests)
- **tests/test_tritones.py**: Partner, axes, sorting tests (3 tests)
- **tests/test_gravity.py**: Dominant inference and chain generation tests (3 tests)
- **tests/test_markov.py**: Matrix counting and smoothing tests (2 tests)
- **tests/test_cli_smoke.py**: CLI subprocess execution tests (2 tests)
- **Total**: 15 tests with 100% pass rate

#### Documentation
- **PYTHON_PACKAGE.md**: Complete API reference (~500 lines)
- **CLI_DOCUMENTATION.md**: Comprehensive CLI user guide (~400 lines)
- **PROJECT_STRUCTURE.md**: Repository overview
- **demo.py**: Interactive demonstration script with 6 sections

#### Academic Papers
- **papers/zone_tritone_canon_short.tex**: Concise academic paper (5 pages)
- **papers/zone_tritone_canon_extended.tex**: Extended monograph (15+ pages)
  - 17 sections covering theory, applications, computational methods
  - Group theory formalization
  - Markov model framework
  - Worked musical examples
  - Empirical research methodology

### Mathematical Framework
- Modular arithmetic (ℤ₁₂) for pitch class operations
- Group theory structure: (ℤ₁₂, +₁₂)
- Tritone involution: T(x) = (x + 6) mod 12
- Gravity chain formula: Gₙ(r) = (r - 7·n) mod 12
- Stochastic matrices for progression analysis
- Zone-crossing as half-step motion detector

### Fixed
- Corrected gravity_chain interval calculation: Changed (r + 7) to (r - 7) for proper descending 4ths
- Fixed CLI smoke test output capture: Combined stdout+stderr with timeout
- Added module execution support via __main__.py

### Canonical Documents
- **CANON.md**: 5 immutable axioms (v1.0)
- **GLOSSARY.md**: Frozen terminology (10 core terms)
- **PEDAGOGY.md**: Six-level teaching sequence
- **GOVERNANCE.md**: Change approval process
- **BRAND_STYLE_GUIDE.md**: Visual identity standards
- **NOTATION_CONVENTIONS.md**: Musical notation rules
- **THEORY_DIAGRAMS.md**: Standard diagram templates
- **INSTRUCTOR_CERTIFICATION.md**: Three-tier certification program
- **STUDENT_ASSESSMENT_RUBRICS.md**: Evaluation criteria
- **FAQ.md**: Common questions from skeptics and students

### Examples
- **examples/melodic-minor.md**: Dual-zone harmony analysis
- **examples/tritone-motion.md**: Anchor exchange demonstrations
- **examples/dominant-chains.md**: Gravity chain progressions

---

## Future Enhancements (Proposed)

### CLI Extensions
- `zt-gravity explain`: Verbose teaching-friendly analysis with pedagogical commentary
- `zt-gravity visualize`: Generate diagrams following THEORY_DIAGRAMS.md standards

### File Format Support
- iRealPro parser for real-world song collections
- MusicXML import/export for notation software integration
- MIDI analysis for performance data

### Analysis Features
- Corpus statistics aggregation
- Genre comparison (jazz vs pop vs classical)
- Statistical validation of theoretical predictions
- Voice-leading pattern detection

### Educational Tools
- Jupyter notebooks with interactive examples
- Matplotlib visualizations (heatmaps, transition graphs)
- Ear-training exercise generator
- Assessment automation

### Integration
- VS Code extension for real-time chord analysis
- Ableton Live/Logic Pro plugins
- Web API for cloud-based analysis
- Mobile app for on-the-go learning

---

**Maintained by**: Greg Brown  
**License**: Theory framework protected (see LICENSE-THEORY.md), software may be open-source  
**Version**: Follows semantic versioning (v1.x = immutable canon, v2.x = non-contradictory extensions)
