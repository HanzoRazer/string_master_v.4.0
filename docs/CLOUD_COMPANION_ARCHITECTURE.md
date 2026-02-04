# Smart Guitar Cloud Companion Architecture

## Executive Summary

This document outlines the architectural split between embedded (on-guitar) and cloud-based coaching services for the Smart Guitar product. The goal is to provide real-time, responsive coaching on-device while optionally leveraging cloud AI for enhanced feedback when connectivity is available.

---

## Hardware Architecture

### Embedded Stack (On-Guitar)

| Component | Spec | Role |
|-----------|------|------|
| **Arduino Uno** | ATmega328P @ 16MHz, 2KB SRAM, 32KB Flash | Audio processor - real-time signal capture, timing detection, MIDI conversion |
| **Raspberry Pi 5** | ARM Cortex-A76 @ 2.4GHz, 4-8GB RAM | DAW processor - string_master, sg_agentd, coaching logic, bundle generation |

### Communication Flow

```
Guitar Pickups
      │
      ▼
┌─────────────────┐
│   Arduino Uno   │  Audio sampling @ 44.1kHz
│   (Audio MCU)   │  Onset detection
│                 │  Timing extraction
└────────┬────────┘
         │ Serial/I2C (115200 baud typical)
         │ Latency: ~1-5ms
         ▼
┌─────────────────┐
│  Raspberry Pi 5 │  MIDI event processing
│  (DAW/Coach)    │  Zone-Tritone engine
│                 │  Deterministic coaching
│                 │  Bundle I/O
└────────┬────────┘
         │ WiFi (optional)
         │ Latency: 50-500ms RTT
         ▼
┌─────────────────┐
│  Cloud Service  │  AI-enhanced coaching
│  (Optional)     │  Practice analytics
│                 │  Long-term progression
└─────────────────┘
```

---

## Program Challenges

### 1. Real-Time Audio Processing on Arduino Uno

**Challenge**: The Arduino Uno has severe resource constraints for audio processing.

| Constraint | Impact |
|------------|--------|
| 16MHz clock | ~62.5ns per instruction; audio @ 44.1kHz = ~362 cycles per sample |
| 2KB SRAM | Cannot buffer more than ~1000 samples (22ms of audio) |
| No FPU | Floating-point math is emulated, 50-100x slower than integer |
| Single core | No parallel processing; ISR conflicts with main loop |

**Mitigations**:
- Use fixed-point arithmetic for all DSP
- Minimal onset detection (zero-crossing, envelope following)
- Offload all complex logic to Pi 5
- Send sparse timing events, not raw audio

**Risk**: Timing jitter from ISR handling could introduce 1-3ms measurement error.

---

### 2. Serial Communication Bottleneck

**Challenge**: Arduino-to-Pi communication is a potential latency source.

| Protocol | Speed | Latency | Reliability |
|----------|-------|---------|-------------|
| Serial UART | 115200 baud | 1-5ms | Good, but no flow control |
| I2C | 400kHz | <1ms | Master/slave complexity |
| SPI | 1MHz+ | <0.5ms | Wiring complexity |

**Current approach**: Serial UART at 115200 baud

**Payload design**:
```
[START][EVENT_TYPE][TIMESTAMP_MS:4][MIDI_NOTE][VELOCITY][END]
= 8 bytes per event = ~0.7ms transmission time
```

**Risk**: Burst of chord events (6 notes) = ~4ms transmission window. If Pi 5 is busy, buffer overrun possible.

---

### 3. Raspberry Pi 5 Processing Load

**Challenge**: Pi 5 runs multiple concurrent services.

| Service | CPU Load | Memory | Latency Sensitivity |
|---------|----------|--------|---------------------|
| DAW (audio routing) | 10-30% | 200-500MB | Critical (<10ms) |
| string_master engine | 5-15% | 50-100MB | High (<50ms) |
| sg_agentd HTTP | 2-5% | 30-50MB | Medium (<100ms) |
| Deterministic coach | <1% | <10MB | Low (<200ms) |
| Bundle writer | 5-10% (burst) | 20-50MB | Non-critical |

**Total baseline**: 22-61% CPU, 300-710MB RAM

**Concerns**:
- Python GIL limits true parallelism
- SD card I/O latency spikes (10-100ms) during bundle writes
- Thermal throttling at sustained load (Pi 5 runs hot)

