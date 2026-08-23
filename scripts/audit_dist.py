"""Fail when distribution archives contain local or restricted resources."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


FORBIDDEN_FRAGMENTS = (
    "en_liwc",
    "nrc-vad-lexicon",
    "brysbaert_concretness",
    "multiwordexpression_concreteness",
)
FORBIDDEN_PARTS = {".env", ".ds_store", "__pycache__"}


def archive_members(path: Path) -> list[str]:
    if path.name.endswith(".whl"):
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            return archive.getnames()
    raise ValueError(f"Unsupported distribution archive: {path}")


def audit(path: Path) -> None:
    blocked: list[str] = []
    unsafe: list[str] = []

    for member in archive_members(path):
        normalized = member.replace("\\", "/")
        pure_path = PurePosixPath(normalized)
        lowered = normalized.lower()
        lowered_parts = {part.lower() for part in pure_path.parts}

        if pure_path.is_absolute() or ".." in pure_path.parts:
            unsafe.append(member)
        if any(fragment in lowered for fragment in FORBIDDEN_FRAGMENTS):
            blocked.append(member)
        if lowered_parts & FORBIDDEN_PARTS or lowered.endswith((".pyc", ".pyo")):
            blocked.append(member)

    if unsafe:
        raise RuntimeError(f"Unsafe archive paths in {path.name}: {unsafe}")
    if blocked:
        raise RuntimeError(f"Restricted or local files in {path.name}: {blocked}")

    print(f"Audited {path.name}")


def main(arguments: list[str]) -> int:
    if not arguments:
        print("usage: audit_dist.py DIST [DIST ...]", file=sys.stderr)
        return 2

    for argument in arguments:
        path = Path(argument)
        if not path.is_file():
            raise FileNotFoundError(path)
        audit(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
