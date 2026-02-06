# Zone–Tritone System Architecture

## 📐 Project Overview

The Zone–Tritone System consists of three integrated layers:

```
┌────────────────────────────────────────────────────────┐
│                  CANONICAL THEORY                       │
│  (CANON.md, GLOSSARY.md, PEDAGOGY.md, GOVERNANCE.md)  │
│         Immutable axioms & frozen terminology           │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│                  PYTHON LIBRARY                         │
│              (src/zone_tritone/*.py)                    │
│    Mathematical implementation & analysis tools         │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│              COMMAND-LINE INTERFACE                     │
│                  (zt-gravity CLI)                       │
│        Practical tooling for musicians/educators        │
└────────────────────────────────────────────────────────┘
```

---

## 🧩 Module Architecture

### Layer 1: Core Data Structures

```python
types.py
  ├─ PitchClass = int          # 0-11 representing C-B
  ├─ TritoneAxis = tuple[int, int]  # (pc1, pc2) where pc2 = (pc1 + 6) % 12
  ├─ RootSequence = list[int]  # Sequence of pitch class roots
  └─ Matrix = list[list[float]]  # 12×12 transition probability matrix
```

### Layer 2: Fundamental Operations

```python
pc.py (Pitch Class Operations)
  ├─ pc_from_name(note: str) -> int
  │   └─ Maps "C", "C#", "Db" → 0-11
  ├─ pc_to_name(pc: int) -> str
  │   └─ Canonical names only (C C# D D# E F F# G G# A A# B)
  └─ CANONICAL_NAMES: tuple[str, ...]
      └─ Frozen 12-note reference
```

```python
zones.py (Zone Membership)
  ├─ zone(pc: int) -> int
  │   └─ Returns 0 or 1 (Zone 1 or Zone 2)
  │   └─ Formula: pc % 2
  ├─ is_zone_crossing(pc1: int, pc2: int) -> bool
  │   └─ Half-step test: abs(pc1 - pc2) % 12 == 1
  └─ is_zone_stable(pcs: list[int]) -> bool
      └─ Checks if all notes share same zone
```

```python
tritones.py (Tritone Operations)
  ├─ tritone_partner(pc: int) -> int
  │   └─ Formula: (pc + 6) % 12
  ├─ tritone_axis(pc: int) -> TritoneAxis
  │   └─ Returns sorted (pc, partner) pair
  ├─ all_tritone_axes() -> list[TritoneAxis]
  │   └─ Generates 6 unique axes: [(0,6), (1,7), (2,8), (3,9), (4,10), (5,11)]
  └─ are_tritones_equivalent(ax1, ax2) -> bool
      └─ Checks if (a,b) == (b,a) or (a,b) == (c,d)
```

### Layer 3: Harmonic Analysis

```python
gravity.py (Dominant Function)
  ├─ dominant_roots_from_tritone(ax: TritoneAxis) -> tuple[int, int]
  │   └─ Returns two roots where tritone acts as 3rd & 7th
  │   └─ Formula: r1 = (low - 5) % 12, r2 = (high + 1) % 12
  └─ gravity_chain(start_pc: int, steps: int) -> RootSequence
      └─ Generates descending 4ths: [r₀, r₁, ..., rₙ]
      └─ Formula: rᵢ = (r₀ - 7·i) % 12  (descending perfect 4th = -5 semitones)
```

```python
corpus.py (Chord Parsing)
  └─ parse_root(chord_symbol: str) -> int | None
      └─ Extracts root from "Dm7", "F#maj7", "Bb7#9" → pitch class
      └─ Returns None for unparseable symbols
```

```python
markov.py (Transition Analysis)
  ├─ transition_counts(roots: RootSequence) -> Matrix
  │   └─ Counts rᵢ → rᵢ₊₁ transitions, returns 12×12 matrix
  ├─ normalize_matrix(counts: Matrix) -> Matrix
  │   └─ Converts counts to probabilities (rows sum to 1.0)
  ├─ laplace_smooth(matrix: Matrix, alpha: float) -> Matrix
  │   └─ Adds smoothing to prevent zero probabilities
  └─ sample_next(matrix: Matrix, current_pc: int) -> int
      └─ Stochastic sampling using transition probabilities
```

### Layer 4: Public API

```python
__init__.py
  └─ Exports 20+ functions:
      ├─ Pitch class: pc_from_name, pc_to_name, CANONICAL_NAMES
      ├─ Zones: zone, is_zone_crossing, is_zone_stable
      ├─ Tritones: tritone_partner, tritone_axis, all_tritone_axes
      ├─ Gravity: dominant_roots_from_tritone, gravity_chain
      ├─ Corpus: parse_root
      └─ Markov: transition_counts, normalize_matrix, laplace_smooth, sample_next
```

### Layer 5: Command-Line Interface

