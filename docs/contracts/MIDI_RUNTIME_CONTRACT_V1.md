# Tritone MIDI Runtime Contract v1

**Status:** ACTIVE (governance-protected)
**Scope:** `zt-band` MIDI generation + real-time playback surface (offline + RT)
**Goal:** Ensure **deterministic**, **DAW-safe**, **real-time schedulable** musical output with **stable failure semantics** and **stable telemetry**.

---

## 0. Definitions

* **Program**: A progression + settings source (e.g. `.ztprog`) used to generate MIDI and/or RT events.
* **Engine (offline)**: Generates MIDI-note events and writes a `.mid` file.
* **RT Engine (realtime)**: Converts generated material into a cyclical step grid and schedules output in real-time.
* **Contract**: A set of invariants that must hold across versions unless an explicit contract bump occurs.
* **Deterministic**: Same canonical inputs ⇒ same canonical outputs (within defined tolerances).
* **Ornament event**: A low-velocity "ghost" or "decorative" note that may be dropped under lateness policy without harming musical continuity.

---

## 1. Non-Negotiable Invariants

### 1.1 Determinism

For a given **canonical input set**, the system MUST produce **identical event streams**:

* **Offline path**: identical event list and stable MIDI serialization ordering.
* **RT path**: identical `(step_i, message)` event list and identical scheduling decisions (drop/no-drop) given the same clock model.

Determinism is defined by:

* explicit seeds for any stochastic path
* stable sorting rules for same-timestamp events
* stable rounding rules for time quantization

### 1.2 DAW safety

Generated MIDI MUST satisfy:

* No negative time
* No zero/negative durations (minimum 1 tick where applicable)
* Velocity in `1..127` (velocity 0 is treated as note-off only if used by the backend; preferred: explicit note_off)
* MIDI channel in `0..15`
* Program changes must be **idempotent** at track start (see §4.2)

### 1.3 Validation gating

All outputs MUST pass validation at defined stages:

* **Pre-expressive validation**
* **Post-expressive validation**
* **Pre-write validation** (offline)
* **Pre-schedule validation** (RT)

No layer may bypass validation.

### 1.4 "Failure must be safe"

If the contract cannot be satisfied:

* Offline mode MUST fail with a structured error (no partial/corrupt MIDI)
* RT mode MUST:

  * optionally panic (send all-notes-off) depending on `--panic/--no-panic`
  * drop late ornaments according to policy
  * avoid "stuck note" conditions

---

## 2. Canonical Inputs

### 2.1 Program inputs (offline + RT generation)

Canonical program inputs include:

* chord symbols list (or resolved `.ztprog`)
* tempo (`bpm`)
* meter (`time_signature`) and grid resolution (`bar_steps` / `grid`)
* bars-per-chord
* base style identifier (style registry key)
* tritone mode + strength + seed (if used)
* expressive parameters (swing/humanize + seeds if stochastic)
* style knobs (ghost hits, velocity contour) if enabled

**Canonicalization rule:** if inputs are loaded from file + CLI overrides exist, the system MUST define precedence deterministically (documented in CLI docs).

### 2.2 RT playback inputs

RT loop canonical inputs include:

* `midi_out` port name
* `backend` (`mido` or `rtmidi`)
* `grid` (8/16)
* `clave` pattern kind
* click on/off
* `tick_s` (scheduler tick cadence)
* `lookahead_s` (window)
* lateness policy (`late_drop_ms`)
* ornament threshold (`ghost_vel_max`)
* panic enable (`panic_enabled`)

---

## 3. Canonical Outputs

### 3.1 Offline output

* A MIDI file containing:

  * track(s) for accompaniment + bass (if applicable)
  * optional GM program injection at start (export mode)
  * stable ordering (see §5)

### 3.2 RT output

* A loopable list of events:

  * `events: list[tuple[int, mido.Message]]`
  * where `step_i` is in cycle coordinates `[0, steps_per_cycle-1]`

---

## 4. Output Compatibility Contracts

### 4.1 Real-time backends

* `backend=mido` MUST function anywhere `mido` can open an output port.
* `backend=rtmidi` MAY be required for low latency on Pi/Linux and MUST be treated as optional dependency.
* If the selected backend is unavailable, RT mode MUST fail fast with a clear error.

### 4.2 DAW Export (GM Injection)

* If DAW export injects GM program changes:

  * injection MUST be **idempotent**
  * repeated export MUST NOT accumulate duplicate program changes at time 0
* The idempotence check MUST be stable and tested.

---

## 5. Ordering, Timing, and Quantization

