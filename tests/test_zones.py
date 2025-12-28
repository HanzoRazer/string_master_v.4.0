from zone_tritone import zone, is_same_zone, is_zone_cross, is_whole_step, is_half_step


def test_zone_parity():
    assert zone(0) == 0
    assert zone(2) == 0
    assert zone(1) == 1
    assert zone(5) == 1


def test_zone_crossing():
    # C (0) -> C# (1) = half-step, zone-cross
    assert is_half_step(0, 1)
    assert is_zone_cross(0, 1)
    # C (0) -> D (2) = whole-step, same zone
    assert is_whole_step(0, 2)
    assert is_same_zone(0, 2)


def test_zone_stability():
    # All even pcs should be in same zone
    assert is_same_zone(0, 2)
    assert is_same_zone(2, 4)
    assert is_same_zone(4, 6)
    # All odd pcs should be in same zone
    assert is_same_zone(1, 3)
    assert is_same_zone(3, 5)
