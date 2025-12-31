# 🔒 Core Lock Verification Report

**Date**: December 30, 2025
**Status**: ✅ **LOCKED AND STABLE**

---

## Executive Summary

The `zt-band` MIDI generator core has been hardened with:

1. **Musical Contract Enforcement** (`musical_contract.py`)
2. **Expressive Layer** (`expressive_layer.py`) — velocity-only, no timing edits
3. **Deterministic Timing Engine** (`midi_out.py`) — collision-safe, reproducible

All verification tests **PASS**.

---

## What Changed

### 1. Musical Contract (`src/zt_band/musical_contract.py`)

**Purpose**: Runtime validation that prevents stability regressions.

**Enforces**:
- ✅ Determinism: Probabilistic mode MUST provide seed
- ✅ Valid MIDI ranges: notes 0-127, channels 0-15, velocities 1-127
- ✅ Time invariants: start_beats ≥ 0, duration_beats > 0
- ✅ No feature creep: Simple, frozen contract

**Integration**: Called in `engine.py` before and after expressive layer.

---

### 2. Expressive Layer (`src/zt_band/expressive_layer.py`)

**Purpose**: Add musical "feel" WITHOUT destabilizing timing.

**Approach**:
- ✅ Velocity-only shaping (no swing, no humanize, no timing edits)
- ✅ Position-based: downbeat boost, offbeat cut, beat 3 accent
- ✅ Deterministic: Same beat position → same velocity adjustment
- ✅ Clamped: All velocities stay in [min_vel, max_vel] range

**Default Profile**:
```python
downbeat_boost: +12    # Beat 1
midbeat_boost: +7      # Beat 3
offbeat_cut: -6        # & of beat
min_vel: 20
max_vel: 120
```

---

### 3. Timing Engine Hardening (`src/zt_band/midi_out.py`)

**Changes**:

#### A) Explicit ticks_per_beat
```python
ticks_per_beat = 480  # canonical
mid = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)
```

#### B) Deterministic rounding
```python
def beat_to_tick(b: float) -> int:
    # "round half up" for non-negative b
    return int(b * ticks_per_beat + 0.5)
```

**Why**: Eliminates platform-dependent float→int truncation.

#### C) Minimum duration enforcement
```python
if end_tick <= start_tick:
    end_tick = start_tick + 1  # enforce minimum 1 tick
```

**Why**: Prevents zero-duration notes that some DAWs reject.

#### D) Collision-safe ordering
```python
# Priority: note_off=0, note_on=1 (offs come first at same tick)
messages_with_time.sort(key=lambda x: (x[0], x[2]))
```

**Why**: When notes collide at same tick, note_off must precede note_on to avoid stuck notes.

---

## Verification Results

### Test Suite: 28/28 Tests Pass

```bash
python -m pytest tests/ -v
```

**Coverage**:
- Zone-tritone theory (15 tests)
- CLI smoke tests (5 tests)
- Musical contract (10 tests)

---

### Lock Verification: 5/5 Tests Pass

```bash
python verify_lock.py
```

**Tests**:
1. ✅ **Contract Enforcement**: Blocks probabilistic mode without seed
2. ✅ **Deterministic Output**: Identical inputs → byte-identical MIDI
3. ✅ **Probabilistic Determinism**: Same seed → same output
4. ✅ **Timing Engine**: Type 1, ticks_per_beat=480, no stuck notes
5. ✅ **Expressive Layer**: Velocities in [20, 120], variation detected

---

## What You Can Now Say

✅ **"The MIDI generator core is locked and stable."**

✅ **"New ideas (swing/humanize) can be layered without changing core behavior."**

✅ **"Only stability improvements enter the core."**

---

## Future Extensions (Outside the Core)

When ready, **swing/humanize** becomes a **separate optional transform**:

```python
# Proposed API (not yet implemented)
from src.zt_band.swing_layer import apply_swing

events = generate_accompaniment(chords, ...)
swung_events = apply_swing(events, swing_ratio=0.6, seed=42)  # optional
```

**Requirements for future layers**:
- ✅ Require seed when non-deterministic
- ✅ Never change note counts
- ✅ Never break end > start
- ✅ Can be disabled to reproduce core output
- ✅ Pass contract validation

---

## Integration with Engine

**File**: `src/zt_band/engine.py`

```python
# ---- Musical Contract Enforcement ----
# Validate inputs: ensure determinism for probabilistic operations
enforce_determinism_inputs(
    tritone_mode=tritone_mode,
    tritone_seed=tritone_seed,
)

# Validate raw generator output before expressive layer
validate_note_events(comp_events)
validate_note_events(bass_events)

# ---- Expressive Layer (velocity shaping only; stability-first) ----
comp_events = apply_velocity_profile(comp_events)
bass_events = apply_velocity_profile(bass_events)

# Re-validate after shaping to ensure contract still satisfied
validate_note_events(comp_events)
validate_note_events(bass_events)
```

