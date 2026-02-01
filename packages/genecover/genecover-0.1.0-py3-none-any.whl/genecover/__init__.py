import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

# Public API (lightweight imports only)
from .api import GeneCover, Iterative_GeneCover  # noqa: E402
from .correlation import gene_gene_correlation  # noqa: E402

__all__ = [
    "GeneCover",
    "Iterative_GeneCover",
    "gene_gene_correlation",
    "__version__",
]