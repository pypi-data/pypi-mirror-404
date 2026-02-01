import numpy as np
import pytest

from genecover import gene_gene_correlation


def test_gene_gene_correlation_pearson_shape():
    X = np.random.randn(10, 5)
    C = gene_gene_correlation(X, method="pearson")
    assert C.shape == (5, 5)


def test_gene_gene_correlation_spearman_shape_and_diag():
    X = np.random.randn(10, 5)
    C = gene_gene_correlation(X, method="spearman")
    assert C.shape == (5, 5)
    assert np.allclose(np.diag(C), 1.0)


def test_gene_gene_correlation_batch_list_stacks_vertically():
    X = [np.random.randn(10, 5), np.random.randn(12, 5)]
    C = gene_gene_correlation(X, method="pearson")
    assert C.shape == (10, 5)  # 2 batches * d rows, d cols


def test_gene_gene_correlation_invalid_method_raises():
    X = np.random.randn(10, 5)
    with pytest.raises(ValueError):
        gene_gene_correlation(X, method="abcde")