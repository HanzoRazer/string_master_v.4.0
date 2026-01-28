# Zone–Tritone 12-Bar Etude Generator Output (One-Pass Build)

This folder contains **18 etudes** in key C:
- **Backdoor insertion modes**: turnaround / cadence / tag
- **Difficulty by density**: easy (8ths), medium (triplet 8ths), hard (16ths)
- **Style toggle**:
  - `hidden`: blues vocabulary present, but **strong beats and bar endings resolve to chord tones**.
  - `bluesy`: rule inverted so **blue notes are allowed/preferred as destinations**.

Each etude ships as:
- `.mid` (2 tracks: comp shells + melody)
- `.ly` (LilyPond notation source: ChordNames + melody staff)

Filename pattern:
`etude_C_<style>_backdoor-<mode>_density-<difficulty>.(mid|ly)`
