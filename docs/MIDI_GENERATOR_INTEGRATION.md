# MIDI Generator Core Lock — Integration Guide

This document describes how to wire the new contract-based MIDI generation system into the existing zt-band CLI without breaking current functionality.

---

## Architecture Overview

### Old System (Current)
```
engine.py → midi_out.NoteEvent (beats) → write_midi_file() → MIDI
```

### New System (Contract-Based)
```
engine.py → contract.NoteEvent (ticks) → timing.build_midi_type1() → MIDI
```

---

## Migration Strategy: Gradual Transition

### Phase 1: Add Parallel Path (Non-Breaking)

Add a new optional flag to `cmd_create`:

```python
# In build_arg_parser(), add to p_create:
p_create.add_argument(
    "--use-contract",
    action="store_true",
    help="Use new contract-based MIDI generator (testing).",
)
```

### Phase 2: Create Adapter Function

Add to `src/zt_band/engine.py`:

```python
from .contract import ProgramSpec, NoteEvent as ContractNoteEvent
from .expressive import apply_velocity_shape
from .timing import build_midi_type1

def generate_accompaniment_v2(
    chord_symbols: List[str],
    style_name: str = "swing_basic",
    tempo_bpm: int = 120,
    bars_per_chord: int = 1,
    outfile: str | None = None,
    tritone_mode: str = "none",
    tritone_strength: float = 1.0,
    tritone_seed: int | None = None,
) -> None:
    """
    Contract-based generation (new path).
    
    Key difference: generates contract.NoteEvent (ticks) instead of midi_out.NoteEvent (beats)
    """
    if style_name not in STYLE_REGISTRY:
        raise ValueError(f"Unknown style: {style_name}")

    style: StylePattern = STYLE_REGISTRY[style_name]

    # Parse + optional tritone reharmonization (existing logic)
    base_chords: List[Chord] = [parse_chord_symbol(s) for s in chord_symbols]
    if tritone_mode != "none":
        chords = apply_tritone_substitutions(
            base_chords, mode=tritone_mode, strength=tritone_strength, seed=tritone_seed
        )
    else:
        chords = base_chords

    # Create program spec
    program = ProgramSpec(
        tempo_bpm=tempo_bpm,
        ticks_per_beat=480,
        seed=tritone_seed,  # Use tritone seed for determinism tracking
    )

    # Generate events using TICKS instead of BEATS
    events: List[ContractNoteEvent] = []
    current_bar = 0

    for chord in chords:
        pitches = chord_pitches(chord, octave=4)
        bass_pitch = chord_bass_pitch(chord, octave=2)

        for bar_offset in range(bars_per_chord):
            bar_start_ticks = (current_bar + bar_offset) * 4 * program.ticks_per_beat  # 4/4 time

            # Comp hits
            for spec in style.comp_hits:
                hit_tick = bar_start_ticks + int(spec.beat * program.ticks_per_beat)
                dur_tick = int(spec.length_beats * program.ticks_per_beat)
                for p in pitches:
                    events.append(
                        ContractNoteEvent(
                            track="Comp",
                            start_tick=hit_tick,
                            dur_tick=dur_tick,
                            channel=0,
                            note=p,
                            velocity=spec.velocity,
                        )
                    )

            # Bass pattern
            for beat, length, vel in style.bass_pattern:
                bass_tick = bar_start_ticks + int(beat * program.ticks_per_beat)
                bass_dur = int(length * program.ticks_per_beat)
                events.append(
                    ContractNoteEvent(
                        track="Bass",
                        start_tick=bass_tick,
                        dur_tick=bass_dur,
                        channel=1,
                        note=bass_pitch,
                        velocity=vel,
                    )
                )

        current_bar += bars_per_chord

    # Apply expressive layer (velocity shaping)
    events = apply_velocity_shape(events, ticks_per_beat=program.ticks_per_beat)

    # Write via contract-enforced timing engine
    if outfile:
        mid = build_midi_type1(
            program=program,
            events=events,
            track_order=["Comp", "Bass"],
        )
        mid.save(outfile)
```

### Phase 3: Wire Into CLI

Modify `cmd_create` in `src/zt_band/cli.py`:

