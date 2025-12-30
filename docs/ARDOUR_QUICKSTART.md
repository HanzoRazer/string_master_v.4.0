# Ardour Quick-Start for Raspberry Pi

**Target Platform:** Raspberry Pi 4/5 with Pi OS (Debian-based Linux)

---

## Why Ardour on Pi?

✅ **Free & open-source** — No licensing costs  
✅ **Professional features** — Industry-standard DAW  
✅ **Linux-native** — Optimized for Pi OS  
✅ **Low latency** — JACK audio support  
✅ **Resource-efficient** — Runs on Pi 4/5 with 4-8GB RAM  
✅ **Active development** — Regular updates & community support  

Perfect companion for zt-band accompaniment generation.

---

## Installation

### Method 1: APT (Easiest)

```bash
sudo apt update
sudo apt install ardour
```

**Pros:** Simple, well-tested on Pi OS  
**Cons:** May be older version (typically Ardour 6.x)

---

### Method 2: Flatpak (Latest Version)

```bash
# Install Flatpak
sudo apt install flatpak

# Add Flathub repository
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install Ardour
flatpak install flathub org.ardour.Ardour

# Run
flatpak run org.ardour.Ardour
```

**Pros:** Latest Ardour version (7.x or 8.x)  
**Cons:** Larger download, slightly slower startup

---

## Initial Setup

### 1. Launch Ardour

```bash
ardour6  # Or: flatpak run org.ardour.Ardour
```

First launch shows setup wizard.

---

### 2. Audio/MIDI Setup

**Backend:** JACK (recommended) or ALSA  
**Sample Rate:** 48000 Hz (standard)  
**Buffer Size:** 256 or 512 samples (balance latency vs CPU)  
**Channels:** 2 in / 2 out (stereo)

**JACK Configuration (Advanced):**
```bash
# Install JACK
sudo apt install jackd2 qjackctl

# Launch JACK Control
qjackctl
```

Adjust settings:
- Realtime: Enabled
- Frames/Period: 256
- Sample Rate: 48000 Hz
- Periods/Buffer: 2

---

### 3. Create New Session

1. File → New Session
2. Name: e.g., "zt-band_practice"
3. Location: `/home/pi/Music/Ardour/`
4. Template: Empty session
5. Click "Open"

---

## Import zt-band MIDI

### Step 1: Export from zt-band

```bash
cd ~/string_master_v.4.0
source .venv/bin/activate

# Generate backing track
zt-band create --chords "Dm7 G7 Cmaj7" --style swing --tempo 120

# Export for DAW
zt-band daw-export backing.mid
```

Output: `exports/daw/YYYY-MM-DD_HHMMSS/backing.mid`

---

### Step 2: Import to Ardour

**Method A: Drag & Drop**
1. Open file manager
2. Navigate to `exports/daw/YYYY-MM-DD_HHMMSS/`
3. Drag `backing.mid` onto Ardour timeline

**Method B: Menu Import**
1. Session → Import
2. Click "Add Files"
3. Browse to `backing.mid`
4. Select "MIDI track per channel"
5. Click "Import"

---

### Step 3: Verify Track Layout

Should see 3 MIDI tracks:
```
Track 1: Comp    (Piano/chords)
Track 2: Bass    (Walking bass)
Track 3: Drums   (Rhythm section)
```

---

## Add Virtual Instruments

Ardour doesn't include built-in synths, so we need plugins.

### Install Plugin Bundles

```bash
# Calf Studio Gear (excellent quality)
sudo apt install calf-plugins

# x42 plugins (lightweight)
sudo apt install x42-plugins

# LSP plugins (low-latency)
sudo apt install lsp-plugins

# FluidSynth (GM soundfont player)
sudo apt install fluidsynth fluid-soundfont-gm
```

---

### Assign Instruments to Tracks

#### Track 1: Comp (Piano)

1. Right-click track → Add Plugin → Instrument
2. Search: "FluidSynth" or "Calf Organ" or "x42 Piano"
3. Select plugin → Click "Add"

**Recommended:**
- **FluidSynth** (GM Piano, Program 0)
- **Calf Organ** (Electric Piano alternative)
- **x42 Piano** (Basic but lightweight)

---

#### Track 2: Bass

1. Right-click track → Add Plugin → Instrument
2. Search: "FluidSynth" (set to GM Bass, Program 32)
3. Or: Calf Monosynth (analog bass sound)

**Recommended:**
- **FluidSynth** (GM Acoustic Bass)
- **Calf Monosynth** (Fat bass with filter)

