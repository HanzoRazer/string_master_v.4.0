#!/usr/bin/env python3
"""Upgrade .ztprog files to v2 format with tempo_range, levels, and Roman numerals."""

import os
import re
import yaml
from pathlib import Path

# Chord to Roman numeral mappings (relative to common roots)
CHORD_TO_ROMAN = {
    # Major keys
    'Cmaj7': 'Imaj7', 'Dm7': 'ii7', 'Em7': 'iii7', 'Fmaj7': 'IVmaj7',
    'G7': 'V7', 'Am7': 'vi7', 'Bm7b5': 'viiø7',
    'C7': 'I7', 'F7': 'IV7', 'D7': 'II7', 'E7': 'III7', 'A7': 'VI7', 'B7': 'VII7',
    # Bb key
    'Bbmaj7': 'Imaj7', 'Bb7': 'I7', 'Eb7': 'IV7', 'Ebmaj7': 'IVmaj7',
    'Cm7': 'ii7', 'Fm7': 'v7', 'Ab7': 'bVII7',
    # Minor
    'Am7b5': 'iiø7', 'Dm7b5': 'iiø7', 'Gm7': 'i7',
}

def calc_tempo_range(tempo):
    """Calculate reasonable tempo range (roughly ±40%)."""
    low = max(40, int(tempo * 0.65))
    high = min(280, int(tempo * 1.5))
    return [low, high]

def calc_levels(tempo):
    """Generate beginner/intermediate/advanced levels."""
    return {
        'beginner': {
            'tempo_bpm': max(40, int(tempo * 0.65)),
            'comping': 'whole_notes'
        },
        'intermediate': {
            'tempo_bpm': tempo,
            'comping': 'rhythmic'
        },
        'advanced': {
            'tempo_bpm': min(280, int(tempo * 1.5)),
            'comping': 'syncopated'
        }
    }

def upgrade_file(filepath):
    """Upgrade a single .ztprog file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    try:
        data = yaml.safe_load(content)
    except:
        print(f"  SKIP (parse error): {filepath}")
        return False
    
    if not data:
        print(f"  SKIP (empty): {filepath}")
        return False
    
    # Already upgraded?
    if 'tempo_range' in data and 'levels' in data:
        print(f"  SKIP (already v2): {filepath}")
        return False
    
    # Get tempo
    tempo = data.get('tempo') or data.get('tempo_bpm') or 100
    
    # Add new fields
    data['tempo_bpm'] = tempo
    data['tempo_range'] = calc_tempo_range(tempo)
    data['levels'] = calc_levels(tempo)
    
    # Remove old tempo field if present
    if 'tempo' in data and 'tempo_bpm' in data:
        del data['tempo']
    
    # Write back
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"  UPGRADED: {filepath}")
    return True

def main():
    programs_dir = Path("C:/Users/thepr/Downloads/string_master_v.4.0/programs")
    
    count = 0
    for ztprog in programs_dir.rglob("*.ztprog"):
        if upgrade_file(ztprog):
            count += 1
    
    print(f"\nUpgraded {count} files.")

if __name__ == "__main__":
    main()