```python
def cmd_create(args: argparse.Namespace) -> int:
    # Prefer config if provided
    if args.config:
        cfg = load_program_config(args.config)

        if cfg.style not in STYLE_REGISTRY:
            print(f"error: style '{cfg.style}' from config is not a known style.", file=sys.stderr)
            return 1

        # CHOICE: old vs new generator
        if getattr(args, "use_contract", False):
            from .engine import generate_accompaniment_v2
            generate_accompaniment_v2(
                chord_symbols=cfg.chords,
                style_name=cfg.style,
                tempo_bpm=cfg.tempo,
                bars_per_chord=cfg.bars_per_chord,
                outfile=cfg.outfile,
                tritone_mode=cfg.tritone_mode,
                tritone_strength=cfg.tritone_strength,
                tritone_seed=cfg.tritone_seed,
            )
        else:
            generate_accompaniment(  # OLD PATH (unchanged)
                chord_symbols=cfg.chords,
                style_name=cfg.style,
                tempo_bpm=cfg.tempo,
                bars_per_chord=cfg.bars_per_chord,
                outfile=cfg.outfile,
                tritone_mode=cfg.tritone_mode,
                tritone_strength=cfg.tritone_strength,
                tritone_seed=cfg.tritone_seed,
            )

        label = cfg.name or args.config
        print(f"Created backing track from config '{label}': {cfg.outfile}")
        return 0

    # Inline/file chords path (same pattern)
    chords = _load_chords_from_args(args)

    if args.style not in STYLE_REGISTRY:
        print(f"error: unknown style '{args.style}'.", file=sys.stderr)
        return 1

    if getattr(args, "use_contract", False):
        from .engine import generate_accompaniment_v2
        generate_accompaniment_v2(
            chord_symbols=chords,
            style_name=args.style,
            tempo_bpm=args.tempo,
            bars_per_chord=args.bars_per_chord,
            outfile=args.outfile,
            tritone_mode=args.tritone_mode,
            tritone_strength=args.tritone_strength,
            tritone_seed=args.tritone_seed,
        )
    else:
        generate_accompaniment(  # OLD PATH
            chord_symbols=chords,
            style_name=args.style,
            tempo_bpm=args.tempo,
            bars_per_chord=args.bars_per_chord,
            outfile=args.outfile,
            tritone_mode=args.tritone_mode,
            tritone_strength=args.tritone_strength,
            tritone_seed=args.tritone_seed,
        )

    print(f"Created backing track: {args.outfile}")
    return 0
```

---

## Testing the New Path

### Command Comparison

**Old generator (default):**
```bash
zt-band create --chords "Dm7 G7 Cmaj7" --style swing --tempo 120
```

**New contract-based generator:**
```bash
zt-band create --chords "Dm7 G7 Cmaj7" --style swing --tempo 120 --use-contract
```

Both should produce functionally identical MIDI, but the new path:
- ✅ Enforces meta events at time 0
- ✅ Prevents stuck notes
- ✅ Validates all events
- ✅ Applies velocity shaping
- ✅ Uses canonical timing engine

### Validation Tests

Run both paths and compare:
```bash
# Old path
zt-band create --chords "Dm7 G7 C" --tempo 120 --outfile old.mid

# New path
zt-band create --chords "Dm7 G7 C" --tempo 120 --outfile new.mid --use-contract

# Compare in DAW
# - Both should import cleanly
# - Both should have correct tempo
# - Both should have no stuck notes
# - New path should have slightly more expressive velocity dynamics
```

---

## Phase 4: Gradual Rollout

### Week 1: Testing
- Add `--use-contract` flag
- Keep old path as default
- Run regression tests
- Validate in DAW

### Week 2: Verification
- Test all `.ztprog` programs with new path
- Verify playlists and exercises
- Check daw-export compatibility

### Week 3: Swap Default
- Make `--use-contract` the default
- Add `--use-legacy` flag to opt back to old path
- Update documentation

### Week 4: Deprecation
- Remove old path entirely
- Remove `midi_out.py` (NoteEvent beats-based)
- Update all references to use contract-based system

---

## Benefits of Contract-Based System

### 1. **Enforced Invariants**
All MIDI output is validated against published invariants automatically.

### 2. **Single Source of Truth**
`timing.build_midi_type1()` is the ONLY way to write MIDI, preventing divergence.

### 3. **Expressive Without Instability**
Velocity shaping improves "feel" without touching timing engine.

### 4. **Future-Proof**
New expressive layers (swing, humanize) can be added as separate optional modules.

### 5. **Determinism Lock**
`ProgramSpec.seed` enables reproducible randomness when needed.

---

## Rollback Plan

If issues arise:
1. Remove `--use-contract` flag
2. Old path remains untouched and working
3. New modules (contract.py, timing.py, expressive.py) can stay dormant
4. No data loss, no broken MIDI files

---

## Next Steps After Wiring

Once new path is validated:
1. **Add drums track** (Channel 9, GM drum kit)
2. **Add swing layer** (optional timing shift, seed-driven)
3. **Add humanize layer** (optional timing/velocity variation, seed-driven)
4. **Lock tempo variations** (rubato, ritardando as contract-validated layers)

All future work builds on the contract foundation.

---

**Last Updated:** December 30, 2025  
**Status:** Ready for integration
