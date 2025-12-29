# Seed Sources — Quickstart

This guide shows how to add seed material to the repository without thinking too hard.

If you follow this document, your seeds will always remain usable,
traceable, and safe to build on later.

---

## 1) Where Seeds Live

All raw seed material goes under:

```
seeds/
  handcrafted/
  public_domain_or_open/
  licensed_third_party/
  ai_generated_external/
```

Each seed **must** have:
- the raw asset(s) (audio, MIDI, stems)
- a matching `*.seed.json` metadata file

---

## 2) Minimal Workflow

1. Decide which category the seed belongs to
2. Place the asset(s) under that folder
3. Create a metadata file using `_TEMPLATE.seed.json`
4. Adjust fields honestly and briefly
5. Done

No analysis or processing is required at this stage.

---

## 3) Example A — Handcrafted Seed

```
seeds/handcrafted/
  cycle_fifths_basic.mid
  cycle_fifths_basic.seed.json
```

```json
{
  "source_category": "handcrafted",
  "provider": "String Master",
  "created_at": "2025-12-29",
  "license_notes": "Original material created in-house",
  "source_reference": "Manual composition",
  "assets": {
    "midi": ["cycle_fifths_basic.mid"]
  },
  "tags": ["cycle", "fifths", "practice"],
  "notes": "Root-motion cycle for early harmonic training"
}
```

---

## 4) Example B — Licensed Third-Party MIDI

```
seeds/licensed_third_party/
  vendor_pack_01/
    groove_12.mid
    groove_12.seed.json
```

```json
{
  "source_category": "licensed_third_party",
  "provider": "Example MIDI Vendor",
  "created_at": "2025-10-12",
  "license_notes": "Purchased MIDI pack; use allowed in productions, not for redistribution",
  "source_reference": "Vendor Pack Vol. 1",
  "assets": {
    "midi": ["groove_12.mid"]
  },
  "tags": ["groove", "swing"],
  "notes": "Used only as internal groove reference"
}
```

---

## 5) Example C — AI-Generated External (Suno)

```
seeds/ai_generated_external/suno/
  raw/track_001.wav
  midi/track_001_bass.mid
  meta/track_001.seed.json
```

```json
{
  "source_category": "ai_generated_external",
  "provider": "suno",
  "created_at": "2025-12-29",
  "license_notes": "Generated under paid plan; used as internal seed and backing material",
  "source_reference": "Suno task_id=XXXX audio_id=YYYY",
  "assets": {
    "audio": ["raw/track_001.wav"],
    "midi": ["midi/track_001_bass.mid"]
  },
  "tags": ["ballad", "C_major"],
  "notes": "Seed for groove extraction and accompaniment variation"
}
```

---

## 6) What Happens Next (Later)

You do **not** need to act on this now.

Later tools may:

* extract patterns into `derived/patterns/`
* convert seeds into `.ztprog` or `.ztex`
* attach seeds to exercises as backing sources

None of that changes how seeds are stored.

---

## 7) Rule of Thumb

If future-you can answer:

* *Where did this come from?*
* *What am I allowed to do with it?*
* *Why is it here?*

…then the seed was added correctly.
