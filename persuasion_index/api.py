"""Stable, user-facing entry points for Persuasion Index scoring."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

import pandas as pd

from persuasion_profile import get_persuasion_report
from persuasion_runner import build_score_matrices, score_persuasion
from .resources import require_resources

LexiconChoice = Literal["expanded", "seeded"]
OutputChoice = Literal["auto", "raw", "matrices", "both"]


def score(
    data: str | Sequence[str] | pd.DataFrame,
    *,
    text_col: str = "argument",
    lexicon: LexiconChoice = "expanded",
    output: OutputChoice = "auto",
    strict_resources: bool = False,
) -> Any:
    """Score one text, a sequence of texts, or a pandas DataFrame.

    A single string returns the nested 15-dimension score dictionary by
    default. Sequences and DataFrames return subfeature and dimension-score
    matrices. Set ``output`` explicitly to select another supported format.
    """
    if strict_resources:
        require_resources()
    return score_persuasion(
        data,
        text_col=text_col,
        lexicon=lexicon,
        output=output,
    )


def score_batch(
    data: Sequence[str] | pd.DataFrame,
    *,
    text_col: str = "argument",
    lexicon: LexiconChoice = "expanded",
    strict_resources: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return 55-subfeature and 15-dimension matrices for multiple texts."""
    if strict_resources:
        require_resources()
    use_expanded = lexicon == "expanded"
    if lexicon not in {"expanded", "seeded"}:
        raise ValueError("lexicon must be 'expanded' or 'seeded'")
    return build_score_matrices(
        data,
        text_col=text_col,
        use_expanded_lexicons=use_expanded,
    )


def get_report(
    text: str,
    *,
    lexicon: LexiconChoice = "expanded",
    strict_resources: bool = False,
) -> tuple[dict, dict | None]:
    """Return raw PI features and the optional UKP-weighted profile."""
    if strict_resources:
        require_resources()
    if lexicon not in {"expanded", "seeded"}:
        raise ValueError("lexicon must be 'expanded' or 'seeded'")
    return get_persuasion_report(
        text,
        use_expanded_lexicons=lexicon == "expanded",
    )