```python
cli.py
  ├─ _parse_chord_string(s: str) -> list[str]
  │   └─ Splits space-separated chord symbols
  ├─ _load_chords_from_file(path: Path) -> list[str]
  │   └─ Reads multi-line chord files
  ├─ cmd_gravity(args: Namespace) -> int
  │   └─ Handler: zt-gravity gravity --root G --steps 7
  │   └─ Displays gravity chain with zone annotations
  ├─ cmd_analyze(args: Namespace) -> int
  │   └─ Handler: zt-gravity analyze --chords "..." | --file ...
  │   └─ Computes transition statistics, optional matrix display
  ├─ build_arg_parser() -> ArgumentParser
  │   └─ Creates subparsers for gravity and analyze
  └─ main(argv: list[str] | None) -> int
      └─ Entry point with command routing
```

---

## 🔄 Data Flow Diagrams

### Gravity Chain Generation

```
User Input: "G"
     ↓
pc_from_name("G") → 7
     ↓
gravity_chain(7, steps=7)
     ↓
Formula: rᵢ = (7 - 7·i) % 12
     ↓
Sequence: [7, 0, 5, 10, 3, 8, 1, 6]
     ↓
pc_to_name(each) → ["G", "C", "F", "Bb", "Eb", "Ab", "C#", "F#"]
     ↓
zone(each) → [1, 0, 1, 0, 1, 0, 1, 0]
     ↓
CLI Output:
  0: G    (pc= 7, Zone 2)
  1: C    (pc= 0, Zone 1)
  2: F    (pc= 5, Zone 2)
  ...
```

### Chord Progression Analysis

```
User Input: "Dm7 G7 Cmaj7"
     ↓
_parse_chord_string() → ["Dm7", "G7", "Cmaj7"]
     ↓
parse_root(each) → [2, 7, 0]  (D, G, C)
     ↓
transition_counts([2, 7, 0])
     ↓
12×12 Matrix:
  matrix[2][7] += 1  (D → G)
  matrix[7][0] += 1  (G → C)
     ↓
normalize_matrix() → Probabilities
     ↓
Statistics:
  - Total transitions: 2
  - Descending 4ths: 2 (100%)
  - Zone crossings: identify via is_zone_crossing()
     ↓
CLI Output:
  # Root sequence: 2:D 7:G 0:C
  # Total transitions: 2
  # Descending 4th motion: 2 (100.0%)
```

---

## 📦 Packaging & Distribution

### Build System

```
pyproject.toml
  ├─ [build-system]
  │   └─ requires = ["setuptools>=64"]
  ├─ [project]
  │   ├─ name = "zone-tritone"
  │   ├─ version = "0.1.0"
  │   ├─ requires-python = ">=3.10"
  │   └─ dependencies = []  # No external dependencies
  └─ [project.scripts]
      └─ zt-gravity = "zone_tritone.cli:main"
```

### Installation Flow

```
pip install -e .
     ↓
setuptools builds package
     ↓
Creates .venv/Scripts/zt-gravity.exe (Windows)
     ↓
Console script wraps zone_tritone.cli:main()
     ↓
User can run: zt-gravity <command>
```

### Module Execution

```
python -m zone_tritone.cli
     ↓
Loads zone_tritone/__main__.py
     ↓
Imports cli.main()
     ↓
sys.exit(main())
```

---

## 🧪 Testing Architecture

### Test Organization

```
tests/
  ├─ test_pc.py           # Unit tests for pitch class operations
  ├─ test_zones.py        # Unit tests for zone calculations
  ├─ test_tritones.py     # Unit tests for tritone functions
  ├─ test_gravity.py      # Unit tests for gravity chains
  ├─ test_markov.py       # Unit tests for Markov models
  └─ test_cli_smoke.py    # Integration tests for CLI commands
```

### Test Patterns

**Unit Tests** (pc, zones, tritones, gravity, markov):
```python
def test_feature():
    # Arrange: Setup test data
    input_data = ...
    
    # Act: Call function under test
    result = function_under_test(input_data)
    
    # Assert: Verify expected behavior
    assert result == expected_value
```

**CLI Smoke Tests** (test_cli_smoke.py):
```python
def test_cli_command():
    # Execute CLI as subprocess
    result = subprocess.run(
        ["python", "-m", "zone_tritone.cli", "command", "--args"],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    # Verify execution success
    assert result.returncode == 0
    
    # Check output contains expected patterns
    output = result.stdout + result.stderr
    assert "expected text" in output
```

---

## 📚 Documentation Hierarchy

