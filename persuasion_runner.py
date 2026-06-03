"""
Convenience entry points for running Persuasion Index scores.

Use `score_persuasion` for the simple API:
    score_persuasion("single argument text")
    score_persuasion(df, text_col="argument")

The expanded lexicon is used by default. Pass `lexicon="seeded"` to use the
original seed lexicon.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any, Literal

import pandas as pd

from PI_score_generator import _PATTERN_CACHE, _load_lexicons, get_helper_dir, score_all

LexiconChoice = Literal["expanded", "seeded"]
OutputChoice = Literal["auto", "raw", "matrices", "both"]


def _use_expanded_from_choice(
    lexicon: LexiconChoice | bool = "expanded",
    use_expanded_lexicons: bool | None = None,
) -> bool:
    if use_expanded_lexicons is not None:
        return bool(use_expanded_lexicons)

    if isinstance(lexicon, bool):
        return lexicon

    normalized = lexicon.strip().lower()
    if normalized in {"expanded", "expand", "llm", "audited"}:
        return True
    if normalized in {"seeded", "seed", "original", "base"}:
        return False

    raise ValueError("lexicon must be 'expanded' or 'seeded'")


def run_expanded_lexicons(
    use_expanded_lexicons: bool = True,
) -> str:
    """
    Select the expanded or seeded lexicon file and clear scorer caches.

    Returns the lexicon path that was selected.
    """
    helper_dir = get_helper_dir()
    filename = (
        helper_dir / "lexicons_expanded_LLM_audited.json"
        if use_expanded_lexicons
        else helper_dir / "lexicons.json"
    )
    os.environ["PI_LEXICON_FILE"] = str(filename)
    _load_lexicons.cache_clear()
    _PATTERN_CACHE.clear()
    return str(filename)


def _as_text_frame(
    data: str | Sequence[str] | pd.DataFrame,
    text_col: str,
) -> tuple[pd.DataFrame, bool]:
    """
    Normalize supported inputs to a DataFrame.

    Returns `(df, is_single_text)`.
    """
    if isinstance(data, pd.DataFrame):
        if text_col not in data.columns:
            raise ValueError(f"text_col '{text_col}' is not in the DataFrame")
        return data, False

    if isinstance(data, str):
        return pd.DataFrame({text_col: [data]}), True

    if isinstance(data, Sequence):
        return pd.DataFrame({text_col: list(data)}), False

    raise TypeError("data must be a string, a sequence of strings, or a pandas DataFrame")


def _flatten_scores(scores: dict[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    flat_sub: dict[str, float] = {}
    flat_mean: dict[str, float] = {}

    for cat, vals in scores.items():
        if isinstance(vals, dict):
            for subk, value in vals.items():
                key = f"{cat}.{subk}"
                if subk == "mean":
                    flat_mean[key] = value
                else:
                    flat_sub[key] = value
        elif cat == "Overall_mean":
            flat_mean["Overall_mean"] = vals

    return flat_sub, flat_mean


def build_score_matrices(
    data: str | Sequence[str] | pd.DataFrame,
    text_col: str = "argument",
    use_expanded_lexicons: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run `score_all` and return two DataFrames:
    1. sub-feature scores, such as `Sentiment.anger`
    2. category mean scores, such as `Sentiment.mean`

    `data` can be a single text string, a sequence of text strings, or a
    DataFrame containing `text_col`.
    """
    run_expanded_lexicons(use_expanded_lexicons)
    df, _ = _as_text_frame(data, text_col=text_col)

    rows_sub = []
    rows_mean = []
    for text in df[text_col].fillna(""):
        scores = score_all(str(text))
        flat_sub, flat_mean = _flatten_scores(scores)
        rows_sub.append(flat_sub)
        rows_mean.append(flat_mean)

    df_subfeatures = (
        pd.DataFrame(rows_sub, index=df.index)
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
    )
    df_means = (
        pd.DataFrame(rows_mean, index=df.index)
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
    )

    return df_subfeatures, df_means


def score_persuasion(
    data: str | Sequence[str] | pd.DataFrame,
    text_col: str = "argument",
    lexicon: LexiconChoice | bool = "expanded",
    output: OutputChoice = "auto",
    use_expanded_lexicons: bool | None = None,
) -> Any:
    """
    Overall convenience function for single texts and DataFrames.

    Defaults:
    - expanded lexicon
    - single text -> raw nested `score_all` dict
    - DataFrame/list -> `(df_subfeatures, df_means)`

    Options:
    - `lexicon="seeded"` uses the original seed lexicons
    - `output="matrices"` always returns `(df_subfeatures, df_means)`
    - `output="both"` returns raw scores plus matrices
    """
    use_expanded = _use_expanded_from_choice(
        lexicon=lexicon,
        use_expanded_lexicons=use_expanded_lexicons,
    )
    run_expanded_lexicons(use_expanded)

    df, is_single_text = _as_text_frame(data, text_col=text_col)

    raw_scores = [score_all(str(text)) for text in df[text_col].fillna("")]

    if output == "raw":
        return raw_scores[0] if is_single_text else raw_scores

    rows_sub = []
    rows_mean = []
    for scores in raw_scores:
        flat_sub, flat_mean = _flatten_scores(scores)
        rows_sub.append(flat_sub)
        rows_mean.append(flat_mean)
    df_subfeatures = (
        pd.DataFrame(rows_sub, index=df.index)
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
    )
    df_means = (
        pd.DataFrame(rows_mean, index=df.index)
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
    )

    if output == "matrices" or (output == "auto" and not is_single_text):
        return df_subfeatures, df_means

    if output == "auto":
        return raw_scores[0]

    if output == "both":
        raw_out = raw_scores[0] if is_single_text else raw_scores
        return raw_out, df_subfeatures, df_means

    raise ValueError("output must be 'auto', 'raw', 'matrices', or 'both'")
