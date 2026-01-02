from shared.zone_tritone import all_tritone_axes, is_tritone_pair, tritone_axis, tritone_partner


def test_tritone_partner_basic():
    assert tritone_partner(0) == 6   # C -> F#
    assert tritone_partner(11) == 5  # B -> F


def test_tritone_pair_and_axes():
    axes = all_tritone_axes()
    assert len(axes) == 6
    assert (0, 6) in axes
    assert (5, 11) in axes

    assert is_tritone_pair(0, 6)
    assert is_tritone_pair(11, 5)


def test_tritone_axis_sorting():
    # Should always return sorted pair
    assert tritone_axis(0) == (0, 6)
    assert tritone_axis(6) == (0, 6)
    assert tritone_axis(5) == (5, 11)
    assert tritone_axis(11) == (5, 11)
