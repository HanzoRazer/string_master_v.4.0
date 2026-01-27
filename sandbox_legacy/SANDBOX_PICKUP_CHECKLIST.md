# Sandbox Pickup Checklist

> Status report from the crashed ChatGPT sandbox session
> (source: `ANALYZR MIDI SCRIPT_CHAT.MD`, 5149 lines)
>
> Date: 2026-01-27
> Purpose: Feed this into the next sandbox session to resume work

---

## Incomplete / Not Started

### 1. Red House Extended Etude (bars 1-24 + variation)
- **Status**: Crashed — sandbox died before generation
- **Key**: B (standard Hendrix tuning)
- **Source**: "In Deep With Jimi Hendrix" by Andy Aledort, pages 1-2
- **What was planned**:
  - .mid for bars 1-24 (full intro section)
  - .mid variation for bars 16-24
  - .ztex lesson wrapper
  - .ztprog shuffle backing (slow blues in B)
- **What exists**: Nothing — generate from scratch
- **Style**: Slow blues shuffle, expressive bends, minor pentatonic
- **Priority**: High — was the active task when the sandbox crashed

### 2. 40 Blues Intros/Outros (38 of 40 remaining)
- **Status**: Only 2 of 40 extracted
- **Source**: `316086156-40-Essential-Blues-Guitar-Intros-and-Outros.docx`
- **Completed**:
  - `srv_outro_bb_bend` (SRV outro, key E, Texas Blues, advanced)
  - `albertking_intro_slideup` (Albert King intro, key G, Chicago Blues, easy)
- **What was planned**:
  - Extract all 40 phrases into `data/blues_phrases.yaml` index
  - Generate .mid + .ztex + .ztprog per phrase
  - Tag by: artist style, difficulty, phrase_type (intro/outro), key
  - Group into .ztplay playlists by style (Texas, Chicago, British)
  - Enable random tutorial mode from YAML index
- **Artist coverage needed**: SRV, BB King, Albert King, Robert Johnson,
  Gary Moore, Peter Green, Hendrix, Clapton
- **Priority**: Medium — large batch, can be done incrementally

### 3. "When You Have a Good Friend" (Robert Johnson)
- **Status**: .mid exists, needs .ztex + .ztprog
- **Key**: C (slow blues)
- **Tempo**: 60 BPM
- **What exists**:
  - `when_you_have_a_good_friend.mid` (in `exercises/bucket_a/midi/`)
  - Melody: slow C blues vocal line, 12-bar form
- **What's needed**:
  - .ztex lesson wrapper (12-bar vocal line phrasing)
  - .ztprog slow shuffle backing (drum + bass + shell voicings)
- **Priority**: Quick win — .mid already committed

### 4. Chromatic Triplet Chain Exercises (Barry Harris)
- **Status**: Not started — identified as a gap in the redundancy analysis
- **Source**: Barry Harris Jazz Workshop PDF (pages on triplet articulation)
- **Concept**: Chromatic triplet cells that connect chord tones through
  diminished passing tones
- **What's needed**:
  - Define `phrase_type: "chromatic_cells"` or `"triplet_resolution_chain"`
  - Create 2-3 example phrases in .mid + .ztex
  - Add to `data/enclosure_examples.yaml` (or new `data/chromatic_cells.yaml`)
  - .ztprog backing (static chord, metronome)
- **Related to**: Existing enclosure exercises, pivot_from_neighbor rule
- **Priority**: Medium — fills a gap in Barry Harris coverage

### 5. Drop-2 Voice Motion Tagging (v6/b6 labels)
- **Status**: Not started — identified from Drop-2 Exercises PDF
- **Source**: `341495925-Barry-Harris-Drop-2-Exercises.pdf`
- **Concept**: Tag voicing exercises with voice motion labels:
  - `v6`: soprano and tenor move
  - `b6`: bass and alto move
  - String set: top 4 vs middle 4
  - Motion type: contrary, parallel, oblique
- **What's needed**:
  - Add `voice_motion` metadata to existing `exercises/voicings/` .ztex files
  - Create `data/voicing_motion_ruleset.yaml` with tagged examples
  - Example: `v6_contrary_top4.ztex`
- **Existing exercises to update**:
  - `diminished_drop2_cycle.ztex` (already in voicings/)
- **Priority**: Low — metadata enrichment, not new content

### 6. Blackberry Blossom + Muleskinner (partial)
- **Status**: Only A1 and B1 sections extracted
- **Source**: Tony Rice Lesson Method (Homespun) PDF
- **Key**: G (both tunes)

#### Blackberry Blossom
- **What exists**:
  - A1 motif .mid (2 bars, scalar G run)
  - B1 motif .mid (bars 10-13, timing shift)
  - .ztex wrappers for both sections
  - .ztprog 8-bar backing (G-C-D-G)
- **What's needed**:
  - A2 section (bars 3-4)
  - B2 section (bars 14-16)
  - Full .ztplay chaining A1-A2-B1-B2
  - Complete etude .mid (all sections combined)

