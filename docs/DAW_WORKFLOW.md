# DAW Workflow Documentation

**Purpose:** Canonical documentation for importing zt-band MIDI exports into any DAW.

---

## Export Structure

zt-band exports use **standard MIDI + folder structure**:

```
exports/daw/
└── 2025-12-29_143022/
    ├── backing.mid          # Standard MIDI file (SMF Type 1)
    └── IMPORT_DAW.md        # Import instructions
```

### Why This Format?

✅ **Universal compatibility** — works with any DAW (Ardour, Reaper, Ableton, Logic, FL Studio, etc.)  
✅ **No vendor lock-in** — standard MIDI, not proprietary  
✅ **Future-proof** — MIDI spec has existed for 40+ years  
✅ **Simple** — drag-and-drop, no special import scripts  

---

## Import Steps (Universal)

### 1. Export from zt-band

```bash
zt-band create --chords "Dm7 G7 Cmaj7" --style swing --tempo 120
zt-band daw-export backing.mid
```

This creates:
- Timestamped folder in `exports/daw/`
- `backing.mid` with GM instrument assignments
- `IMPORT_DAW.md` guide

### 2. Open Your DAW

Launch any DAW:
- **Ardour** (recommended for Pi)
- Reaper
- Ableton Live
- Logic Pro
- FL Studio
- Bitwig
- ProTools
- etc.

### 3. Drag & Drop MIDI File

**Method 1:** Drag `backing.mid` directly onto DAW timeline  
**Method 2:** Use DAW's File → Import → MIDI menu

### 4. Verify Track Layout

Should see 3 MIDI tracks:
- **Comp** (Piano, Channel 0)
- **Bass** (Bass, Channel 1)
- **Drums** (Drums, Channel 9)

### 5. Assign Virtual Instruments

Map each MIDI track to a software instrument:
- **Comp** → Piano/Rhodes/Synth pad
- **Bass** → Electric/Upright bass
- **Drums** → Drum kit (GM mapping)

### 6. Hit Play

You now have proof-of-sound.

---

## Track Conventions

### Track Names
zt-band uses these canonical track names:

```
Track 1: Comp     (Comping/chordal accompaniment)
Track 2: Bass     (Walking bass line)
Track 3: Drums    (Rhythmic foundation)
```

### MIDI Channels
```
Channel 0:  Comp     (Piano, Program 0)
Channel 1:  Bass     (Acoustic Bass, Program 32)
Channel 9:  Drums    (GM Drum Kit)
```

### GM Program Changes

zt-band injects GM (General MIDI) program changes for maximum compatibility:

```python
# From src/zt_band/daw_export.py
CHANNEL_0_PIANO      = 0   # Acoustic Grand Piano
CHANNEL_1_BASS       = 32  # Acoustic Bass
CHANNEL_9_DRUMS      = (Channel 9 is percussion by GM spec)
```

DAWs with GM-compatible instruments will load correct sounds automatically.

---

## Design Rules

### Rule 1: zt-band is the Musical Brain

zt-band generates:
✅ Chord progressions
✅ Voice-leading
✅ Bass lines
✅ Drum patterns
✅ Tritone logic
✅ Zone-crossing motion

**Output:** Standard MIDI file

---

### Rule 2: DAW is the Sound Engine

Your DAW provides:
✅ Virtual instruments (piano, bass, drums)
✅ Audio mixing (EQ, reverb, compression)
✅ Effects processing
✅ Master output (recording/bouncing)
✅ Real-time playback

**Input:** Standard MIDI file

---

### Rule 3: Clear Separation of Concerns

```
zt-band (generator)  →  MIDI  →  DAW (audio engine)
```