**Mitigations**:
- Use `asyncio` for non-blocking I/O
- RAM disk for hot bundles, lazy flush to SD
- Active cooling required
- Consider freezing Python with Nuitka for 2-3x speedup

---

### 4. Deterministic Coach Limitations

**Challenge**: The 15-template coach_hint system has limited expressiveness.

**Current matrix**:
```
Score Bands (5):  excellent | solid | stable | recover | reset
Trend Buckets (3): up | flat | down
Templates: 5 × 3 = 15 unique hints
```

**Limitations**:
- Cannot reference specific mistakes (e.g., "you rushed beat 3")
- Cannot adapt to individual learning patterns
- Same hint repeats for identical score/trend (user fatigue)
- No awareness of musical context (style, song section)

**Pros**:
- 100% predictable and testable
- Zero latency overhead
- Works offline
- Certified pedagogical content

---

### 5. Cloud AI Coach Challenges

**Challenge**: Network dependency introduces failure modes and latency.

#### Latency Breakdown

| Stage | Typical | Worst Case |
|-------|---------|------------|
| WiFi association | 0ms (connected) | 2-10s (reconnect) |
| DNS resolution | 10-50ms | 500ms (timeout) |
| TLS handshake | 50-150ms | 300ms |
| Request upload | 10-30ms | 100ms (large payload) |
| AI inference | 50-200ms | 500ms (cold start) |
| Response download | 10-30ms | 100ms |
| **Total RTT** | **130-460ms** | **1.5-11s** |

#### Failure Modes

| Failure | Probability | Impact | Mitigation |
|---------|-------------|--------|------------|
| WiFi dropout | 5-15% sessions | No AI coaching | Fallback to deterministic |
| Cloud timeout | 1-5% requests | Delayed feedback | 500ms timeout + fallback |
| Cold start | First request | 2-5s delay | Keep-alive pings |
| Rate limiting | Burst usage | 429 errors | Client-side throttle |
| Model drift | Over time | Inconsistent hints | Version pinning |

---

### 6. Synchronization Complexity

**Challenge**: Two coaching systems must produce coherent feedback.

**Scenario**: User plays a phrase poorly (score=45, trend=down)

| System | Response |
|--------|----------|
| Deterministic (instant) | "Trending down—reset your approach: slower, simpler, and perfectly in time." |
| AI (300ms later) | "I noticed you're consistently late on beat 2. Try counting '1-and-2-and' out loud." |

**Problems**:
- Which message does the user see first?
- Do we show both? (cognitive overload)
- Do we replace deterministic with AI? (jarring UX)
- What if AI contradicts deterministic? (trust erosion)

**Proposed solution**: Layered enhancement
```
1. Show deterministic hint immediately (0ms)
2. If AI returns within 500ms, append "Tip: [AI insight]"
3. If AI returns after 500ms, queue for next cycle
4. Never replace, only augment
```

---

## Latency Budget Analysis

### Target: Feedback within 500ms of phrase completion

| Stage | Budget | Actual | Status |
|-------|--------|--------|--------|
| Audio onset detection | 50ms | 10-30ms | ✓ OK |
| Arduino → Pi serial | 20ms | 1-5ms | ✓ OK |
| MIDI event processing | 50ms | 5-20ms | ✓ OK |
| Score calculation | 50ms | 10-30ms | ✓ OK |
| Deterministic coach | 10ms | <1ms | ✓ OK |
| **Subtotal (on-device)** | **180ms** | **27-86ms** | ✓ OK |
| WiFi + Cloud AI | 320ms | 130-460ms | ⚠️ Tight |
| **Total with AI** | **500ms** | **157-546ms** | ⚠️ Marginal |

**Conclusion**: Deterministic coaching easily meets budget. AI coaching is marginal and will exceed budget ~30% of the time.

---

## Pros and Cons Summary

### Deterministic Coaching (On-Device)

| Pros | Cons |
|------|------|
| Zero latency | Limited to 15 templates |
| 100% offline | No personalization |
| Predictable/testable | Can feel repetitive |
| Low resource usage | No specific mistake callouts |
| Certified content | No learning adaptation |

### AI Coaching (Cloud)

| Pros | Cons |
|------|------|
| Specific, contextual feedback | Network dependency |
| Learns user patterns | 130-500ms latency |
| Rich exercise suggestions | Cloud costs |
| Timing-aware insights | Cold start delays |
| Continuous improvement | Privacy concerns |

