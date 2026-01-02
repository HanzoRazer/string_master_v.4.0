"""
Quick demonstration of the zone-tritone Python library.

Run this script to see the Zone-Tritone System in action.
"""

from zone_tritone import (
    __version__,
    all_tritone_axes,
    build_transition_counts,
    dominant_roots_from_tritone,
    gravity_chain,
    is_zone_cross,
    name_from_pc,
    normalize_transition_matrix,
    pc_from_name,
    zone,
    zone_name,
)


def main():
    print(f"Zone-Tritone System v{__version__}\n")
    print("=" * 60)

    # 1. Zones
    print("\n1️⃣  ZONES: Whole-Tone Families\n")
    print("Zone 1 (even): ", end="")
    print(" ".join(name_from_pc(pc) for pc in range(12) if zone(pc) == 0))
    print("Zone 2 (odd):  ", end="")
    print(" ".join(name_from_pc(pc) for pc in range(12) if zone(pc) == 1))

    # 2. Zone-crossing
    print("\n2️⃣  ZONE-CROSSING: Half-Steps\n")
    examples = [("C", "C#"), ("E", "F"), ("B", "C")]
    for note1, note2 in examples:
        pc1, pc2 = pc_from_name(note1), pc_from_name(note2)
        cross = is_zone_cross(pc1, pc2)
        z1, z2 = zone_name(pc1), zone_name(pc2)
        status = "✓ crosses zones" if cross else "✗ same zone"
        print(f"   {note1:3s} ({z1}) → {note2:3s} ({z2}): {status}")

    # 3. Tritones
    print("\n3️⃣  TRITONE ANCHORS: Six Pairs\n")
    axes = all_tritone_axes()
    for axis in axes:
        name1, name2 = name_from_pc(axis[0]), name_from_pc(axis[1])
        print(f"   {name1}–{name2}")

    # 4. Dominant roots from tritone
    print("\n4️⃣  DOMINANT FUNCTION: B–F Tritone\n")
    b_f_axis = (11, 5)  # B, F
    roots = dominant_roots_from_tritone(b_f_axis)
    print("   Tritone: B–F")
    print(f"   Dominants: {' and '.join(name_from_pc(r) + '7' for r in roots)}")
    print("   → Classic tritone substitution pair!")

    # 5. Gravity chain
    print("\n5️⃣  GRAVITY CHAIN: Descending in Fourths\n")
    chain = gravity_chain(pc_from_name("G"), steps=7)
    chord_names = [name_from_pc(r) + "7" for r in chain]
    print(f"   {' → '.join(chord_names)}")

    # 6. Markov model
    print("\n6️⃣  MARKOV MODEL: Transition Probabilities\n")
    # Simulate a ii-V-I loop
    progression = ["Dm7", "G7", "Cmaj7"] * 3
    from zone_tritone.corpus import chord_sequence_to_roots

    roots = chord_sequence_to_roots(progression)
    counts = build_transition_counts(roots)
    matrix = normalize_transition_matrix(counts, smoothing=0.1)

    # Show a few transition probabilities
    d, g, c = pc_from_name("D"), pc_from_name("G"), pc_from_name("C")
    print(f"   P(D → G) = {matrix[d][g]:.3f}")
    print(f"   P(G → C) = {matrix[g][c]:.3f}")
    print(f"   P(C → D) = {matrix[c][d]:.3f}")
    print("\n   Classic ii-V-I pattern captured!")

    print("\n" + "=" * 60)
    print("\n✅ Zone-Tritone library demonstration complete!")
    print("\n📚 Import zone_tritone in your Python code to use these functions.")
    print("📖 See tests/ for more detailed usage examples.\n")


if __name__ == "__main__":
    main()
