"""Command-line interface for scoring one argument."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from . import __version__
from .api import get_report, score


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="persuasion-index",
        description="Compute interpretable Persuasion Index features for one English argument.",
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Argument text. If omitted, text is read from standard input.",
    )
    parser.add_argument(
        "--lexicon",
        choices=("expanded", "seeded"),
        default="expanded",
        help="Lexicon set to use (default: expanded).",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Include the UKP-weighted empirical profile.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON instead of indented JSON.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _read_text(parts: Sequence[str], parser: argparse.ArgumentParser) -> str:
    if parts:
        return " ".join(parts).strip()
    if sys.stdin.isatty():
        parser.error("provide argument text or pipe text through standard input")
    return sys.stdin.read().strip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    text = _read_text(args.text, parser)
    if not text:
        parser.error("argument text cannot be empty")

    if args.profile:
        raw, weighted = get_report(text, lexicon=args.lexicon)
        result = {"scores": raw, "weighted_profile": weighted}
    else:
        result = score(text, lexicon=args.lexicon)

    indent = None if args.compact else 2
    print(json.dumps(result, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
