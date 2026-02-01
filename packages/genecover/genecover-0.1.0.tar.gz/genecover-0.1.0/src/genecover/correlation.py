import numpy as np

def gene_gene_correlation(X, method: str = "spearman") -> np.ndarray:
    """
    Compute a (possibly batch-stacked) gene-gene correlation matrix from X.

    Parameters
    ----------
    X : np.ndarray or list of np.ndarray
        - If np.ndarray: expression matrix of shape (N, d),
          where N is the number of cells/spots and d is the number of genes.
        - If list of np.ndarray: each element is (N_b, d) with the same d.
          For each batch, a (d, d) correlation matrix is computed and the
          resulting matrices are stacked vertically, yielding shape
          (b * d, d) where b = number of batches.
    method : {"spearman", "pearson"}, default="spearman"
        Correlation method.

    Returns
    -------
    np.ndarray
        If X is a single array of shape (N, d): a (d, d) correlation matrix.
        If X is a list of b arrays of shape (N_b, d): a stacked matrix of
        shape (b * d, d), where each block of d rows corresponds to one batch.
    """
    if isinstance(X, list):
        if len(X) == 0:
            raise ValueError("X is an empty list; cannot compute correlations.")

        corr_mat_list = []
        for x in X:
            x = np.asarray(x)
            if x.ndim != 2:
                raise ValueError("Each batch x in X must be a 2D array.")

            if method == "spearman":
                from scipy.stats import spearmanr  # lazy import
                corr_mat, _ = spearmanr(x)
            elif method == "pearson":
                corr_mat = np.corrcoef(x.T)
            else:
                raise ValueError("method must be 'spearman' or 'pearson'.")

            corr_mat_list.append(np.asarray(corr_mat))

        corr_mat = np.vstack(corr_mat_list)

    else:
        X = np.asarray(X)
        if X.ndim != 2:
            raise ValueError("X must be a 2D array or a list of 2D arrays.")

        if method == "spearman":
            from scipy.stats import spearmanr  # lazy import
            corr_mat, _ = spearmanr(X)
        elif method == "pearson":
            corr_mat = np.corrcoef(X.T)
        else:
            raise ValueError("method must be 'spearman' or 'pearson'.")

    return np.asarray(corr_mat)