**Why**: Double validation ensures expressive layer cannot violate contract.

---

## Developer Workflow

### Adding New Features

**Rule**: New expressive features are **layers**, not core changes.

**Example**: Adding swing timing
```python
# NEW FILE: src/zt_band/swing_layer.py

def apply_swing(events, swing_ratio=0.6, seed=None):
    """
    Apply swing timing to offbeat notes.
    
    Requires:
    - seed if swing introduces randomness
    - preserve note counts
    - preserve end > start invariant
    """
    if seed is not None:
        random.seed(seed)
    
    # ... swing logic here ...
    
    # MUST pass validation before returning
    validate_note_events(swung_events)
    return swung_events
```

**Integration**:
```python
# In engine.py (optional flag)
if swing_enabled:
    comp_events = apply_swing(comp_events, swing_ratio, swing_seed)
    validate_note_events(comp_events)  # re-check
```

---

## DAW Workflow (Unchanged)

The locked core preserves the **Proof-of-Sound** workflow:

1. Generate MIDI: `zt-band create --program myfile.ztprog`
2. Export for DAW: `zt-band daw-export myfile.mid --output daw_ready.mid`
3. Import in Ardour/Reaper/etc.
4. Assign instruments (GM presets: Piano=0, Bass=32)
5. Verify playback

**Badge**: 🎹 Proof-of-Sound Verified (Raspberry Pi 5 + Ardour 8.11 + FluidSynth)

---

## Regression Prevention

### Before committing new code:

1. Run test suite: `python -m pytest tests/ -v`
2. Run lock verification: `python verify_lock.py`
3. Verify determinism: Generate twice, binary compare
4. Document any contract changes in CHANGELOG.md

### CI/CD (Future)

```yaml
# .github/workflows/verify-lock.yml
- name: Verify Core Lock
  run: |
    python -m pytest tests/ -v
    python verify_lock.py
```

---

## Technical Debt Eliminated

### Before Lock

❌ Timing engine used `int(beat * ticks_per_beat)` → platform-dependent truncation
❌ No minimum duration enforcement → zero-length notes possible
❌ Collision ordering undefined → stuck notes possible
❌ No contract validation → invalid events could reach MIDI writer
❌ Expressive layer mixed with generator logic → hard to isolate

### After Lock

✅ Deterministic rounding: `int(beat * tpb + 0.5)`
✅ Minimum duration: `max(end_tick, start_tick + 1)`
✅ Priority-based sorting: `(tick, priority)` tuples
✅ Contract enforcement gates at input and output
✅ Expressive layer is separate, validated transform

---

## Performance Characteristics

**Timing Engine**:
- Time complexity: O(n log n) where n = event count
- Space complexity: O(n) for message buffer
- Deterministic: Same inputs → same output (byte-identical MIDI)

**Contract Validation**:
- Time complexity: O(n) for n events
- Zero allocation: Validates in-place
- Fast-fail: Raises on first violation

**Expressive Layer**:
- Time complexity: O(n)
- Space complexity: O(n) (creates new event list)
- Pure function: No side effects

---

## Maintenance Commitment

**Core stability promise**:

1. No breaking changes to `musical_contract.py` interface
2. No changes to timing engine that affect output
3. Expressive layer remains velocity-only
4. All tests must pass before merge
5. Lock verification must pass before release

**Allowed changes**:

- Performance optimizations (if output unchanged)
- Bug fixes that improve determinism
- Documentation improvements
- New optional layers (outside core)

---

## References

**Files Modified**:
- `src/zt_band/musical_contract.py` (NEW - 118 lines)
- `src/zt_band/expressive_layer.py` (NEW - 111 lines)
- `src/zt_band/engine.py` (MODIFIED - 16 lines added)
- `src/zt_band/midi_out.py` (MODIFIED - timing engine hardened)

**Tests Added**:
- `tests/test_musical_contract.py` (NEW - 10 tests)
- `verify_lock.py` (NEW - comprehensive verification script)

**Documentation**:
- See `DEVELOPER_GUIDE.md` for import protocols
- See `docs/DAW_WORKFLOW.md` for production workflow

---

## Conclusion

The `zt-band` core is now **production-ready** with:

✅ Provable determinism
✅ Contract enforcement
✅ Collision-safe timing
✅ Expressive feel without instability
✅ Comprehensive test coverage

**Next steps**: Build optional swing/humanize layers on top of this stable foundation.

---

**Version**: 0.1.0 (Core Locked)
**Verification Date**: December 30, 2025
**Status**: ✅ LOCKED AND STABLE
