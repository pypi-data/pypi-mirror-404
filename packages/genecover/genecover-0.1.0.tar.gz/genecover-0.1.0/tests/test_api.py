import numpy as np
import pytest

from genecover import GeneCover, Iterative_GeneCover


def test_GeneCover_runs_with_greedy():
    np.random.seed(0)
    d = 15

    # Construct a correlation-like matrix with some structure
    corr = 0.2 * np.ones((d, d))
    np.fill_diagonal(corr, 1.0)
    for k in range(0, d, 5):
        corr[k:k+5, k:k+5] = 0.9

    w = np.ones(d)

    markers = GeneCover(
        num_marker=5,
        corr_mat=corr,
        w=w,
        solver="Greedy",
        output=0,
        m=1,  # avoid post-filter collapsing everything
        lambdaMin=0.05,
        lambdaMax=0.9
    )
    assert isinstance(markers, list)
    assert all(isinstance(i, (int, np.integer)) for i in markers)


def test_Iterative_GeneCover_runs_with_greedy():
    np.random.seed(0)
    d = 20
    corr = 0.2 * np.ones((d, d))
    np.fill_diagonal(corr, 1.0)
    for k in range(0, d, 5):
        corr[k:k+5, k:k+5] = 0.9

    w = np.ones(d)

    out = Iterative_GeneCover(
        incremental_sizes=[3, 3],
        corr_mat=corr,
        w=w,
        solver="Greedy",
        output=0,
        m=1,
        lambdaMin=0.05,
        lambdaMax=0.9
    )
    assert isinstance(out, list)
    assert len(out) == 2
    for lst in out:
        arr = np.asarray(lst)
        assert arr.ndim == 1
        assert np.issubdtype(arr.dtype, np.integer)


def test_GeneCover_gurobi_missing_dependency_raises_importerror():
    d = 5
    corr = np.eye(d)
    w = np.ones(d)

    with pytest.raises(ImportError):
        GeneCover(2, corr, w, solver="Gurobi")


def test_GeneCover_invalid_solver_raises():
    d = 5
    corr = np.eye(d)
    w = np.ones(d)
    with pytest.raises(ValueError):
        GeneCover(2, corr, w, solver="NotASolver")