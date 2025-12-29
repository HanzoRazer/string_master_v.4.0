# Seed Sources Quickstart

**3-minute guide to storing and tracking seed material.**

Full policy: [SEED_SOURCES.md](./SEED_SOURCES.md)

---

## Where Files Go

```
seeds/
  handcrafted/              # stuff you/we create directly
  public_domain_or_open/    # CC0, public domain, open licensed
  licensed_third_party/     # paid packs, vendor libraries
  ai_generated_external/    # Suno, etc.
    suno/
      raw/                  # original audio downloads
      stems/                # stem-separated tracks
      midi/                 # MIDI extracted from stems
      meta/                 # .seed.json metadata files
```

---

## 3 Examples

### 1) Handcrafted Pattern

**File:** `seeds/handcrafted/swing_comping_01.mid`  
**Metadata:** `seeds/handcrafted/swing_comping_01.seed.json`

```json
{
  "source_category": "handcrafted",
  "creator": "greg_brown",
  "created_at": "2025-12-29",
  "assets": {
    "midi": ["seeds/handcrafted/swing_comping_01.mid"]
  },
  "tags": ["swing", "comping", "medium_tempo"],
  "notes": "Basic Charleston rhythm for teaching swing feel."
}
```

---

### 2) Licensed Third-Party Pack

**File:** `seeds/licensed_third_party/vendor_jazz_pack/groove_12.mid`  
**Metadata:** `seeds/licensed_third_party/vendor_jazz_pack/groove_12.seed.json`

```json
{
  "source_category": "licensed_third_party",
  "vendor_name": "JazzGrooves Inc",
  "product_name": "Pro Jazz MIDI Pack Vol 1",
  "license_notes": "Licensed for use in productions; no raw redistribution.",
  "created_at": "2025-11-15",
  "assets": {
    "midi": ["seeds/licensed_third_party/vendor_jazz_pack/groove_12.mid"]
  },
  "tags": ["bossa", "latin", "120bpm"],
  "notes": "Purchased pack; extract patterns, don't ship raw MIDI."
}
```

---

### 3) Suno-Generated Backing

**Files:**
- `seeds/ai_generated_external/suno/raw/ballad_c_major_001.wav`
- `seeds/ai_generated_external/suno/stems/ballad_c_major_001_instrumental.wav`
- `seeds/ai_generated_external/suno/midi/ballad_c_major_001_bass.mid`

**Metadata:** `seeds/ai_generated_external/suno/meta/ballad_c_major_001.seed.json`

```json
{
  "source_category": "ai_generated_external",
  "provider": "suno",
  "plan_tier": "pro",
  "suno_task_id": "abc123-task",
  "suno_audio_id": "def456-audio",
  "created_at": "2025-12-29",
  "assets": {
    "audio": "seeds/ai_generated_external/suno/raw/ballad_c_major_001.wav",
    "stems": [
      "seeds/ai_generated_external/suno/stems/ballad_c_major_001_instrumental.wav"
    ],
    "midi": [
      "seeds/ai_generated_external/suno/midi/ballad_c_major_001_bass.mid"
    ]
  },
  "tags": ["ballad", "C_major", "70bpm"],
  "notes": "Used for pattern extraction and backing track variations."
}
```

---

## Quick Rules

✅ **DO:** Track every seed with a `.seed.json` file  
✅ **DO:** Extract patterns → store in `seeds/derived/patterns/`  
✅ **DO:** Use seeds for practice/pedagogy internally

❌ **DON'T:** Redistribute raw third-party or AI assets without checking terms  
❌ **DON'T:** Lose provenance (no orphan files)

---

## Template

Copy `seeds/_TEMPLATE.seed.json` and fill in the blanks.

---

**That's it.** Now go seed some grooves. 🎸
