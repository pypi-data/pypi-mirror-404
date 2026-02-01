import numpy as np

from genecover.solvers.greedy import greedy_weighted_set_cover


def test_greedy_weighted_set_cover_toy():
    # element 0 covered by set 0
    # element 1 covered by set 0 and 1
    Z = np.array([[1, 0],
                  [1, 1]])
    w = np.array([1.0, 2.0])

    sol = greedy_weighted_set_cover(Z, w)
    assert sol == [0]


def test_greedy_returns_list_of_ints():
    Z = np.array([[1, 0, 0],
                  [0, 1, 1],
                  [1, 0, 1]])
    w = np.array([1.0, 1.0, 1.0])

    sol = greedy_weighted_set_cover(Z, w)
    assert isinstance(sol, list)
    assert all(isinstance(i, (int, np.integer)) for i in sol)


def test_greedy_handles_uncoverable_elements():
    Z = np.array([[0, 0],
                  [1, 0]])
    w = np.array([1.0, 1.0])
    sol = greedy_weighted_set_cover(Z, w)
    assert isinstance(sol, list)
    assert 1 not in sol