---

#### Track 3: Drums

1. Right-click track → Add Plugin → Instrument
2. Search: "FluidSynth" (GM Drum Kit, Channel 9)
3. Or: Load drum samples via DrumGizmo

**Recommended:**
- **FluidSynth** (GM Drum Kit, instant setup)
- **DrumGizmo** (realistic multisamples, higher CPU)

**FluidSynth Setup:**
```bash
# Verify soundfont location
ls /usr/share/sounds/sf2/FluidR3_GM.sf2

# If missing, install
sudo apt install fluid-soundfont-gm
```

In Ardour:
1. Open FluidSynth plugin window
2. Load Soundfont: `/usr/share/sounds/sf2/FluidR3_GM.sf2`
3. For drums: Set to Channel 9 (GM standard)

---

## Configure Routing

### Enable MIDI Input Monitoring

For each MIDI track:
1. Click "Input" button (monitor icon)
2. Set to "Auto Input" or "Disk"
3. Ensure MIDI is routed to instrument plugin

---

### Audio Output Routing

Tracks should auto-route to Master bus:
```
Comp  → Master/Audio 1
Bass  → Master/Audio 1
Drums → Master/Audio 1
```

Check: Mixer view → verify green routing lines.

---

## Playback & Mixing

### Basic Playback

1. Press **Space** to play/stop
2. Press **Home** to return to start
3. Press **L** to enable loop

---

### Adjust Tempo

If MIDI tempo doesn't match:
1. Window → Tempo Map
2. Double-click tempo marker
3. Enter desired BPM (e.g., 120)

Or: Right-click timeline → Set Tempo

---

### Mix Levels

**Mixer Window:** Window → Mixer (or Ctrl+Alt+M)

Typical levels:
- **Comp:** -8 to -12 dB
- **Bass:** -6 to -10 dB
- **Drums:** -8 to -12 dB (kick louder, hi-hat quieter)

**Master Bus:** Keep below 0 dB to avoid clipping.

---

### Add Effects (Optional)

**Reverb (Room ambience):**
1. Right-click Master bus → Add Plugin → Reverb
2. Recommended: x42 Convolver or Calf Reverb
3. Mix: 15-25%

**Compression (Glue mix):**
1. Right-click Master bus → Add Plugin → Compressor
2. Recommended: Calf Compressor or LSP Compressor
3. Ratio: 3:1, Attack: 5ms, Release: 50ms

---

## Performance Optimization for Pi

### Reduce CPU Load

✅ **Lower buffer size** if latency is acceptable (256 → 512 samples)  
✅ **Use lightweight plugins** (x42, Calf over heavy synths)  
✅ **Freeze tracks** (Track → Freeze) to render MIDI as audio  
✅ **Limit reverb** — reverb plugins are CPU-heavy  
✅ **Close unused windows** (Mixer, Editor, Plugin UI)  
✅ **Disable video timeline** (View → uncheck Video Timeline)  

---

### Monitor CPU Usage

**Top bar:** Shows DSP load percentage  
**Target:** Keep below 70% for smooth playback  
**If above 80%:** Increase buffer size or freeze tracks

---

## Export Audio (Bounce Mix)

### Step 1: Set Export Range

1. Click and drag on timeline ruler to select region
2. Or: Session → Select All

---

### Step 2: Export

1. Session → Export → Export to Audio File(s)
2. Format: **WAV** (highest quality) or **MP3** (smaller)
3. Sample Rate: **48000 Hz** (matches session)
4. Bit Depth: **16-bit** (CD quality) or **24-bit** (archival)
5. Click "Export"

**Output:** `/home/pi/Music/Ardour/zt-band_practice/export/`

---

## Common Issues & Fixes

### Problem: No sound on playback

**Cause:** Instrument plugins not assigned

**Fix:**
1. Check each MIDI track has an instrument plugin
2. Enable monitoring (Input button)
3. Verify audio routing to Master bus

---

### Problem: JACK connection errors

**Cause:** JACK server not running or misconfigured

**Fix:**
```bash
# Stop JACK
killall jackd

# Restart with correct settings
jackd -d alsa -r 48000 -p 512
```

Or use QJackCtl GUI to manage connections.

---

### Problem: Crackling/distortion during playback

**Cause:** Buffer size too small (DSP overload)

**Fix:**
1. Edit → Preferences → Audio/MIDI
2. Increase Buffer Size: 256 → 512 or 1024
3. Restart audio engine

---

### Problem: MIDI tracks not visible after import