This separation means:
- zt-band stays **deterministic** (same input = same MIDI)
- DAW handles **sound design** (not zt-band's job)
- MIDI is the **contract** between them

---

### Rule 4: No Feature Creep

zt-band **does NOT**:
❌ Generate audio files (WAV/MP3)
❌ Include virtual instruments
❌ Provide mixing/mastering tools
❌ Replace your DAW

Those are DAW responsibilities.

---

## Touchscreen UI Role (Pi Interface)

When you run zt-band on a Raspberry Pi with touch display, the UI is a **control surface**, not a DAW:

### What the Touch UI Does:
✅ Select chord progressions (.ztprog files)
✅ Choose style (swing, bossa, ballad)
✅ Adjust tempo
✅ Start/stop playback
✅ Export to DAW
✅ Run exercises (.ztex files)

### What the Touch UI Does NOT Do:
❌ Audio mixing
❌ Virtual instruments
❌ Multi-track editing
❌ Recording audio
❌ Plugin management

**Analogy:** The Pi touch UI is like a **MIDI controller** or **looper pedal** for practice — it generates accompaniment, but you still need a DAW (or hardware sound module) for final sound.

---

## Proof-of-Sound Workflow

### Minimal Example (3 commands)

```bash
# 1. Generate backing track
zt-band create --chords "Dm7 G7 Cmaj7" --style swing --tempo 120

# 2. Export for DAW
zt-band daw-export backing.mid

# 3. Check output
ls exports/daw/
```

### Expected Output:
```
exports/daw/2025-12-29_143022/
    backing.mid
    IMPORT_DAW.md
```

### Import to DAW:
1. Open Ardour (or any DAW)
2. Drag `backing.mid` onto timeline
3. Assign instruments to tracks
4. Play

✅ **You now have sound.**

---

## DAW-Specific Notes

### Ardour (Recommended for Pi)

**Why Ardour?**
- Free & open-source
- Runs on Linux (Pi OS)
- Professional-grade features
- Low latency
- JACK audio support

**Quick Setup:**
1. Install: `sudo apt install ardour`
2. Create new session
3. Import MIDI file: Session → Import → `backing.mid`
4. Add virtual instruments (e.g., FluidSynth, Calf plugins)
5. Route MIDI tracks to instruments

**Pi-Specific:**
- Enable JACK for low-latency audio
- Use lightweight plugins (Calf, x42, LSP)
- Keep track count reasonable (~8 tracks max)

---

### Reaper

**Import:**
1. File → Insert Media File
2. Select `backing.mid`
3. Choose "Insert as new MIDI items"

**Instruments:**
- ReaSynth (built-in, lightweight)
- ReaSamplOmatic5000 (drum samples)
- Or any VST/AU plugin

---

### Ableton Live

**Import:**
1. Drag `backing.mid` into Arrangement View
2. Live auto-creates MIDI tracks

**Instruments:**
- Use built-in devices (e.g., Electric, Operator, Collision)
- Drums: Drum Rack with GM mapping

---

### Logic Pro

**Import:**
1. File → Import → MIDI File
2. Logic creates tracks automatically

**Instruments:**
- EXS24 (sampler)
- Ultrabeat (drums)
- Alchemy (synth bass)

---

## Troubleshooting

### Problem: No sound after import

**Cause:** MIDI tracks have no instruments assigned

**Fix:**
1. Select each MIDI track
2. Assign a virtual instrument
3. Enable monitor/input on tracks

---

### Problem: Drums not playing correctly

**Cause:** Non-GM drum mapping

**Fix:**
1. Verify drum track is on Channel 9 (GM standard)
2. Use GM-compatible drum kit
3. Check MIDI note mapping (C1 = kick, D1 = snare, etc.)

---

### Problem: Wrong tempo

**Cause:** DAW ignoring MIDI tempo map

**Fix:**
1. Check DAW's tempo settings
2. Enable "Import MIDI tempo" option
3. Or manually set project tempo to match

---

### Problem: Tracks named incorrectly

**Cause:** DAW auto-naming from MIDI meta-events

**Fix:**
1. Manually rename tracks: Comp, Bass, Drums
2. Future exports should preserve names

---

## File Format Specs

### MIDI Format: SMF Type 1

- **Type 1:** Multi-track (3 separate tracks)
- **Resolution:** 480 PPQN (ticks per quarter note)
- **Channels:** 0 (Comp), 1 (Bass), 9 (Drums)

### Track Structure:

```
Track 0: Tempo map (120 BPM default)
Track 1: Comp (Piano, Channel 0, Program Change 0)
Track 2: Bass (Bass, Channel 1, Program Change 32)
Track 3: Drums (Drums, Channel 9, no program change)
```

### Timestamp Format:

Exports use ISO 8601 timestamps for folder names:
```
YYYY-MM-DD_HHMMSS
```

Example: `2025-12-29_143022`

This ensures:
- Chronological sorting
- No filename collisions
- Clear export history

---

## Integration with zt-band CLI

### Relevant Commands

```bash
# Generate backing track (writes to backing.mid by default)
zt-band create --chords "Dm7 G7 C" --style swing --tempo 120

# Export existing MIDI for DAW
zt-band daw-export backing.mid

# Specify custom export root
zt-band daw-export backing.mid --export-root my_exports

# Run exercise and export
zt-band ex-run exercises/cycle_fifths_roots.ztex
zt-band daw-export cycle_fifths_roots.mid
```

### Default Paths

```
Input MIDI:  ./backing.mid (or specified file)
Export Root: ./exports/daw/
Output:      ./exports/daw/YYYY-MM-DD_HHMMSS/
```

---

## Best Practices

✅ **Keep exports organized** — timestamped folders preserve history  
✅ **Test in multiple DAWs** — ensures universal compatibility  
✅ **Use GM instruments initially** — guarantees baseline sound  
✅ **Customize later** — swap instruments after confirming playback  
✅ **Save DAW project** — preserves instrument assignments for future edits  
✅ **Check MIDI invariants** — no stuck notes, valid tempo, proper track names  

---

## Validation Checklist

Before considering an export "production-ready," verify:

- [ ] MIDI file opens in 3+ different DAWs
- [ ] Track names are correct (Comp, Bass, Drums)
- [ ] GM program changes load correct instruments
- [ ] Tempo matches intended BPM
- [ ] No stuck notes (all Note Ons have Note Offs)
- [ ] Drums play on Channel 9
- [ ] File size is reasonable (<1 MB for typical backing track)
- [ ] IMPORT_DAW.md guide is present and accurate

---

## Future Enhancements (Not Roadmap)

Possible extensions (no commitment):

- Export to Ardour session format (native .ardour file)
- Include sample-based soundfont for instant playback
- Generate audio preview (WAV) alongside MIDI
- Support for MIDI 2.0 (when spec is widely adopted)

**Note:** These are speculative — current design is intentionally minimal to avoid scope creep.

---

## Philosophy

> **zt-band generates music.  
> Your DAW makes it sound good.  
> MIDI is the bridge.**

This workflow respects the separation of concerns and leverages industry-standard tools rather than reinventing the wheel.

---

## Related Documentation

- [CLI_DOCUMENTATION.md](../CLI_DOCUMENTATION.md) — zt-band command reference
- [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) — Code architecture
- [MIDI Generation Invariants](../CLI_DOCUMENTATION.md#midi-generation-invariants) — Validation rules
- [src/zt_band/daw_export.py](../src/zt_band/daw_export.py) — Export implementation

---

**Last Updated:** December 29, 2025  
**Status:** Production — zt-band v0.1.0
