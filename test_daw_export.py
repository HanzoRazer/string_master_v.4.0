#!/usr/bin/env python3
"""Quick test: Generate MIDI → Export for DAW → Verify files exist."""

import subprocess
import sys
from pathlib import Path


def main():
    print("=== zt-band DAW Export Test ===\n")

    # 1) Generate a quick backing track
    print("1. Generating backing track...")
    result = subprocess.run([
        sys.executable, "-m", "zt_band.cli", "create",
        "--chords", "Dm7 G7 Cmaj7 Am7",
        "--style", "bossa",
        "--tempo", "110",
        "--outfile", "test_backing.mid"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FAILED to generate: {result.stderr}")
        return 1
    print("✓ Generated test_backing.mid\n")

    # 2) Export for DAW
    print("2. Exporting for DAW...")
    result = subprocess.run([
        sys.executable, "-m", "zt_band.cli", "daw-export",
        "--midi", "test_backing.mid",
        "--export-root", "exports/test_daw"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FAILED to export: {result.stderr}")
        return 1

    print(result.stdout)

    # 3) Verify export structure
    print("\n3. Verifying export structure...")
    export_root = Path("exports/test_daw")
    if not export_root.exists():
        print("✗ Export root doesn't exist")
        return 1

    # Find the timestamped folder
    exports = sorted(export_root.glob("*"))
    if not exports:
        print("✗ No timestamped export folder")
        return 1

    latest = exports[-1]
    midi_file = latest / "test_backing.mid"
    guide_file = latest / "IMPORT_DAW.md"

    if not midi_file.exists():
        print(f"✗ Missing MIDI: {midi_file}")
        return 1
    if not guide_file.exists():
        print(f"✗ Missing guide: {guide_file}")
        return 1

    print("✓ Export structure verified:")
    print(f"  - {midi_file}")
    print(f"  - {guide_file}")

    print("\n✅ SUCCESS: DAW export ready for import!")
    print(f"\n📂 Import folder: {latest}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
