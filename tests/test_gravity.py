from zone_tritone import dominant_roots_from_tritone, gravity_chain


def test_dominant_roots_from_tritone():
    # B–F axis should correspond to G7 and Db7
    roots = dominant_roots_from_tritone((5, 11))  # F, B
    # Order not strictly guaranteed, so check membership
    for r in roots:
        assert r in (7, 1)  # G or Db
    assert len(roots) == 2


def test_gravity_chain_fourths():
    # Starting on G (7), descending 4ths should go:
    # G -> C -> F -> Bb
    chain = gravity_chain(7, steps=3)
    assert chain == [7, 0, 5, 10]


def test_gravity_chain_complete_cycle():
    # Full cycle should return to start after 12 steps
    chain = gravity_chain(0, steps=12)
    assert chain[0] == 0
    assert chain[-1] == 0
    assert len(chain) == 13  # 0 + 12 steps
