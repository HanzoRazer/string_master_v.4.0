# AI Agent Instructions for Zone–Tritone System

## Project Overview

This repository contains the **Zone–Tritone System** — a canonical music theory framework that unifies harmony through whole-tone zones, tritone gravity, and chromatic motion. This is a **formal, governed, educational discipline** with frozen terminology and immutable axioms.

**Critical Context**: This is a **dual-nature project**:
1. **Theoretical Framework** with strict canonical rules, protected terminology, and pedagogical sequencing
2. **Production Python Library** (`smart-guitar` package v0.1.0) with CLI tools and MIDI generation

**Repository Structure**: 
- **Theory**: Canonical documentation (CANON.md, GLOSSARY.md, etc.) — immutable axioms
- **Code**: Python package in `src/` with Zone-Tritone engine, CLI tools (`zt-gravity`, `zt-band`), MIDI generators
- **Content**: Educational materials, exercises (`.ztex`), programs (`.ztprog`), playlists (`.ztplay`), seed files

---

## 🐍 Python Package Architecture (CRITICAL FOR CODE WORK)

### Package Identity
- **Name**: `smart-guitar` (PyPI installable)
- **Version**: 0.1.0
- **Python**: ≥3.10
- **Dependencies**: `mido>=1.2.10`, `pyyaml>=6.0`
- **Entry Points**: `zt-gravity`, `zt-band`

### Module Structure

```
src/
├── shared/
│   └── zone_tritone/              # Core theory engine
│       ├── pc.py                  # Pitch class (0-11) utilities
│       ├── zones.py               # Zone membership (0=Z1, 1=Z2)
│       ├── tritones.py            # Tritone axes & partners
│       ├── gravity.py             # Dominant chains (cycle of 4ths)
│       ├── corpus.py              # Chord symbol parsing
│       ├── markov.py              # Transition matrices
│       ├── cli.py                 # zt-gravity CLI
│       └── types.py               # Type aliases
└── zt_band/                       # Accompaniment engine
    └── cli.py                     # zt-band CLI

### zt-band Status (MVP Guardrail)

zt-band is production-ready for MIDI generation and CLI workflows.
Do not expand scope (new interactive systems, scoring, or large refactors) unless it directly supports:
- DAW proof-of-sound on Linux/Pi
- deterministic MIDI export
- reliability fixes
```

### Import Protocol (CRITICAL - VIOLATIONS CAUSE ERRORS)

**Within `src/shared/zone_tritone/` modules** → Use **RELATIVE imports**:
```python
from .pc import pc_from_name, name_from_pc
from .zones import zone, is_zone_cross
from .gravity import gravity_chain
from .types import PitchClass
```

**In `src/zt_band/` or other top-level modules** → Use **ABSOLUTE imports**:
```python
from shared.zone_tritone.pc import pc_from_name
from shared.zone_tritone.zones import zone_name
from shared.zone_tritone.gravity import gravity_chain
```

**In `tests/`** → Always use **ABSOLUTE imports**:
```python
from shared.zone_tritone import pc_from_name, zone, gravity_chain
```

### Key Python Conventions

