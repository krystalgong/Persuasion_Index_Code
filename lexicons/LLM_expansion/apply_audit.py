import argparse, json, re, string
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--rich-lexicon', required=True)
ap.add_argument('--audit-csv', required=True)  # audit_decision: 1=keep, 2=remove, empty=keep
ap.add_argument('--raw-lexicons', default=None)
ap.add_argument('--out', required=True)
args = ap.parse_args()


def strip_punctuation(w: str) -> str:
    """Strip leading/trailing punctuation, then normalise internal whitespace.
    Leaves apostrophes inside words intact (e.g. "it's") and hyphens inside
    compound words (e.g. "well-known"), since those are part of the token."""
    # Strip any leading/trailing punctuation characters
    stripped = w.strip(string.punctuation + " ")
    # Collapse any internal runs of whitespace
    return re.sub(r"\s+", " ", stripped)


audit = pd.read_csv(args.audit_csv)
# Only rows explicitly marked 2 are removed; empty or 1 = keep
remove = set(zip(
    audit[audit.audit_decision == 2]['category'],
    audit[audit.audit_decision == 2]['word_surface'].str.lower(),
))

lex = json.load(open(args.rich_lexicon))
raw = json.load(open(args.raw_lexicons)) if args.raw_lexicons else {}

flat = {}
for cat, items in lex.items():
    keep = []
    seen_norm = {}  # norm -> canonical surface form (first winner kept)

    for it in items:
        raw_word = it['word']
        if (cat, raw_word.lower()) in remove:
            continue
        cleaned = strip_punctuation(raw_word)
        if not cleaned:
            continue
        norm = cleaned.lower()
        if norm not in seen_norm:
            seen_norm[norm] = cleaned
            keep.append(cleaned)

    # union with raw lexicon
    raw_words = raw.get(cat, [])
    if raw_words and isinstance(raw_words[0], dict):
        raw_words = [r['word'] for r in raw_words]
    for w in raw_words:
        cleaned = strip_punctuation(w)
        if not cleaned:
            continue
        norm = cleaned.lower()
        if norm not in seen_norm:
            seen_norm[norm] = cleaned
            keep.append(cleaned)

    flat[cat] = sorted(keep, key=str.lower)

json.dump(flat, open(args.out, 'w'), indent=2, ensure_ascii=False)
print(f'wrote {args.out}: {sum(len(v) for v in flat.values())} items / {len(flat)} categories')