### Hybrid Approach

| Pros | Cons |
|------|------|
| Best of both worlds | Two systems to maintain |
| Graceful degradation | Synchronization complexity |
| Offline-first, AI-enhanced | UX consistency challenges |
| Future-proof | Higher test surface |

---

## Cloud Service Cost Factors

For cost estimation, consider these cloud service requirements:

### Compute

| Metric | Estimate |
|--------|----------|
| Requests per user per session | 50-200 |
| Average session length | 20-45 minutes |
| Inference time per request | 50-200ms |
| Concurrent users (peak) | TBD |

### API Characteristics

```
Request payload:  ~2KB (groove context, timing data)
Response payload: ~1KB (coaching draft)
Requests/user/hour: 100-300
```

### Infrastructure Options

| Option | Pros | Cons | Cost Model |
|--------|------|------|------------|
| **Serverless (Lambda/Cloud Functions)** | Auto-scale, no idle cost | Cold starts, 15min timeout | Per-invocation |
| **Container (ECS/Cloud Run)** | Warm instances, predictable | Idle cost, scaling lag | Per-second + baseline |
| **Dedicated (EC2/Compute Engine)** | Full control, no cold starts | Fixed cost, manual scaling | Per-hour |
| **Edge (Cloudflare Workers)** | Ultra-low latency | Limited compute, no GPU | Per-request |

### Estimated Monthly Costs (1000 active users)

| Component | Low | Medium | High |
|-----------|-----|--------|------|
| Compute (serverless) | $50 | $150 | $400 |
| Database (user profiles) | $20 | $50 | $100 |
| Storage (practice logs) | $10 | $30 | $80 |
| Bandwidth | $20 | $60 | $150 |
| Monitoring/logging | $10 | $30 | $50 |
| **Total** | **$110** | **$320** | **$780** |

*Note: These are rough estimates. Actual costs depend on usage patterns, region, and provider.*

---

## Recommendations

1. **Ship with deterministic coaching only** for v1.0
   - Validates core product without cloud dependency
   - Reduces launch complexity

2. **Build cloud service as v1.1 enhancement**
   - Opt-in feature for connected users
   - A/B test AI vs deterministic outcomes

3. **Design for graceful degradation**
   - AI enhances but never replaces deterministic
   - Offline mode is always fully functional

4. **Monitor latency religiously**
   - P50, P95, P99 for cloud requests
   - Alert if P95 > 400ms

5. **Consider edge deployment**
   - If latency is critical, edge functions reduce RTT
   - Trade-off: limited model complexity

---

## Open Questions

1. What is the target user count for cloud service sizing?
2. Is practice data stored long-term for analytics? (storage costs)
3. Will AI models run on Anthropic API or self-hosted?
4. What's the acceptable monthly cost per active user?
5. Is there a companion mobile app that could run AI locally?

---

## Data Schemas: Before and After

This section details the data structures at each layer, showing how information flows from Arduino through to the user interface.

### Layer 1: Arduino → Raspberry Pi (Serial Events)

**Schema: `TimingEvent` (Arduino output)**

```c
// Arduino C struct (8 bytes)
typedef struct {
    uint8_t  start_marker;      // 0xAA
    uint8_t  event_type;        // 0x01=note_on, 0x02=note_off, 0x03=chord
    uint32_t timestamp_ms;      // Milliseconds since loop start
    uint8_t  midi_note;         // 0-127
    uint8_t  velocity;          // 0-127
} TimingEvent;
```

```python
# Python equivalent (Pi 5 receiver)
@dataclass
class TimingEvent:
    event_type: Literal["note_on", "note_off", "chord"]
    timestamp_ms: int
    midi_note: int
    velocity: int
```

---

### Layer 2: Performance Scoring (Pi 5 Internal)

**Schema: `TakeMetrics` (computed from timing events)**

```python
@dataclass
class TakeMetrics:
    """Computed after each practice loop (take)."""

    # Timing accuracy
    timing_error_ms_avg: float      # Mean deviation from grid
    timing_error_ms_max: float      # Worst single hit
    late_hits: int                  # Count of hits > 20ms late
    early_hits: int                 # Count of hits > 20ms early

    # Chord accuracy
    total_chord_hits: int           # Expected chord changes
    missed_chord_hits: int          # Missed or late chord changes

    # Overall
    score: float                    # 0-100 composite score
    take_result: Literal["pass", "struggle", "fail"]
```

