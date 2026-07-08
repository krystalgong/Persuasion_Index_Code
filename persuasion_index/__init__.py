"""Public API for the Persuasion Index package."""

from importlib.metadata import PackageNotFoundError, version

from .api import (
    build_score_matrices,
    get_persuasion_report,
    get_report,
    score,
    score_batch,
    score_persuasion,
)

try:
    __version__ = version("persuasion-index")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "__version__",
    "build_score_matrices",
    "get_persuasion_report",
    "get_report",
    "score",
    "score_batch",
    "score_persuasion",
]
