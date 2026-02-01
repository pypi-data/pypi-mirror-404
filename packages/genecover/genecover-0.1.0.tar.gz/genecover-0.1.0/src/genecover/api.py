import numpy as np

from .solvers.greedy import greedy_weighted_set_cover # lazy imports for other algorithms


def GeneCover(
    num_marker,
    corr_mat,
    w,
    m=3,
    interval=0,
    lambdaMax=0.3,
    lambdaMin=0.05,
    timeLimit=600,
    output=0,
    solver="Gurobi",
):
    """
    Selects marker genes based on gene-gene correlation using combinatorial optimization or a greedy heuristic.

    Args:
        num_marker (int): Desired number of markers to select.
        corr_mat (np.ndarray): Gene-gene correlation matrix.
        interval (int): Allowed deviation from `num_marker`. The final number of markers may vary within this range.
        w (np.ndarray): An array of weights for the genes. Higher weights indicate higher cost for selection.
        lambdaMax (float): Maximum threshold for acceptable gene-gene correlation.
        lambdaMin (float): Minimum threshold for acceptable gene-gene correlation.
        timeLimit (float): Time limit (in seconds) for the optimization.
        ouput (int): Whether to print the optimization process. Set to 1 to enable.
        solver (str): The solver to use for the optimization. Options are "Gurobi", "SCIP", and "Greedy".
        greedy (bool): Whether to use a greedy algorithm for set cover instead of the Gurobi solver. Default: False.

    Returns:
        List[int]: Indices of the selected marker genes.
    """
    corr_mat = np.asarray(corr_mat)
    w = np.asarray(w)

    epsilon = (lambdaMax + lambdaMin) / 2
    best_marker_length_gap = 1e6
    selection = np.arange(corr_mat.shape[1])
    G_v3 = corr_mat > epsilon

    if solver == "Gurobi":
        from .solvers.gurobi import covering

        cov_sol = covering(G_v3, minSize=1, alpha=0.0, weights=w, timeLimit=timeLimit, output=output)
        cov_sol = selection[np.array(cov_sol.x)[: len(selection)] > 0.5]
    elif solver == "Greedy":
        cov_sol = greedy_weighted_set_cover(G_v3, w)
    elif solver == "SCIP":
        from .solvers.scip import covering_scip

        cov_sol = covering_scip(G_v3, minSize=1, weights=w, timeLimit=timeLimit, output=output)
    else:
        raise ValueError("Invalid solver specified. Choose from 'Gurobi', 'SCIP', or 'Greedy'.")

    markers = []
    num_batches = G_v3.shape[0] // G_v3.shape[1]
    num_genes = G_v3.shape[1]

    for i in cov_sol:
        if num_batches > 1:
            if G_v3[[i + j * num_genes for j in range(num_batches)]].sum(axis=1).min() >= m:
                markers.append(i)
        else:
            if G_v3[i].sum() >= m:
                markers.append(i)

    n_markers = len(markers)
    current_gap = abs(n_markers - num_marker)
    best_marker_length_gap = current_gap
    best_epsilon = epsilon

    while (lambdaMax - lambdaMin) > 1e-6 and (n_markers < num_marker or n_markers > num_marker + interval):
        if n_markers < num_marker:
            lambdaMax = epsilon
        else:
            lambdaMin = epsilon

        epsilon = (lambdaMin + lambdaMax) / 2
        G_v3 = corr_mat > epsilon

        if solver == "Gurobi":
            from .solvers.gurobi import covering

            cov_sol = covering(G_v3, minSize=1, alpha=0.0, weights=w, timeLimit=timeLimit, output=output)
            cov_sol = selection[np.array(cov_sol.x)[: len(selection)] > 0.5]
        elif solver == "Greedy":
            cov_sol = greedy_weighted_set_cover(G_v3, w)
        elif solver == "SCIP":
            from .solvers.scip import covering_scip

            cov_sol = covering_scip(G_v3, minSize=1, weights=w, timeLimit=timeLimit, output=output)
        else:
            raise ValueError("Invalid solver specified. Choose from 'Gurobi', 'SCIP', or 'Greedy'.")

        markers = []
        for i in cov_sol:
            if num_batches > 1:
                if G_v3[[i + j * num_genes for j in range(num_batches)]].sum(axis=1).min() >= m:
                    markers.append(i)
            else:
                if G_v3[i].sum() >= m:
                    markers.append(i)
            n_markers = len(markers)

        current_gap = abs(n_markers - num_marker)
        if current_gap < best_marker_length_gap:
            best_marker_length_gap = current_gap
            best_epsilon = epsilon
            best_lambdaMin = lambdaMin
            best_lambdaMax = lambdaMax
            best_direction = n_markers < num_marker

    print("Best Gap: ", best_marker_length_gap)
    print("Best Epsilon: ", best_epsilon)
    return markers


def Iterative_GeneCover(
    incremental_sizes,
    corr_mat,
    w,
    m=3,
    lambdaMin=0.05,
    lambdaMax=0.3,
    timeLimit=600,
    output=0,
    solver="Gurobi",
):
    """
    Performs iterative marker gene selection using the GeneCover algorithm.

    Args:
        corr_mat (np.ndarray): Gene-gene correlation matrix of shape (d, d).
        incremental_sizes (List[int]): A list indicating the number of markers to select at each iteration.
        w (np.ndarray): An array of weights for each gene. Higher weights indicate higher cost for selection.
        lambdaMax (float): Maximum threshold for gene-gene correlation.
        lambdaMin (float): Minimum threshold for gene-gene correlation.
        timeLimit (float): Time limit (in seconds) for the optimization.
        output (int): Whether to print the optimization process. Set to 1 to enable.
        solver (str): The solver to use for the optimization. Options are "Gurobi", "SCIP", and "Greedy".
    Returns:
        List[List[int]]: A list where each element is a list of indices of the selected marker genes at the corresponding iteration.
    """
    corr_mat = np.asarray(corr_mat)
    w = np.asarray(w)

    num_batches = corr_mat.shape[0] // corr_mat.shape[1]
    num_genes = corr_mat.shape[1]
    MARKERS = []

    print("Iteration 1")
    markers = GeneCover(
        incremental_sizes[0],
        corr_mat,
        w=w,
        m=m,
        lambdaMax=lambdaMax,
        lambdaMin=lambdaMin,
        timeLimit=timeLimit,
        output=output,
        solver=solver,
    )

    selection = np.arange(corr_mat.shape[1])
    MARKERS.append(markers)
    remaining_genes_idx_abs = np.setdiff1d(selection, markers)

    for t, size in enumerate(incremental_sizes[1:]):
        print("Iteration ", t + 2)
        remaining_genes_idx_abs_batches = np.array(
            [remaining_genes_idx_abs + j * num_genes for j in range(num_batches)]
        ).flatten()

        corr_mat_remain = corr_mat[remaining_genes_idx_abs_batches][:, remaining_genes_idx_abs]
        markers = GeneCover(
            size,
            corr_mat_remain,
            w=w[remaining_genes_idx_abs],
            m=m,
            lambdaMin=lambdaMin,
            lambdaMax=lambdaMax,
            timeLimit=timeLimit,
            output=output,
            solver=solver,
        )

        MARKERS.append(remaining_genes_idx_abs[markers])
        remaining_genes_idx_abs = np.setdiff1d(remaining_genes_idx_abs, [j for i in MARKERS for j in i])

    return MARKERS