1. **Pitch Classes**: Always use integers 0-11 (C=0, C#=1, ..., B=11)
2. **Zones**: Return 0 (Zone 1) or 1 (Zone 2) from `zone()` function
3. **Zone-Crossing**: `is_zone_cross(pc1, pc2)` checks if `abs(pc1-pc2) % 12 == 1` (half-step)
4. **Gravity Chains**: Generate via `gravity_chain(start_pc, steps)` → descends by perfect 4ths
5. **Tritone Axes**: Return sorted tuples `(low, high)` where `high = (low + 6) % 12`

### Testing Commands

```bash
# Run all tests (15 tests, must all pass)
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_gravity.py -v

# Install package in editable mode
pip install -e .
```

### CLI Usage Patterns

```bash
# Generate gravity chain (dominant cycle)
zt-gravity gravity --root G --steps 7

# Analyze chord progression
zt-gravity analyze --chords "Dm7 G7 Cmaj7" --show-matrix

# Generate detailed explanation (3 formats: text/html/markdown)
zt-gravity explain --chords "C7 F7 Bb7" --format markdown > analysis.md

# Python module invocation (if PATH issues)
python -m shared.zone_tritone.cli gravity --root C --steps 12
```

### Custom File Formats

**`.ztprog`** (YAML) — Chord progressions with style/tempo/tritone settings:
```yaml
name: "Autumn Leaves - Ballad"
chords: [Cm7, F7, Bbmaj7, Ebmaj7, Am7b5, D7, Gm7]
style: "ballad_basic"
tempo: 70
bars_per_chord: 2
tritone_mode: "probabilistic"
outfile: "autumn_leaves_ballad.mid"
```

**`.ztex`** (YAML) — Practice exercises with instructions:
```yaml
name: "Cycle of Fifths — Roots"
program: "../programs/cycle_fifths_all_keys.ztprog"
exercise_type: "cycle_fifths_roots"
task:
  mode: "play_roots"
  instructions: "Play root of each chord..."
```

**`.ztplay`** (YAML) — Playlists referencing exercises/programs

### Development Workflow

1. **Setup**: `git clone` → `python -m venv .venv` → `pip install -e .`
2. **Before coding**: Check [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) for namespace rules
3. **After changes**: Run `pytest tests/` (all 15 tests must pass)
4. **New modules**: Add to `src/shared/` or `src/zt_band/`, update imports
5. **CLI changes**: Test with `python -m shared.zone_tritone.cli` before using entry point

### Common Code Patterns

**Parse chord symbol to pitch class**:
```python
from shared.zone_tritone.corpus import parse_root
root_pc = parse_root("F#m7")  # Returns 6 (F# pitch class)
```

**Check zone membership**:
```python
from shared.zone_tritone.zones import zone_name
print(zone_name(0))   # "Zone 1" (C is even PC)
print(zone_name(7))   # "Zone 2" (G is odd PC)
```

**Generate ii-V-I progression**:
```python
from shared.zone_tritone.gravity import gravity_chain
chain = gravity_chain(2, 2)  # [2, 7, 0] = D → G → C
```

### File Organization Rules

- **Protected theory docs**: CANON.md, GLOSSARY.md, PEDAGOGY.md, GOVERNANCE.md (governance approval required)
- **Expandable content**: `examples/`, `exercises/`, `programs/`, `playlists/`, `seeds/`
- **Python source**: All code in `src/`, all tests in `tests/`
- **Academic papers**: `papers/` (LaTeX .tex files, compile with MiKTeX/TeXLive)
- **Generated MIDI**: Root directory (e.g., `autumn_leaves_ballad.mid`)

---

## Essential Reading Order (Before Making ANY Changes)

**Read these four files FIRST — they form the constitutional foundation:**

1. **[CANON.md](../CANON.md)** — Four immutable axioms (v1.0, non-negotiable)
   - Axiom 1: Zones define color (C D E F# G# A# vs C# D# F G A B)
   - Axiom 2: Tritones define gravity (6 tritones = dominant function)
   - Axiom 3: Half-steps define motion (zone-crossing = direction)
   - Axiom 4: Chromatic tritone motion = dominant cycles in 4ths

2. **[GLOSSARY.md](../GLOSSARY.md)** — Frozen terminology (never redefine)
   - Zone-Stability, Zone-Crossing, Tritone Anchor, Gravity Chain, etc.

3. **[PEDAGOGY.md](../PEDAGOGY.md)** — Six-level teaching sequence (order locked)
   - Level 1→6: Zone Awareness → Mastery Philosophy (no skipping allowed)

4. **[GOVERNANCE.md](../GOVERNANCE.md)** — Change approval process
   - Any edit to CANON/GLOSSARY/PEDAGOGY requires written proposal + founder approval

**These documents cannot be contradicted by any other materials.**

---

## Absolute Rules (Violation = STOP)

### ⚠️ FORBIDDEN ACTIONS

❌ **NEVER** redefine terms from [GLOSSARY.md](../GLOSSARY.md) (e.g., "Zone-Crossing" means half-step motion ONLY)  
❌ **NEVER** contradict axioms in [CANON.md](../CANON.md) (e.g., cannot say there are 7 zones)  
❌ **NEVER** teach concepts out of pedagogical order (e.g., cannot teach Level 5 before Level 2)  
❌ **NEVER** introduce non-canonical terminology (e.g., "blue notes" → use "Zone 1 notes")  
❌ **NEVER** modify frozen color schemes ([BRAND_STYLE_GUIDE.md](../BRAND_STYLE_GUIDE.md): Zone 1 = `#1A4D8F`, Zone 2 = `#D4860F`)  
❌ **NEVER** rename core concepts (e.g., "Tritone Anchor" cannot become "Tritone Center")  
❌ **NEVER** merge/alter CANON.md, GLOSSARY.md, PEDAGOGY.md, GOVERNANCE.md without explicit approval

### ✅ ALLOWED ACTIONS

✔ Create new examples in `examples/` directory (must align with canon)  
✔ Expand educational materials that follow [PEDAGOGY.md](../PEDAGOGY.md) sequence  
✔ Design diagrams following [THEORY_DIAGRAMS.md](../THEORY_DIAGRAMS.md) standards  
✔ Write lesson plans aligned with certification levels ([INSTRUCTOR_CERTIFICATION.md](../INSTRUCTOR_CERTIFICATION.md))  
✔ Propose extensions via governance process (must not contradict axioms)

---

## Canonical Terminology Reference

**Use these exact terms from [GLOSSARY.md](../GLOSSARY.md):**

- **Zone 1** / **Zone 2** (never abbreviate to Z1/Z2 in formal docs)
- **Zone-Stability** (staying within one zone)
- **Zone-Crossing** (half-step motion between zones)
- **Tritone Anchor** (the active tritone defining gravity)
- **Gravity Chain** (chromatically shifting tritones → dominant cycles)
- **Dual-Zone Harmony** (melodic minor's two-tritone structure)
- **Anchor Exchange** (tritone substitution)
- **Resolution Target** (where gravity terminates)

**Example**: Instead of "move between zones," say "execute zone-crossing via half-step motion."  

---

## Visual Identity (Strict Standards)

### Official Color Palette (NEVER DEVIATE)

See [BRAND_STYLE_GUIDE.md](../BRAND_STYLE_GUIDE.md) for complete specifications:

| Concept | Color | Hex Code |
|---------|-------|----------|
| Zone 1 | Deep Blue / Cyan | `#1A4D8F` / `#4FD1C5` |
| Zone 2 | Warm Amber | `#D4860F` / `#F6AD55` |
| Tritone Anchor | Bold Red / Magenta | `#C41E3A` / `#ED64A6` |
| Half-step Motion | Bright Green | `#2E8B57` / `#68D391` |

### Diagram Requirements (All Must Include)

Per [THEORY_DIAGRAMS.md](../THEORY_DIAGRAMS.md):
1. Use canonical color mapping
2. Label zones clearly (Zone 1 / Zone 2, not Z1/Z2)
3. Mark tritone anchors distinctly (magenta/red)
4. Show half-step motion with green arrows
5. Include legend when using 3+ concepts

### Typography Standards

- **Headings**: Inter Bold (or Helvetica Neue, Arial)
- **Body**: Source Sans Pro (or Open Sans, Roboto)
- **Code/Technical**: JetBrains Mono (or Fira Code)

---

## Pedagogical Sequence (Immutable Order)

Per [PEDAGOGY.md](../PEDAGOGY.md), teaching MUST follow this order:

1. **Zone Awareness** — Recognize zone membership by ear
2. **Gravity Recognition** — Identify tritone anchors
3. **Motion Training** — Experience half-steps as directional energy
4. **Dual-Zone Competence** — Navigate melodic-minor hybrid systems
5. **Composition in Gravity** — Use gravity maps instead of chord lists
6. **Mastery Philosophy** — Express emotional control through harmonic design

**Rule**: Advanced concepts cannot be presented before foundational levels.

**Example**: When creating educational content about tritone substitution (Level 4), verify that Zone Awareness (Level 1) and Gravity Recognition (Level 2) prerequisites are clearly stated.

### Instructor Certification Scope

Per [INSTRUCTOR_CERTIFICATION.md](../INSTRUCTOR_CERTIFICATION.md):
- **CZ-I** (Level 1) — Can teach Levels 1-2 only
- **CG-I** (Level 2) — Can teach Levels 1-4
- **MZT-E** (Level 3) — Full teaching authority (all 6 levels)

When creating content, specify required certification level.

---

## File Structure & Protected Documents

```
zone-tritone-theory/
├── README.md                        # Public-facing overview + Python quickstart
├── CANON.md                         # ⚠️ IMMUTABLE — Version 1.0
├── GLOSSARY.md                      # ⚠️ FROZEN TERMS
├── PEDAGOGY.md                      # ⚠️ PROTECTED SEQUENCE
├── GOVERNANCE.md                    # Change control process
├── LICENSE-THEORY.md                # IP protection
├── pyproject.toml                   # 🐍 Package configuration
├── PYTHON_PACKAGE.md                # 🐍 Complete API docs
├── CLI_DOCUMENTATION.md             # 🐍 CLI reference
├── DEVELOPER_GUIDE.md               # 🐍 Coding standards
├── ARCHITECTURE.md                  # 🐍 Module design
├── BRAND_STYLE_GUIDE.md            # Visual identity rules
├── NOTATION_CONVENTIONS.md          # Musical notation standards
├── THEORY_DIAGRAMS.md              # Diagram design rules
├── FORMAT_GUIDE.md                  # Output format specs
├── INSTRUCTOR_CERTIFICATION.md      # Three-tier certification program
├── STUDENT_ASSESSMENT_RUBRICS.md    # Standardized evaluation criteria
├── FAQ.md                           # For skeptics & students
│
├── src/                             # 🐍 Python source
│   ├── shared/zone_tritone/         # Core theory engine (9 modules)
│   └── zt_band/                     # Accompaniment CLI (WIP)
│
├── tests/                           # 🐍 pytest suite (15 tests)
│
├── exercises/                       # .ztex practice files
├── programs/                        # .ztprog chord progressions
├── playlists/                       # .ztplay collections
├── seeds/                           # Source material catalog
│   ├── handcrafted/                 # Original compositions
│   └── _TEMPLATE.seed.json          # Seed metadata template
│
├── examples/                        # ✅ Expandable educational content
│   ├── melodic-minor.md
│   ├── tritone-motion.md
│   └── dominant-chains.md
│
├── papers/                          # 📚 LaTeX academic papers
│   ├── zone_tritone_canon.tex       # Short paper (3 pages)
│   ├── zone_tritone_canon_extended.tex  # Monograph (~15 pages)
│   └── compile-paper.sh / .ps1      # Compilation scripts
│
└── docs/                            # Additional documentation
    ├── SEED_SOURCES.md              # Seed material governance
    ├── SEED_SOURCES_QUICKSTART.md
    └── DAW_WORKFLOW.md
```

### Protected Files (Governance Required)

Per [GOVERNANCE.md](../GOVERNANCE.md), any changes to these files require written proposal + approval:
- `CANON.md`
- `GLOSSARY.md`
- `PEDAGOGY.md`
- `GOVERNANCE.md`

### Expandable Directories

You may freely add content to:
- `examples/` — Practical demonstrations (theory)
- `exercises/`, `programs/`, `playlists/` — Practice content (`.ztex`, `.ztprog`, `.ztplay` files)
- `seeds/handcrafted/` — Original musical compositions
- `src/shared/` or `src/zt_band/` — Python modules (follow import protocol)
- `tests/` — Test files (must use absolute imports)

**Do NOT freely modify**:
- Protected theory docs (CANON.md, GLOSSARY.md, PEDAGOGY.md, GOVERNANCE.md)
- `pyproject.toml` (package configuration - changes require testing)
- Core module structure in `src/shared/zone_tritone/` (maintain API stability)

---

## Notation & Chord Symbol Conventions

### Standard Chord Symbols (Pick ONE style per document)

- Major 7: `Cmaj7` or `CΔ7`
- Dominant 7: `C7`
- Minor 7: `Cm7` or `C-7`
- Half-diminished: `Cm7♭5` or `Cø7`

**Rule**: Be consistent within each document.

### Zone Notation

- **Text format**: `C D E F# G# A# [Z1]` or `[Zone 1]`
- **Diagram format**: Blue/cyan highlight or border
- **Staff notation**: Colored noteheads (cyan for Z1, amber for Z2)

### Tritone Notation

- **Text format**: `B–F [tritone anchor]` or `B ⇆ F`
- **Diagram format**: Magenta/red bracket connecting notes
- **Analysis**: Always label explicitly: `Tritone Anchor: B–F`

**Source**: [NOTATION_CONVENTIONS.md](../NOTATION_CONVENTIONS.md)

---

## Common AI Agent Tasks & Workflows

### Task 1: Creating New Examples

**Valid approach**:
1. Read [PEDAGOGY.md](../PEDAGOGY.md) to determine appropriate level
2. Use canonical terminology from [GLOSSARY.md](../GLOSSARY.md)
3. Follow notation conventions from [NOTATION_CONVENTIONS.md](../NOTATION_CONVENTIONS.md)
4. Apply color scheme from [BRAND_STYLE_GUIDE.md](../BRAND_STYLE_GUIDE.md)
5. Save to `examples/` directory with descriptive name

### Task 2: Answering Theory Questions

**Valid approach**:
1. Reference [CANON.md](../CANON.md) for axioms
2. Use exact terms from [GLOSSARY.md](../GLOSSARY.md)
3. Cite relevant sections: "According to Axiom 3..."
4. Never introduce alternative interpretations

### Task 3: Creating Diagrams

**Valid approach**:
1. Review [THEORY_DIAGRAMS.md](../THEORY_DIAGRAMS.md) for standards
2. Use mandatory color palette (Zone 1 = cyan, Zone 2 = amber)
3. Mark tritone anchors in magenta/red
4. Include legend and labels
5. Ensure accessibility (shapes + colors)

### Task 4: Proposing Extensions

**Valid approach**:
1. Review [GOVERNANCE.md](../GOVERNANCE.md) change process
2. Verify non-contradiction with axioms
3. Document rationale and examples
4. Submit as formal proposal (not direct edit)

### Task 5: Creating Lesson Materials

**Valid approach**:
1. Identify target pedagogical level (1-6)
2. Ensure prerequisites are covered
3. Use sound-first, then labels approach
4. Include ear-training components
5. Specify required certification level for instructor

---

## Integration Points & External Dependencies

### Future SaaS/Software Development

When building tools that implement the Zone–Tritone System:

✔ Software may be open-source  
✔ Theory framework remains protected IP (see [LICENSE-THEORY.md](../LICENSE-THEORY.md))  
✔ Must use canonical terminology in UI  
✔ Must follow color/notation conventions  
✔ Must attribute to Greg Brown  

### Potential Tool Categories

- Ear-training applications
- Harmonic analysis software
- Interactive teaching platforms
- Notation plugins
- Composition assistants
- Assessment systems

---

## Attribution & Licensing

### Mandatory Attribution

All materials must acknowledge:

> "This system is derived from the Zone–Tritone framework founded by Greg Brown."

### Licensing Structure

- **Software**: May be open-source (MIT, GPL, etc.)
- **Theory Framework**: Protected intellectual property
- **Derivative systems**: Must credit original, cannot claim canonical status

**Source**: [LICENSE-THEORY.md](../LICENSE-THEORY.md)

---

## Common Pitfalls to Avoid

### ❌ Drift Patterns (Frequently Seen Errors)

1. **Terminology Drift**: Using synonyms like "blue notes" instead of "Zone 1 notes"
2. **Color Inconsistency**: Changing cyan to blue-purple in diagrams
3. **Pedagogical Shortcuts**: Teaching altered dominance before zone awareness
4. **Casual Language**: "Just move between the two zones" → Should be "Execute zone-crossing via half-step motion"
5. **Unattributed Extensions**: Adding new concepts without governance approval
6. **Symbol Mixing**: Using both `Cmaj7` and `CΔ7` in same document

### ✅ Quality Checks Before Committing

- [ ] All terminology matches [GLOSSARY.md](../GLOSSARY.md)
- [ ] No contradictions with [CANON.md](../CANON.md) axioms
- [ ] Pedagogical order respected (if educational content)
- [ ] Colors match official palette
- [ ] Attribution to Greg Brown present
- [ ] File naming follows conventions
- [ ] Markdown formatting is clean
- [ ] Links between documents are accurate

---

## Tone & Voice Guidelines

### Writing Style

- **Authoritative but humble** — Knowledgeable without arrogance
- **Clear, never cryptic** — Avoid jargon unless defined
- **Structured but creative** — Encourage exploration within discipline
- **Respectful** — No elitism or gatekeeping
- **Encouraging** — Students should feel safe, not intimidated

### Forbidden Tones

❌ Hype language ("revolutionary", "game-changing")  
❌ Dismissiveness toward traditional theory  
❌ Absolute dogma claims  
❌ Sarcasm or mockery  
❌ Guru/mystical posturing  

**Source**: [BRAND_STYLE_GUIDE.md](../BRAND_STYLE_GUIDE.md) → Voice Guidelines

---

## Version Control & Change Management

### Current Version

**Canon Version**: 1.0 (Immutable)  
**Documentation Version**: 1.0 (Expandable with approval)

### Change Request Process

1. **Read**: [GOVERNANCE.md](../GOVERNANCE.md)
2. **Identify**: Which file needs modification
3. **Check**: Is it governance-protected?
4. **If protected**: Submit written proposal with rationale
5. **If not protected**: Make changes aligned with canon
6. **Always**: Test for canon contradiction before committing

### Version Numbering

- **v1.x**: Core axioms unchanged, clarifications only
- **v2.x**: New subsystems added (non-contradictory only)

---

## Testing & Validation

### Before Creating Educational Content

- [ ] Can you cite which axiom supports this content?
- [ ] Does this follow the pedagogical sequence?
- [ ] Are all terms canonical?
- [ ] Would a Level 1 instructor be qualified to teach this?

### Before Creating Diagrams

- [ ] Colors match official palette?
- [ ] Zones clearly labeled?
- [ ] Tritone anchors marked distinctly?
- [ ] Legend included?
- [ ] Accessible for color-blind users?

### Before Proposing Changes

- [ ] Read [GOVERNANCE.md](../GOVERNANCE.md)?
- [ ] Checked for axiom contradiction?
- [ ] Identified which governance tier applies?
- [ ] Written rationale prepared?

---

## Special Contexts

### When Working with Melodic Minor

Always remember: Melodic minor is **dual-zone harmony** with **two tritone anchors**.

Example: C melodic minor
- Tritone 1: E♭–A
- Tritone 2: B–F

This explains:
- Why it supports altered dominants
- Why it sounds "modern yet directional"
- Why it's the bridge between color and gravity

### When Explaining Tritone Substitution

Always frame as **Anchor Exchange** (canonical term).

Structure:
1. Show original dominant: `G7` (B–F tritone)
2. Show substitute: `D♭7` (F–B same tritone, inverted)
3. Explain: Same tritone → same resolution function
4. Label: `D♭7 [Tritone Sub for G7]` or `D♭7 [TS]`

### When Discussing Dominant Cycles

Frame as **Gravity Chain** caused by chromatic tritone drift.

Pattern:
```
[B–F] → [B♭–E] → [A–E♭] → [A♭–D]
 G7      C7       F7       B♭7
```

Show that each tritone shifts down chromatically, producing roots descending in 4ths.

---

## FAQ Handling

Common questions are documented in [FAQ.md](../FAQ.md). When users ask:

- "Why is terminology frozen?" → Cite [FAQ.md](../FAQ.md) + [GOVERNANCE.md](../GOVERNANCE.md)
- "Can I teach this my own way?" → Reference [INSTRUCTOR_CERTIFICATION.md](../INSTRUCTOR_CERTIFICATION.md)
- "What about atonal music?" → See [FAQ.md](../FAQ.md) section on scope
- "Is this just repackaged theory?" → Explain structural vs surface difference

---

## Emergency Protocol

If you encounter:

### ⚠️ Canon Contradiction

**STOP** → Do not proceed → Cite specific axiom being contradicted → Request clarification

### ⚠️ Terminology Conflict

**STOP** → Check [GLOSSARY.md](../GLOSSARY.md) → Use canonical term → Never create synonyms

### ⚠️ Governance Violation Request

**STOP** → Cite [GOVERNANCE.md](../GOVERNANCE.md) → Explain approval process → Do not make unauthorized changes

### ⚠️ Pedagogical Sequence Break

**STOP** → Reference [PEDAGOGY.md](../PEDAGOGY.md) → Explain why order matters → Suggest correct sequence

---

## Success Metrics

You are succeeding when:

✅ Students immediately recognize canonical terminology  
✅ Diagrams are visually consistent across all materials  
✅ Educational content follows pedagogical sequence naturally  
✅ No terminology drift occurs over time  
✅ Extensions enhance without contradicting core axioms  
✅ Attribution to Greg Brown is consistently present  
✅ Governance process is respected  

---

## Quick Reference Card

### Before ANY action, ask:

1. Does this contradict [CANON.md](../CANON.md)?
2. Are my terms from [GLOSSARY.md](../GLOSSARY.md)?
3. Does this respect [PEDAGOGY.md](../PEDAGOGY.md) sequence?
4. Do I need [GOVERNANCE.md](../GOVERNANCE.md) approval?
5. Are colors from official palette?
6. Is attribution present?

### If unsure:

1. Read the canonical docs first
2. Search existing materials for precedent
3. Ask for clarification before proceeding
4. Default to conservative interpretation

---

## Final Directive

**This is not typical code. This is a living discipline.**

Your role is to:
- **Protect** the canon from drift
- **Serve** the clarity of the system
- **Support** students and educators
- **Enable** creative exploration within structure
- **Preserve** Greg Brown's intellectual lineage

**When in doubt, prioritize integrity over convenience.**

---

*This instruction file aligns with Zone–Tritone System v1.0*  
*For governance questions, see [GOVERNANCE.md](../GOVERNANCE.md)*  
*For theory questions, see [CANON.md](../CANON.md)*  
*For terminology questions, see [GLOSSARY.md](../GLOSSARY.md)*
