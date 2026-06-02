import argparse
import json
import re
import string
from pathlib import Path

import pandas as pd


def strip_punctuation(w: str) -> str:
    """Strip leading/trailing punctuation, then normalise internal whitespace.
    Leaves apostrophes inside words intact (e.g. "it's") and hyphens inside
    compound words (e.g. "well-known"), since those are part of the token."""
    # Strip any leading/trailing punctuation characters
    stripped = w.strip(string.punctuation + " ")
    # Collapse any internal runs of whitespace
    return re.sub(r"\s+", " ", stripped)


def load_removed_items(audit_csv: Path) -> set[tuple[str, str]]:
    audit = pd.read_csv(audit_csv)
    if "audit_decision" not in audit.columns:
        return set()

    decisions = pd.to_numeric(audit["audit_decision"], errors="coerce")
    remove_rows = audit[decisions == 2]
    return set(zip(
        remove_rows["category"],
        remove_rows["word_surface"].astype(str).str.lower(),
    ))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rich-lexicon", required=True)
    ap.add_argument("--audit-csv", required=True)  # audit_decision: 1=keep, 2=remove, empty=keep
    ap.add_argument("--raw-lexicons", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    remove = load_removed_items(Path(args.audit_csv))

    with open(args.rich_lexicon, encoding="utf-8") as f:
        lex = json.load(f)
    if args.raw_lexicons:
        with open(args.raw_lexicons, encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = {}

    flat = {}
    for cat, items in lex.items():
        keep = []
        seen_norm = {}  # norm -> canonical surface form (first winner kept)

        for it in items:
            raw_word = it["word"]
            if (cat, raw_word.lower()) in remove:
                continue
            cleaned = strip_punctuation(raw_word)
            if not cleaned:
                continue
            norm = cleaned.lower()
            if norm not in seen_norm:
                seen_norm[norm] = cleaned
                keep.append(cleaned)

        # Union with raw lexicon.
        raw_words = raw.get(cat, [])
        if raw_words and isinstance(raw_words[0], dict):
            raw_words = [r["word"] for r in raw_words]
        for w in raw_words:
            cleaned = strip_punctuation(w)
            if not cleaned:
                continue
            norm = cleaned.lower()
            if norm not in seen_norm:
                seen_norm[norm] = cleaned
                keep.append(cleaned)

        flat[cat] = sorted(keep, key=str.lower)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(flat, f, indent=2, ensure_ascii=False)
    print(f"wrote {args.out}: {sum(len(v) for v in flat.values())} items / {len(flat)} categories")


if __name__ == "__main__":
    main()
