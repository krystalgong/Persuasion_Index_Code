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
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from PI_score_generator import (
    _select_lexicon_for_context,
    _selected_lexicon_path,
    _using_lexicon,
    get_helper_dir,
    score_all,
)

LexiconChoice = Literal["expanded", "seeded"]
OutputChoice = Literal["auto", "raw", "matrices", "both"]


def _use_expanded_from_choice(
    lexicon: LexiconChoice | bool | None = None,
    use_expanded_lexicons: bool | None = None,
) -> bool:
    if use_expanded_lexicons is not None:
        return bool(use_expanded_lexicons)

    if isinstance(lexicon, bool):
        return lexicon

    if lexicon is None:
        return True

    normalized = lexicon.strip().lower()
    if normalized in {"expanded", "expand", "llm", "audited"}:
        return True
    if normalized in {"seeded", "seed", "original", "base"}:
        return False

    raise ValueError("lexicon must be 'expanded' or 'seeded'")


def _bundled_lexicon_path(use_expanded_lexicons: bool) -> Path:
    filename = (
        "lexicons_expanded_LLM_audited.json"
        if use_expanded_lexicons
        else "lexicons.json"
    )
    return (get_helper_dir() / filename).resolve()


def _resolve_scoring_lexicon(
    *,
    lexicon: LexiconChoice | bool | None = None,
    lexicon_file: str | Path | None = None,
    use_expanded_lexicons: bool | None = None,
) -> Path:
    """Resolve one immutable lexicon choice for a scoring operation."""
    if lexicon_file is not None:
        if lexicon is not None or use_expanded_lexicons is not None:
            raise ValueError(
                "lexicon_file cannot be combined with lexicon or "
                "use_expanded_lexicons"
            )
        return _selected_lexicon_path(lexicon_file)

    if use_expanded_lexicons is not None or lexicon is not None:
        return _bundled_lexicon_path(
            _use_expanded_from_choice(lexicon, use_expanded_lexicons)
        )

    configured = os.environ.get("PI_LEXICON_FILE", "").strip()
    if configured:
        return _selected_lexicon_path(configured)

    return _bundled_lexicon_path(True)


def run_expanded_lexicons(
    use_expanded_lexicons: bool = True,
) -> str:
    """
    Select the expanded or seeded lexicon in the current thread/task context.

    Returns the lexicon path that was selected.
    """
    filename = _bundled_lexicon_path(use_expanded_lexicons)
    return _select_lexicon_for_context(filename)


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
    use_expanded_lexicons: bool | None = None,
    *,
    lexicon: LexiconChoice | bool | None = None,
    lexicon_file: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run `score_all` and return two DataFrames:
    1. sub-feature scores, such as `Sentiment.anger`
    2. category mean scores, such as `Sentiment.mean`

    `data` can be a single text string, a sequence of text strings, or a
    DataFrame containing `text_col`.
    """
    selected_lexicon = _resolve_scoring_lexicon(
        lexicon=lexicon,
        lexicon_file=lexicon_file,
        use_expanded_lexicons=use_expanded_lexicons,
    )
    df, _ = _as_text_frame(data, text_col=text_col)

    rows_sub = []
    rows_mean = []
    with _using_lexicon(selected_lexicon):
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
    lexicon: LexiconChoice | bool | None = None,
    output: OutputChoice = "auto",
    use_expanded_lexicons: bool | None = None,
    lexicon_file: str | Path | None = None,
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
    selected_lexicon = _resolve_scoring_lexicon(
        lexicon=lexicon,
        lexicon_file=lexicon_file,
        use_expanded_lexicons=use_expanded_lexicons,
    )

    df, is_single_text = _as_text_frame(data, text_col=text_col)

    with _using_lexicon(selected_lexicon):
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
