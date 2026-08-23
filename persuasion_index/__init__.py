"""Public analysis functions for the Persuasion Index package."""

from .api import (
    build_score_matrices,
    get_persuasion_report,
    get_report,
    score,
    score_batch,
    score_persuasion,
)
from ._version import __version__
from .resources import (
    ResourceUnavailableError,
    check_resources,
    missing_resources,
    require_resources,
)

__all__ = [
    "__version__",
    "ResourceUnavailableError",
    "build_score_matrices",
    "get_persuasion_report",
    "get_report",
    "score",
    "score_batch",
    "score_persuasion",
    "check_resources",
    "missing_resources",
    "require_resources",
]
