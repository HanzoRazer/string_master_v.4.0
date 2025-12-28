from zone_tritone import build_transition_counts, normalize_transition_matrix, sample_next_root


def test_markov_counts_and_normalization():
    # Simple loop: G7 -> C7 -> F7 -> G7 ...
    # Roots: G(7), C(0), F(5), G(7)
    roots = [7, 0, 5, 7]
    counts = build_transition_counts(roots)
    assert counts[7][0] == 1
    assert counts[0][5] == 1
    assert counts[5][7] == 1

    matrix = normalize_transition_matrix(counts, smoothing=0.0)
    # Rows with transitions should sum to 1.0
    for i in (7, 0, 5):
        assert abs(sum(matrix[i]) - 1.0) < 1e-9

    # Sampling shouldn't crash
    current = 7
    next_root = sample_next_root(current, matrix)
    assert 0 <= next_root <= 11


def test_markov_smoothing():
    # Empty sequence should produce uniform distribution with smoothing
    roots = [0, 0]  # Only self-transitions on C
    counts = build_transition_counts(roots)
    
    matrix = normalize_transition_matrix(counts, smoothing=1.0)
    # With smoothing, all probabilities should be > 0
    for i in range(12):
        for j in range(12):
            assert matrix[i][j] > 0