```
Root Documentation (Canonical Theory)
  ├─ CANON.md               # 5 immutable axioms
  ├─ GLOSSARY.md            # Frozen terminology
  ├─ PEDAGOGY.md            # Six-level teaching sequence
  ├─ GOVERNANCE.md          # Change approval process
  ├─ BRAND_STYLE_GUIDE.md   # Visual identity
  ├─ NOTATION_CONVENTIONS.md # Musical notation standards
  ├─ THEORY_DIAGRAMS.md     # Standard diagrams
  ├─ INSTRUCTOR_CERTIFICATION.md # Three-tier program
  ├─ STUDENT_ASSESSMENT_RUBRICS.md # Evaluation
  └─ FAQ.md                 # Common questions

Implementation Documentation
  ├─ README.md              # Project overview + quickstart
  ├─ PYTHON_PACKAGE.md      # Complete API reference
  ├─ CLI_DOCUMENTATION.md   # CLI user guide
  ├─ PROJECT_STRUCTURE.md   # Repository map
  ├─ CHANGELOG.md           # Version history
  └─ ARCHITECTURE.md        # This file

Educational Resources
  ├─ demo.py                # Interactive demonstration
  └─ examples/
      ├─ melodic-minor.md
      ├─ tritone-motion.md
      └─ dominant-chains.md

Academic Papers
  └─ papers/
      ├─ zone_tritone_canon_short.tex       (5 pages)
      └─ zone_tritone_canon_extended.tex    (15+ pages)
```

---

## 🔐 Governance & Canon Protection

### Change Control Matrix

| Component | Change Type | Approval Required |
|-----------|-------------|-------------------|
| CANON.md | Any edit | Founder approval + written proposal |
| GLOSSARY.md | Any edit | Founder approval + written proposal |
| PEDAGOGY.md | Any edit | Founder approval + written proposal |
| GOVERNANCE.md | Any edit | Founder approval + written proposal |
| Python code | Bug fix | Code review |
| Python code | New feature | Alignment check + tests |
| CLI commands | New subcommand | Canon consistency check |
| Documentation | Clarification | Terminology alignment |
| Examples | New example | Canon compliance |
| Tests | New test | Coverage improvement |

### Canon Validation Checks

Before any commit:
```bash
# 1. Terminology check
grep -r "non-canonical-term" . --exclude-dir=.venv

# 2. Attribution check
grep -r "Ross Echols" . --exclude-dir=.venv  # Should be empty

# 3. Test suite
pytest -v

# 4. CLI smoke test
zt-gravity gravity --root C --steps 4
zt-gravity analyze --chords "Dm7 G7 Cmaj7"
```

---

## 🚀 Future Architecture Expansions

### Phase 1: Enhanced CLI
```
zt-gravity explain --chords "..." → Verbose pedagogical analysis
zt-gravity visualize --chords "..." → ASCII/SVG diagram generation
zt-gravity validate --file song.txt → Canon compliance checker
```

### Phase 2: Web API
```
FastAPI backend
  ├─ /api/v1/gravity/chain → JSON endpoint
  ├─ /api/v1/analyze/progression → Transition analysis
  └─ /api/v1/explain/chord → Teaching-friendly output
```

### Phase 3: Interactive Tools
```
Jupyter notebooks
  ├─ zone_tritone_tutorial.ipynb
  ├─ corpus_analysis.ipynb
  └─ visualization_examples.ipynb

Web dashboard
  ├─ Real-time chord input
  ├─ Gravity map visualization
  └─ Corpus statistics browser
```

### Phase 4: Integration Plugins
```
VS Code extension
  ├─ Syntax highlighting for chord symbols
  ├─ Real-time analysis sidebar
  └─ Zone-crossing detection

DAW plugins (Ableton, Logic)
  ├─ MIDI analysis
  ├─ Harmonic suggestions
  └─ Voice-leading checker
```

---

## 🎯 Design Principles

### Code Quality
✔ **Type hints everywhere**: All functions fully annotated  
✔ **Zero external dependencies**: Pure Python implementation  
✔ **100% test coverage**: Unit tests for all functions  
✔ **Immutable data**: Functions return new values, never mutate  
✔ **Pure functions**: No side effects except CLI output  

### API Design
✔ **Consistent naming**: `verb_noun()` pattern (e.g., `parse_root`, `gravity_chain`)  
✔ **Clear types**: PitchClass = int (0-11), Zone = int (0-1)  
✔ **Predictable returns**: Always int, tuple, list, or Matrix  
✔ **Error handling**: None for invalid input, not exceptions  
✔ **Documentation**: Docstrings with examples and formulas  

### CLI Design
✔ **Unix philosophy**: Do one thing well  
✔ **Composable**: Pipe-friendly output  
✔ **Help text**: --help for every command  
✔ **File support**: Read from files or stdin  
✔ **Exit codes**: 0 = success, 1 = error  

### Canonical Alignment
✔ **Terminology**: Use GLOSSARY.md frozen terms only  
✔ **Attribution**: Greg Brown credited in all materials  
✔ **Pedagogy**: Code structure mirrors PEDAGOGY.md levels  
✔ **Governance**: Major changes require approval  

---

**The architecture serves the theory — never overshadows it.**

See [GOVERNANCE.md](GOVERNANCE.md) for change approval process.  
See [PYTHON_PACKAGE.md](PYTHON_PACKAGE.md) for complete API reference.  
See [CLI_DOCUMENTATION.md](CLI_DOCUMENTATION.md) for CLI user guide.
