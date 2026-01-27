"""
red_house_zone_tritone_walkthrough.py

A "teaching script" you can run to explain Red House in zone-tritone terms:
- prints zones
- prints the three core blues dominants in Bb
- prints each chord's tritone axis
- shows a "backdoor" cadence in Bb major (Ebmaj7 -> Ab7 -> Bbmaj7)
"""

from zone_tritone_tools import (
    pc, name_from_pc, zone,
    dominant_tritone_axis, dominant_roots_from_axis,
    backdoor_cadence_roots
)

def show_zone(note: str):
    p = pc(note)
    z = zone(p)
    print(f"{note:>3} pc={p:2d} zone={'Z1(even)' if z==0 else 'Z2(odd)'}")

def show_dom7(root_name: str, prefer_flats=True):
    r = pc(root_name)
    ax = dominant_tritone_axis(r)
    r_sub = (r + 6) % 12
    d1, d2 = dominant_roots_from_axis(ax)
    print(f"{root_name}7:")
    print(f"  root={name_from_pc(r, prefer_flats)}  tritone_axis=({name_from_pc(ax[0], prefer_flats)}, {name_from_pc(ax[1], prefer_flats)})")
    print(f"  dominant_pair_by_axis = {name_from_pc(d1, prefer_flats)}7 / {name_from_pc(d2, prefer_flats)}7")
    print(f"  tritone_sub_root (root+6) = {name_from_pc(r_sub, prefer_flats)}")
    print()

def show_backdoor(key_name: str, prefer_flats=True):
    I = pc(key_name)
    IV, bVII, I2 = backdoor_cadence_roots(I)
    print(f"Backdoor cadence in {key_name} major: IV -> bVII7 -> I")
    print(f"  {name_from_pc(IV, prefer_flats)}maj7 -> {name_from_pc(bVII, prefer_flats)}7 -> {name_from_pc(I2, prefer_flats)}maj7")
    print("  Guide-tone resolution idea on bVII7 -> I:")
    print("    (3rd of bVII7) -> (3rd of I)  and  (7th of bVII7) -> (5th/7th of I)")
    print()

if __name__ == "__main__":
    print("Zones (examples):")
    for n in ["Bb", "A", "Ab", "G", "D", "Eb", "E"]:
        show_zone(n)
    print()

    print("Core dominants in Bb blues (Red House frame):")
    for chord_root in ["Bb", "Eb", "F"]:
        show_dom7(chord_root, prefer_flats=True)

    show_backdoor("Bb", prefer_flats=True)