**Cause:** Ardour imported as audio instead of MIDI

**Fix:**
1. Delete imported tracks
2. Re-import: Ensure "MIDI" option is selected
3. Check file is actually `.mid` format

---

### Problem: Drums not playing (silent)

**Cause:** Channel 9 not routed to drum kit

**Fix:**
1. Select drum track
2. Open FluidSynth plugin
3. Verify Channel 9 is active
4. Load GM Drum Kit preset

---

## Workflow: zt-band → Ardour Loop

### Typical Practice Session

```bash
# 1. Generate backing track
cd ~/string_master_v.4.0
source .venv/bin/activate
zt-band create --chords "Dm7 G7 Cmaj7" --style swing --tempo 120

# 2. Export for DAW
zt-band daw-export backing.mid

# 3. Launch Ardour
ardour6

# 4. Import MIDI (drag & drop)
# 5. Assign instruments (FluidSynth)
# 6. Hit play
# 7. Practice improvisation over changes
```

---

## Save & Reload Sessions

### Save Session

1. Session → Save (Ctrl+S)
2. Or: Ardour auto-saves every 2 minutes

**Files saved:**
- Session state: `.ardour` XML file
- Audio: `interchange/` folder
- Plugins: Automation data

---

### Reload Session

1. Launch Ardour
2. File → Recent Sessions → Select session
3. All tracks, instruments, and routing restored

---

## Recommended Pi Hardware

### Minimum Specs
- **Raspberry Pi 4** (4GB RAM)
- **32GB SD card** (Class 10 or faster)
- **USB audio interface** (optional, improves latency)
- **Headphones or monitors**

### Optimal Specs
- **Raspberry Pi 5** (8GB RAM)
- **128GB NVMe SSD** (via USB 3.0 or HAT)
- **Focusrite Scarlett Solo** (USB audio interface)
- **Active studio monitors** (or quality headphones)

---

## Advanced: JACK Routing

If using JACK, you can route audio between apps:

### Example: zt-band → FluidSynth → Ardour

```bash
# Terminal 1: Start JACK
qjackctl

# Terminal 2: Run FluidSynth standalone
fluidsynth -a jack /usr/share/sounds/sf2/FluidR3_GM.sf2

# Terminal 3: Send MIDI from zt-band
zt-band play --chords "Dm7 G7 C"
```

Use QJackCtl's "Graph" view to connect:
```
zt-band MIDI out → FluidSynth MIDI in
FluidSynth Audio out → Ardour Audio in
```

---

## Resources

### Documentation
- Ardour Manual: https://manual.ardour.org/
- JACK Audio: https://jackaudio.org/
- Calf Plugins: https://calf-studio-gear.org/

### Forums
- Ardour Community: https://discourse.ardour.org/
- Raspberry Pi Audio: https://www.raspberrypi.org/forums/

### Video Tutorials
- Ardour Basics: YouTube search "Ardour tutorial"
- JACK on Pi: YouTube search "JACK audio Raspberry Pi"

---

## Integration with zt-band CLI

### Relevant Commands

```bash
# Generate with specific tempo/style
zt-band create --chords "Am7 D7 Gmaj7" --style bossa --tempo 140

# Export multiple progressions
zt-band create --program programs/autumn_leaves.ztprog
zt-band daw-export autumn_leaves_ballad.mid

# Run exercise and export
zt-band ex-run exercises/cycle_fifths_roots.ztex
zt-band daw-export cycle_fifths_roots.mid
```

---

## Touchscreen UI Workflow

If running zt-band with Pi touchscreen:

1. **Touch UI:** Select progression, style, tempo
2. **zt-band:** Generates MIDI in background
3. **DAW Export:** Auto-exports to timestamped folder
4. **Ardour:** Auto-imports from watch folder (optional)
5. **Practice:** Play along with backing track

**Future enhancement:** Watch folder import automation.

---

## Checklist: Ready to Practice

- [ ] Ardour installed and launching
- [ ] JACK audio working (or ALSA fallback)
- [ ] Plugin bundles installed (Calf, x42, FluidSynth)
- [ ] zt-band exports successfully
- [ ] MIDI imports into Ardour
- [ ] Instruments assigned and producing sound
- [ ] Master bus not clipping
- [ ] Export to audio working
- [ ] Session saves correctly

---

**Last Updated:** December 29, 2025  
**Status:** Production — zt-band v0.1.0 + Ardour 6.x/7.x  
**Tested on:** Raspberry Pi 4 (8GB), Pi OS Bookworm
