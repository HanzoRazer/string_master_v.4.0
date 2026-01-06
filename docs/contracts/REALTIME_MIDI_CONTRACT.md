# Realtime MIDI Contract

## Version 1.0 — Governance Document

> **Purpose:**
> Define the non-negotiable guarantees and failure behaviors for realtime MIDI output from the String Master engine when feeding a DAW or external MIDI consumer.

This contract applies to:

- `zt-band rt-play`
- Any future realtime MIDI backend (ALSA, CoreMIDI, JACK MIDI)
- Any DAW or hardware device consuming String Master MIDI

---

## Governance Status

This document is **governance-protected**.

Changes require:

✔ Written proposal  
✔ Review  
✔ Founder approval  

Per [GOVERNANCE.md](GOVERNANCE.md), no fork may claim canonical status without following this process.

---

## 1. Execution Model

### Engine Position

- String Master runs **outside** the DAW.
- It emits MIDI events to a **realtime MIDI port**.
- The DAW is a **consumer**, never a scheduler.

### Scheduling Authority

- **String Master owns musical time.**
- The DAW does *not* quantize, reorder, or interpret intent.
- MIDI timestamps (or emission timing) are authoritative.

---

## 2. Latency Contract

### Target Latency (Pickup → DAW)

| Tier | Definition |
|------|------------|
| **Hard max** | ≤ **20 ms** end-to-end |
| **Target** | ≤ **10 ms** |
| **Ideal** | ≤ **5 ms** |

### Latency Violation Behavior

If latency exceeds **20 ms**, the engine must:

1. **Continue playback** (no audio dropouts)
2. **Emit a telemetry warning**
3. **Never "catch up" by compressing musical time**

> **Axiom:** Musical time must never warp to compensate for system delay.

---

## 3. Jitter Contract

### Per-Event Timing Jitter

| Category | Allowed |
|----------|---------|
| **Note-on jitter** | ≤ **±2 ms** |
| **Note-off jitter** | ≤ **±5 ms** |
| **Telemetry CC jitter** | ≤ **±3 ms** |

### Jitter Rules

- Jitter must be **zero-mean** (no drift).
- Repeated jitter bias = **bug**.
- Humanize layers must operate **before scheduling**, not by runtime delay injection.

---

## 4. Scheduling Model

### Internal Representation

Engine generates events as:

```
(absolute_time_seconds, MIDI_message)
```

These are converted to wall-clock emission times.

### Emission Rules

- Events are emitted in **monotonic order**.
- Events scheduled for the same timestamp preserve priority:

```
program_change → control_change → note_on → note_off
```

### No Look-Ahead Rewrite

Once a bar begins:

- No reharmonization
- No pattern mutation
- No tempo drift

Changes apply **at bar boundaries only**.

---

## 5. Tempo & Clock Behavior

### Tempo Source

- Tempo is **engine-owned**, not MIDI clock-slaved (v1).
- MIDI Clock output is optional and non-authoritative.

### Tempo Changes

- Allowed **only at bar boundaries**.
- Mid-bar tempo changes are **forbidden** in realtime mode.

---

## 6. Failure Behavior (Critical Section)

This is where most engines fail. String Master must not.

### A. MIDI Backend Failure

Examples:

- MIDI port disappears
- ALSA/JACK disconnect
- python-rtmidi throws

**Required behavior:**

1. Stop emitting events immediately
2. Emit a **structured error**
3. Preserve engine state
4. Allow **clean restart** without restart of process

**Forbidden:**

- ❌ Crash the process
- ❌ Block the scheduler thread
- ❌ Emit malformed MIDI

---

### B. Engine Overload (CPU spike)

If scheduling falls behind, shed load in this order:

1. **Drop ghost notes first**
2. Then drop **velocity contour**
3. **Never drop:**
   - Bar markers
   - Chord roots
   - Note-offs (stuck notes are unacceptable)

This establishes a **priority hierarchy**.

---

### C. Contract Violation

If a note event fails validation:

1. Abort playback
2. Emit structured error:

```json
{
  "code": "RT_CONTRACT_VIOLATION",
  "bar": N,
  "event_index": M,
  "reason": "negative duration"
}
```

---

## 7. Determinism Rules (Realtime Edition)

Realtime does **not** mean nondeterministic.

### Required

- Any probabilistic behavior **must have a seed**
- Given:
  - same program
  - same seed
  - same tempo
- The emitted event sequence **must be identical** (timing aside within jitter bounds)

### Forbidden

- ❌ Reading system randomness mid-playback
- ❌ Adaptive AI decisions inside a bar
- ❌ Feedback loops that alter harmony timing

---

## 8. Telemetry Guarantees

### Bar & Section Markers

- Emitted as **MIDI CC** (fixed CC numbers, documented)
- Exactly aligned with bar boundaries
- Never skipped, even under load

### Telemetry Priority

Telemetry is:

- Lower bandwidth than notes
- Higher priority than ornamentation
- The **bridge to UI, practice mode, and teaching**

> **Axiom:** Telemetry is sacred.

---

## 9. Scope Explicitly Excluded (v1)

These are **intentionally out of scope**:

- Audio generation
- Plugin hosting
- MIDI input feedback loops
- DAW tempo following
- AI decision-making mid-bar

This keeps the engine stable.

---

## Summary: What Is Locked

> In realtime mode, **String Master is a deterministic musical scheduler with bounded latency, bounded jitter, and defined failure semantics.**

If someone violates this contract:

- It is a **bug**
- Not a creative choice

---

## Contract Violation Codes

| Code | Description |
|------|-------------|
| `RT_LATENCY_EXCEEDED` | End-to-end latency > 20ms |
| `RT_JITTER_BIAS` | Systematic timing drift detected |
| `RT_CONTRACT_VIOLATION` | Event failed validation |
| `RT_BACKEND_FAILURE` | MIDI port/backend error |
| `RT_OVERLOAD` | Scheduler fell behind |
| `RT_STUCK_NOTE` | Note-off was dropped (critical) |

---

## Testing Requirements

Any PR touching realtime code must verify:

- [ ] Latency stays within hard max (20ms)
- [ ] Jitter is zero-mean over 100+ events
- [ ] Backend failure triggers clean shutdown
- [ ] Determinism holds with fixed seed
- [ ] Telemetry CC emits at bar boundaries
- [ ] Note-offs are never dropped under load

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-06 | Initial governance lock |

---

## Attribution

This contract is part of the **String Master / Smart Guitar Platform**.

> "This system is derived from the Zone–Tritone framework founded by Greg Brown."

See [LICENSE-THEORY.md](LICENSE-THEORY.md) for intellectual property terms.