---

### Layer 3: Deterministic Coaching (BEFORE - Current Implementation)

**Schema: `ProgressionDecision` (string_master_v.4.0)**

```python
# Location: src/sg_agentd/services/progression_policy.py

class ProgressionDecision(BaseModel):
    """
    Output of the deterministic progression policy.
    Episode 11: Adds coach_hint for user-facing narrative.
    """

    # Difficulty adjustments
    difficulty_delta: float         # -0.05 to +0.05
    tempo_delta_bpm: float          # -5 to +3 BPM

    # Engine parameters
    density_bucket: Literal["sparse", "medium", "dense"]
    syncopation_bucket: Literal["straight", "light", "heavy"]

    # User feedback
    rationale: str                  # Internal logging
    coach_hint: str                 # User-facing message (15 templates)

    policy_version: str = "v1"
```

**Template Matrix (15 hints):**

| Score Band | Trend: Up | Trend: Flat | Trend: Down |
|------------|-----------|-------------|-------------|
| **Excellent** (≥85) | "Your control is strong and improving..." | "Strong control. Keep consistency..." | "Still strong overall, but the last rep dipped..." |
| **Solid** (≥70) | "Nice improvement. Keep the groove steady..." | "Solid. Hold steady and try to reduce..." | "Good work, but it's slipping a bit..." |
| **Stable** (≥55) | "You're stabilizing and trending up..." | "Hold here and stabilize..." | "You're close, but trending down..." |
| **Recover** (≥40) | "Recovering and improving. Stay patient..." | "Let's reduce load and rebuild control..." | "Trending down—reset your approach..." |
| **Reset** (<40) | "Good—starting to recover..." | "Reset fundamentals: play it simple..." | "Pause and reset fundamentals..." |

**Limitations:**
- No reference to specific timing issues
- No exercise suggestions
- No awareness of what the user played
- Same hint for identical score/trend combinations

---

### Layer 4: AI-Enhanced Coaching (AFTER - Cloud Service)

**Schema: `CoachContextPacket` (request to sg-ai)**

```python
# Location: sg-ai/packages/sg-engine/sg_engine/schemas.py

class GrooveMetrics(BaseModel):
    """Detailed performance metrics for AI analysis."""

    tempo_stability: float          # 0.0-1.0 (derived from timing variance)
    beat_accuracy: float            # 0.0-1.0 (1 - timing_error_ms/100)
    articulation_clarity: float     # 0.0-1.0 (1 - missed_chords * 0.15)
    phrase_coherence: float         # 0.0-1.0 (score / 100)

class SessionStats(BaseModel):
    """Session context for AI."""

    tempo_bpm: int
    bars_completed: int
    total_takes: int
    style_id: str                   # e.g., "swing_basic", "bossa"

class CoachContextPacket(BaseModel):
    """Full context sent to AI coach."""

    session_id: str
    groove_metrics: GrooveMetrics
    session_stats: SessionStats

    # Optional detailed timing data
    error_by_step: Optional[List[float]] = None
    timing_error_ms: Optional[Dict[str, float]] = None  # mean, std, max
```

**Schema: `CoachingDraft` (response from sg-ai)**

```python
# Location: sg-ai/packages/sg-engine/sg_engine/schemas.py

class FeedbackItem(BaseModel):
    """Single piece of coaching feedback."""

    category: Literal["strength", "focus_area", "tip", "warning"]
    text: str
    confidence: float               # 0.0-1.0

class ExerciseHint(BaseModel):
    """Suggested exercise."""

    title: str
    description: str
    duration_minutes: Optional[int] = None

class GrooveScore(BaseModel):
    """AI-computed groove quality score."""

    value: float                    # 0-100
    breakdown: Optional[Dict[str, float]] = None

class CoachingDraft(BaseModel):
    """Full AI coaching response."""

    feedback: List[FeedbackItem]    # Multiple insights
    groove_score: Optional[GrooveScore] = None
    next_focus: Optional[ExerciseHint] = None
    summary: Optional[str] = None   # One-line summary

    # Timing-specific (if timing_feedback was called)
    timing_explanation: Optional[str] = None
    timing_exercises: Optional[List[ExerciseHint]] = None
```