#### Muleskinner Blues
- **What exists**:
  - 4-bar intro .mid (G-A-B-C-D-E-G-F#-E-D + extension)
  - .ztex wrapper (4-bar scope)
  - .ztprog backing (4-bar G-G-C-G)
- **What's needed**:
  - Bars 5-8 and 9-16 phrases
  - Full .ztplay etude
  - Variation .mid for contrast

- **Priority**: Medium — good bluegrass repertoire content

### 7. Articulation Model Schema Field
- **Status**: Not started — identified as a schema gap
- **Source**: Barry Harris Jazz Workshop analysis
- **Concept**: New schema field for articulation patterns:
  ```yaml
  articulation_model:
    type: string
    enum:
      - "3-2-1_pulloff"
      - "hammer_on_triplet"
      - "chromatic_slide"
      - "ghost_note_accent"
      - "rake_mute"
  ```
- **Where it goes**: `schemas/ztex.schema.json` or
  `schemas/pedagogy_ruleset_v1.schema.json`
- **Purpose**: Allow .ztex exercises to declare required articulation
  techniques for assessment
- **Priority**: Low — schema enrichment for future assessment features

---

## Already Completed and Committed

| Pack | Format | Location |
|------|--------|----------|
| Gospel Turnaround C/G/D | .ztex + .ztprog + .ztplay | exercises/bucket_a/, programs/bucket_a/, playlists/bucket_a/ |
| Gospel Color Upgrades C | .ztex + .ztprog | exercises/bucket_a/, programs/bucket_a/ |
| Gospel Chromatic Lick C | .ztex | exercises/bucket_a/ |
| Dorian Gospel Backdoor Cm | .ztex + .ztprog + .ztplay | exercises/bucket_a/, programs/bucket_a/, playlists/bucket_a/ |
| Dorian Chromatic Lick Cm | .ztex | exercises/bucket_a/ |
| Voodoo Child Intro Etude Em | .ztex + .ztprog | exercises/bucket_a/, programs/bucket_a/ |
| C Dorian Intro Etude | .ztex + .ztprog | exercises/bucket_a/, programs/bucket_a/ |
| Walkin' Blues Riff C | .ztex + .ztprog | exercises/bucket_a/, programs/bucket_a/ |
| Enclosure exercises | .ztex + .mid + .ztprog | exercises/enclosures/, programs/ |
| Pivot packs (12 keys) | .mid + .ztex + .ztprog | exercises/pivots/, pivot_enclosure_pack/, pivot_4bar_allkeys_pack/ |
| Voicing cycles | .ztex + .mid + .ztprog | exercises/voicings/ |
| Blues phrases (SRV, Albert King) | .ztex + .mid + .ztprog | exercises/blues/ |
| Blues turnarounds (3 types) | .ztex + .mid + .ztprog | exercises/blues_turnarounds/ |
| G Bluegrass licks (1-4) | .ztex + .mid + .ztprog | various |

## MIDI Files (committed to exercises/bucket_a/midi/)

| File | Source |
|------|--------|
| voodoo_child_intro_etude.mid | Hendrix sandbox session |
| voodoo_child_intro_variation.mid | Hendrix sandbox session |
| beginning_intro_dorian_etude.mid | Hendrix sandbox session |
| walkin_blues_main_riff.mid | Blues sandbox session |
| walkin_blues_variation_riff.mid | Blues sandbox session |
| when_you_have_a_good_friend.mid | Robert Johnson sandbox session |

---

## Source Documents (for next sandbox)

| Document | Content | Location |
|----------|---------|----------|
| ANALYZR MIDI SCRIPT_CHAT.MD | Full sandbox transcript (5149 lines) | sandbox_legacy/ |
| Musical_Cadence_Explaine.md | Cadence theory + gospel lesson | sandbox_legacy/ |
| 5 legacy YAML exercises | Old-format exercise definitions | sandbox_legacy/ |
| Barry Harris PDFs | Workshop, Drop-2, Diminished Patterns | (external — re-upload to new sandbox) |
| 40 Blues Intros/Outros .docx | Phrasebook | (external — re-upload to new sandbox) |
| Blues Turnarounds E-book .pdf | Turnaround anatomy | (external — re-upload to new sandbox) |
| Tony Rice Lesson Method .pdf | Bluegrass transcriptions | (external — re-upload to new sandbox) |
| In Deep With Jimi Hendrix .pdf | Hendrix etude transcriptions | (external — re-upload to new sandbox) |
| Bluegrass Fakebook .pdf | Lead sheets (Wildwood Flower etc.) | (external — re-upload to new sandbox) |

---

## Recommended Pickup Order

1. **When You Have a Good Friend** — quick win, .mid already exists
2. **Red House Extended Etude** — high priority, was active when crashed
3. **Blackberry Blossom + Muleskinner** — complete the partial sections
4. **Chromatic Triplet Chains** — fills Barry Harris gap
5. **Blues Intros/Outros batch** — large set, do in batches of 5-8
6. **Drop-2 Voice Motion Tagging** — metadata enrichment
7. **Articulation Model Schema** — schema work, do last