### 5.1 Stable ordering rule (offline and RT conversions)

If two MIDI messages share the same timestamp/tick:

1. **note_off** events MUST be ordered before **note_on** at the same time (prevents stuck/overlap artifacts)
2. Program changes/CC at time 0 MUST come before any note_on
3. Within the same type and time, maintain deterministic secondary ordering (track then pitch)

### 5.2 Quantization policy

* Any beat→step mapping MUST specify the quantize mode (e.g., `nearest` or `down`)
* Quantization must be deterministic and consistent across platforms.

---

## 6. Expressive Layers Contract (Style-Only)

Expressive layers may change feel **without altering harmonic intent**.

### 6.1 Allowed expressive transforms

* velocity contour (per-bar multipliers)
* ghost hits (ornamentation)
* swing timing offsets (deterministic)
* humanize timing/velocity ONLY if a seed is provided (deterministic jitter)

### 6.2 Forbidden expressive transforms (core contract)

* transformations that change chord identity
* transformations that alter bar count/meter implicitly
* randomness without explicit seed
* transforms that bypass validation

---

## 7. Real-Time Lateness & Panic Policy

### 7.1 Lateness classification

An event is **late** if `now - due_time > late_drop_ms`.

### 7.2 Drop policy

* If late and the message is classified as **ornament** (see §7.3), it MAY be dropped.
* If late and the message is **non-ornament**, it MUST be sent (late) unless this causes unsafe behavior.

### 7.3 Ornament classification

By default, an event is ornament if it is a note_on with:

* `velocity <= ghost_vel_max`

This threshold MUST be user-tunable via CLI flags without code edits.

### 7.4 Panic cleanup

If panic is enabled:

* On exit (normal or interrupt) RT mode MUST send a safe "all notes off" sequence and close the sender.
* Panic must be idempotent and safe even if the backend is partially failed.

CLI surface:

* `--panic/--no-panic` (default ON)
* `--late-drop-ms` (default 35)
* `--ghost-vel-max` (default 22)

---

## 8. Telemetry + DAW Alignment Contract

Telemetry is part of the moat and must remain stable.

### 8.1 Bar boundary CC emissions (optional)

If enabled (`--bar-cc`), RT playback MUST emit at bar boundaries:

* bar index count-up CC (`--bar-cc-index`, default 21)
* bars-remaining countdown CC (`--bar-cc-countdown`, default 20)
* section/item marker CC at program start (`--bar-cc-section`, default 22)

### 8.2 Telemetry stability

* Default CC numbers MUST NOT change without a contract bump.
* Channel MUST be configurable (default channel 15).
* Telemetry must never compromise playback safety.

---

## 9. Compatibility, Versioning, and Contract Bumps

### 9.1 Contract version

This contract is **v1**.

A **contract bump** (v2) is required if any of the following change:

* event ordering semantics (§5.1)
* determinism definition or seed requirements (§1.1, §6.1)
* telemetry meaning or default CC mapping (§8)
* RT lateness/panic default behavior (§7)

### 9.2 Backward compatibility

Minor releases MUST preserve v1 behavior unless explicitly documented under "Breaking Changes" and accompanied by a contract bump.

---

## 10. Extension Points (allowed growth)

These are safe axes of extension under v1:

* new styles added to the registry
* new style knobs that map to existing StylePattern fields (whitelisted)
* new telemetry channels/messages (if opt-in and non-breaking)
* new RT backends (if they preserve sender semantics)
* additional validators (stricter is OK if errors are clear)

---

## 11. Non-Goals (explicitly out of scope for v1)

* Generative AI teacher behavior (Mode 3)
* Adaptive "learning" modifications to engine behavior based on user sessions
* Changing harmonic intelligence rules in a way that changes determinism outputs without a contract bump
* UI/dashboard systems

---

## 12. Required Test Surface (minimum)

To claim compliance with this contract, the repo MUST have:

1. **Ordering test** for same-tick collisions (note_off before note_on)
2. **DAW export idempotence** test (no duplicate GM program changes)
3. **RT lateness policy** test:

   * late ornaments drop
   * late non-ornaments send
4. **Panic cleanup** test (sender receives all-notes-off on exit path)
5. **Golden vector** test for at least one canonical program (stable digest of event list or MIDI file)

---

## 13. "Proof-of-Sound Verified" Definition

A build may claim "Proof-of-Sound Verified" if:

* DAW export produces a `.mid` that plays sound in a standard GM instrument in at least one reference DAW on Linux
* The above required tests pass in CI
* The contract version is recorded in the export payload metadata (recommended)

---

**End of Contract v1**
