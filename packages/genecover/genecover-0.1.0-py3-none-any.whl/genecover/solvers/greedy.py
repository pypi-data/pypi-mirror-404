import numpy as np


def greedy_weighted_set_cover(Z, w):
    """
    Greedy heuristic for the weighted set cover problem.

    Args:
        Z (np.ndarray): A binary matrix of shape (n_elements, m_sets), where `Z[i, j] == 1`
            indicates that set `j` covers element `i`.
        w (np.ndarray): A 1D array of length `m_sets` representing the weight of each set.

    Returns:
        List[int]: Indices of the selected sets (column indices of `Z`) that form a cover.
    """
    Z = np.asarray(Z)
    w = np.asarray(w)

    n, m = Z.shape
    # which elements are still uncovered
    uncovered = np.ones(n, dtype=bool)
    # which sets are still available
    available = np.ones(m, dtype=bool)
    selected = []

    while uncovered.any():
        # For each set j: how many of the still-uncovered elements it would cover?
        # Z[uncovered] is an array of shape (#uncovered_elements, m)
        cover_counts = Z[uncovered].sum(axis=0)  # shape (m,)
        # zero out the ones we've already taken
        cover_counts = np.where(available, cover_counts, 0)

        # fast-path: if the best we can do is cover exactly one element per set,
        # grab them all at once and be done
        if cover_counts.max() == Z.shape[0] // Z.shape[1]:
            singletons = np.where((available) & (cover_counts == 1))[0]
            selected.extend(singletons.tolist())
            break

        # otherwise pick the set with max (covered_new_elems / weight)
        nonzero = cover_counts > 0
        if not nonzero.any():
            # nothing left can cover any new element
            break

        ratios = np.zeros(m, dtype=float)
        ratios[nonzero] = cover_counts[nonzero] / w[nonzero]
        best = int(ratios.argmax())
        selected.append(best)

        # mark its covered elements as now covered
        # Z[:, best] is the column for set "best"
        uncovered &= ~Z[:, best].astype(bool)
        # and remove that set from future consideration
        available[best] = False

    return selected