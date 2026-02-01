import numpy as np


def covering_scip(Z, minSize=1, weights=1.0, timeLimit=None, output=1):
    """
    Solves the minimal weight set covering problem using the SCIP solver.

    Args:
        Z (np.ndarray): A binary matrix of shape (N, d), where Z[i, j] == 1 indicates that set j covers element i.
        minSize (int, optional): Minimum number of sets required to cover each element. Defaults to 1.
        weights (str|float|Sequence[float], optional): Weights for each set.
            - If 'prob', uses 1 - 0.01 * mean coverage per column.
            - If scalar, uses the same weight for all sets.
            - Otherwise, an array of length d giving each set’s weight.
            Defaults to 1.0.
        timeLimit (float, optional): Time limit in seconds for the SCIP solver. Defaults to None (no limit).
        output (int, optional): 1 to enable solver output, 0 to suppress it. Defaults to 1.

    Returns:
        List[int]: List of selected set indices (column indices of Z).

    """
    try:
        from pyscipopt import Model, quicksum
    except ImportError as e:
        raise ImportError(
            "covering_scip requires pyscipopt. Install with: pip install 'genecover[scip]'"
        ) from e

    Z = np.asarray(Z)
    N, d = Z.shape

    # Prepare weight array
    if isinstance(weights, str) and weights == 'prob':
        w = 1 - 0.01 * np.mean(Z, axis=0)
    elif np.isscalar(weights):
        w = weights * np.ones(d, dtype=float)
    else:
        w = np.asarray(weights, dtype=float)

    # Precompute non‐zero columns per row and check coverage feasibility
    cover_indices = [np.flatnonzero(Z[i]) for i in range(N)]
    for i, cols in enumerate(cover_indices):
        if cols.size == 0:
            raise ValueError(f"Element {i} has no covering sets → problem infeasible")

    # Build SCIP model
    model = Model("SetCover_simple")
    if timeLimit is not None:
        model.setParam("limits/time", timeLimit)
    if output == 0:
        model.hideOutput()

    # Variables: x[j]=1 if set j is selected
    x = [model.addVar(vtype="B", name=f"x_{j}") for j in range(d)]

    # Objective: minimize total weight
    model.setObjective(quicksum(w[j] * x[j] for j in range(d)), "minimize")

    # Cover each element i with at least minSize selected sets
    for i, cols in enumerate(cover_indices):
        model.addCons(
            quicksum(x[j] for j in cols) >= minSize,
            name=f"cover_i{i}"
        )

    # Solve
    model.optimize()

    # Extract solution
    selected = [j for j in range(d) if model.getVal(x[j]) > 0.5]
    return selected