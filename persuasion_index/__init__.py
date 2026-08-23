"""Public analysis functions for the Persuasion Index package.

The public API is imported lazily so lightweight commands such as
``persuasion-index --version`` do not have to import pandas and the scorer.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from ._version import __version__


_API_EXPORTS = {
    "build_score_matrices",
    "get_persuasion_report",
    "get_report",
    "score",
    "score_batch",
    "score_persuasion",
}
_RESOURCE_EXPORTS = {
    "ResourceUnavailableError",
    "check_resources",
    "missing_resources",
    "require_resources",
}

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


def __getattr__(name: str) -> Any:
    """Load public functions only when they are first requested."""
    if name in _API_EXPORTS:
        value = getattr(import_module(".api", __name__), name)
    elif name in _RESOURCE_EXPORTS:
        value = getattr(import_module(".resources", __name__), name)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