**Example AI Response:**

```json
{
  "feedback": [
    {
      "category": "strength",
      "text": "Your chord changes are landing cleanly on the downbeats.",
      "confidence": 0.85
    },
    {
      "category": "focus_area",
      "text": "You're consistently 15-20ms late on beat 2. This creates a laid-back feel, but it's drifting too far.",
      "confidence": 0.92
    },
    {
      "category": "tip",
      "text": "Try accenting beat 2 slightly to lock it in place.",
      "confidence": 0.78
    }
  ],
  "groove_score": {
    "value": 72.5,
    "breakdown": {
      "timing": 0.68,
      "dynamics": 0.82,
      "feel": 0.71
    }
  },
  "next_focus": {
    "title": "Beat 2 Lock Drill",
    "description": "Play quarter notes on beat 2 only, with metronome on 1 and 3.",
    "duration_minutes": 5
  },
  "timing_explanation": "Your timing on beat 2 averages +17ms (late). This is common when focusing on chord voicings—the left hand anticipates while the right hand lags."
}
```

---

### Layer 5: Combined Response (Hybrid Output)

**Schema: `EnhancedCoachingResponse` (merged deterministic + AI)**

```python
class EnhancedCoachingResponse(BaseModel):
    """
    Final coaching response combining both systems.
    Deterministic is always present; AI fields are optional.
    """

    # === Always present (deterministic) ===
    coach_hint: str                 # From 15-template matrix
    difficulty_delta: float
    tempo_delta_bpm: float
    density_bucket: str
    syncopation_bucket: str

    # === Optional (AI-enhanced) ===
    ai_available: bool = False
    ai_latency_ms: Optional[int] = None

    # AI coaching additions
    coaching_tip: Optional[str] = None          # Best tip from AI
    timing_insight: Optional[str] = None        # Specific timing feedback
    exercise_hint: Optional[str] = None         # Suggested drill
    ai_groove_score: Optional[float] = None     # AI-computed score

    # Metadata
    source: Literal["deterministic", "hybrid"] = "deterministic"
```

**Example Combined Output:**

```json
{
  "coach_hint": "Solid. Hold steady and try to reduce timing error on the next loop. Tempo unchanged. Density: medium. Sync: light.",
  "difficulty_delta": 0.0,
  "tempo_delta_bpm": 0.0,
  "density_bucket": "medium",
  "syncopation_bucket": "light",

  "ai_available": true,
  "ai_latency_ms": 287,

  "coaching_tip": "You're consistently 15-20ms late on beat 2.",
  "timing_insight": "Your timing on beat 2 averages +17ms (late). Try accenting beat 2 slightly.",
  "exercise_hint": "Beat 2 Lock Drill: Play quarter notes on beat 2 only, with metronome on 1 and 3.",
  "ai_groove_score": 72.5,

  "source": "hybrid"
}
```

---

### Schema Evolution Summary

| Layer | Schema | Size | Latency | Source |
|-------|--------|------|---------|--------|
| 1. Arduino → Pi | `TimingEvent` | 8 bytes | 1-5ms | Hardware |
| 2. Scoring | `TakeMetrics` | ~200 bytes | 5-20ms | Pi 5 |
| 3. Deterministic | `ProgressionDecision` | ~500 bytes | <1ms | Pi 5 |
| 4. AI Request | `CoachContextPacket` | ~2KB | - | Pi 5 → Cloud |
| 4. AI Response | `CoachingDraft` | ~1KB | 130-460ms | Cloud → Pi 5 |
| 5. Combined | `EnhancedCoachingResponse` | ~1.5KB | Total: 27-546ms | Pi 5 |

---

### Migration Path

**Phase 1 (v1.0)**: Deterministic only
- Implement layers 1-3
- Ship with 15-template coach_hint
- Validate core feedback loop

**Phase 2 (v1.1)**: Add AI layer
- Implement layer 4 (cloud service)
- Add optional AI fields to layer 5
- Graceful fallback when offline

**Phase 3 (v2.0)**: Full hybrid
- AI enhances every response when available
- User preference for AI verbosity
- Analytics on AI vs deterministic outcomes

---

*Document created: 2026-02-04*
*Related repos: string_master_v.4.0, sg-agentd, sg-ai, sg-spec*
