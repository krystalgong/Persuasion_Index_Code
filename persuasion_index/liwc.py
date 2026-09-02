"""Parsing and validation for locally licensed LIWC-compatible dictionaries."""

from __future__ import annotations

from pathlib import Path


REQUIRED_LIWC_CATEGORIES = (
    "I",
    "You",
    "Anger",
    "Sad",
    "Anx",
    "Posemo",
    "Past",
    "See",
    "Ppron",
)

_CATEGORY_ALIASES = {
    "i": "I",
    "you": "You",
    "anger": "Anger",
    "sad": "Sad",
    "anx": "Anx",
    "posemo": "Posemo",
    "past": "Past",
    "focuspast": "Past",
    "see": "See",
    "ppron": "Ppron",
}


class LiwcParseError(ValueError):
    """Raised when a configured file is not a usable LIWC dictionary."""


def _canonical_category(name: str) -> str:
    stripped = name.strip()
    return _CATEGORY_ALIASES.get(stripped.casefold(), stripped)


def _append_terms(
    dictionary: dict[str, list[str]],
    category: str,
    terms: list[str],
) -> None:
    canonical = _canonical_category(category)
    if not canonical:
        return
    bucket = dictionary.setdefault(canonical, [])
    for term in terms:
        cleaned = term.strip()
        if cleaned and cleaned not in bucket:
            bucket.append(cleaned)


def parse_liwc_file(path: str | Path) -> dict[str, list[str]]:
    """Parse a legacy LIWC ``.dic`` file or PI's compact ``Category: terms`` form.

    The parser only reads a file the user has already obtained. It does not
    download, convert, or redistribute licensed dictionary content.
    """
    resource_path = Path(path)
    try:
        lines = resource_path.read_text(
            encoding="utf-8-sig",
            errors="strict",
        ).splitlines()
    except Exception as exc:
        raise LiwcParseError(f"could not read the configured file: {exc}") from exc

    percent_lines = [i for i, line in enumerate(lines) if line.strip() == "%"]
    dictionary: dict[str, list[str]] = {}

    if len(percent_lines) >= 2:
        category_names: dict[str, str] = {}
        for line in lines[percent_lines[0] + 1 : percent_lines[1]]:
            parts = line.strip().split()
            if len(parts) >= 2:
                category_names[parts[0]] = _canonical_category(parts[1])

        if not category_names:
            raise LiwcParseError("the LIWC category table is empty")

        for line in lines[percent_lines[1] + 1 :]:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            term = parts[0]
            for category_id in parts[1:]:
                category = category_names.get(category_id)
                if category:
                    _append_terms(dictionary, category, [term])
    else:
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or ":" not in stripped:
                continue
            category, raw_terms = stripped.split(":", 1)
            _append_terms(dictionary, category, raw_terms.split())

    dictionary = {
        category: terms
        for category, terms in dictionary.items()
        if terms
    }
    if not dictionary:
        raise LiwcParseError(
            "no LIWC categories with terms could be parsed from the file"
        )
    return dictionary


def missing_required_categories(
    dictionary: dict[str, list[str]],
) -> list[str]:
    """Return PI-used categories that are absent or empty."""
    return [
        category
        for category in REQUIRED_LIWC_CATEGORIES
        if not dictionary.get(category)
    ]
