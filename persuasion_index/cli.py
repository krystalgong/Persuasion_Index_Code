"""Command-line interface for scoring one argument."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from ._version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="persuasion-index",
        description="Compute interpretable Persuasion Index features for one English argument.",
    )
    parser.add_argument(
        "--strict-resources",
        action="store_true",
        help="Require all optional resources used by the full feature set.",
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


def build_doctor_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="persuasion-index doctor",
        description="Check optional resources without downloading licensed data.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write machine-readable JSON.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 unless every optional resource is available.",
    )
    return parser


def _doctor_main(argv: Sequence[str]) -> int:
    from .resources import check_resources

    parser = build_doctor_parser()
    args = parser.parse_args(argv)
    statuses = check_resources()
    missing = [name for name, status in statuses.items() if not status["available"]]

    if args.json:
        result = {
            "complete": not missing,
            "missing": missing,
            "resources": statuses,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Persuasion Index resource check")
        for name, status in statuses.items():
            marker = "OK" if status["available"] else "MISSING"
            print(f"[{marker}] {name}: {status['detail']}")
            if not status["available"]:
                print(f"  Features: {', '.join(status['features'])}")
                print(f"  Source: {status['source_url']}")
                print(f"  License: {status['license_note']}")
        print(
            "Optional feature resources:",
            "complete" if not missing else "incomplete",
        )

    return 1 if args.strict and missing else 0


def _read_text(parts: Sequence[str], parser: argparse.ArgumentParser) -> str:
    if parts:
        return " ".join(parts).strip()
    if sys.stdin.isatty():
        parser.error("provide argument text or pipe text through standard input")
    return sys.stdin.read().strip()


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["doctor"]:
        return _doctor_main(argv[1:])

    parser = build_parser()
    args = parser.parse_args(argv)
    text = _read_text(args.text, parser)
    if not text:
        parser.error("argument text cannot be empty")

    if args.profile:
        from .api import get_report

        raw, weighted = get_report(
            text,
            lexicon=args.lexicon,
            strict_resources=args.strict_resources,
        )
        result = {"scores": raw, "weighted_profile": weighted}
    else:
        from .api import score

        result = score(
            text,
            lexicon=args.lexicon,
            strict_resources=args.strict_resources,
        )

    indent = None if args.compact else 2
    print(json.dumps(result, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
