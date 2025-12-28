from zone_tritone import pc_from_name, name_from_pc


def test_pc_roundtrip_basic():
    for name, expected in [("C", 0), ("F#", 6), ("Bb", 10), ("E", 4)]:
        pc = pc_from_name(name)
        assert pc == expected
        assert name_from_pc(pc)  # just ensure no crash


def test_enharmonic_equivalents():
    assert pc_from_name("C#") == pc_from_name("Db")
    assert pc_from_name("F#") == pc_from_name("Gb")
    assert pc_from_name("B") == pc_from_name("Cb")
