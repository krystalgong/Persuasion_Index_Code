"""
Post-processor for generator_runner.py output.

Reads the raw JSONL (one record per generated item) and produces:

  out/lexicons.json
      Final clean lexicon, organised by category. Each entry includes
      the union of slice provenance, register set, all rationales, and a
      derived n_slices field — items appearing across multiple slices
      get high natural confidence.

  out/hard_negatives.json
      Items from negation_partner / boundary_test slices, kept separate.

  out/audit_priority.csv
      A spreadsheet to drive human audit. Sorted so the riskiest items
      come first: low-confidence + single-slice-occurrence + boundary
      items at the top.

  out/coverage_overlap.csv  (only if --embedding-csv is provided)
      Per-category counts comparing the generated lexicon to the legacy
      embedding-expanded CSV. Columns:
        n_generated, n_embed_unique_at_sim_geq_X, n_overlap, jaccard,
        embed_only_high_sim_count.
      This is the headline figure for the paper's "head-to-head" panel.
"""
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
def load_records(path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (item_records, meta_records)."""
    items, metas = [], []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if "_meta_status" in r:
                metas.append(r)
            else:
                items.append(r)
    return pd.DataFrame(items), pd.DataFrame(metas)


def normalise_word(w: str) -> str:
    """Conservative normalisation for dedup: lowercase + collapse whitespace.
    We do NOT strip punctuation because some items are punctuation-bearing
    (e.g. '%', 'right?', "i.e.")."""
    return re.sub(r"\s+", " ", w.strip().lower())


# ---------------------------------------------------------------------------
# Build merged lexicon
# ---------------------------------------------------------------------------
def merge_items(items: pd.DataFrame) -> pd.DataFrame:
    """Group by (category, normalised word). Aggregate slice provenance,
    registers, types, rationales, hard-negative flag."""
    df = items.copy()
    df["word_norm"] = df["word"].apply(normalise_word)

    grouped = (
        df.groupby(["category", "word_norm"])
          .agg(
              word_surface=("word", lambda s: max(set(s), key=list(s).count)),
              slices=("slice", lambda s: sorted(set(s))),
              registers=("register", lambda s: sorted(set(s))),
              types=("type", lambda s: sorted(set(s))),
              confidences=("confidence", lambda s: sorted(set(s))),
              rationales=("rationale", lambda s: list(s)),
              is_hard_negative_any=("is_hard_negative", "any"),
              is_hard_negative_all=("is_hard_negative", "all"),
              n_slices=("slice", "nunique"),
              n_occurrences=("slice", "size"),
          )
          .reset_index()
    )

    # Resolve confidence: max of any confidence label seen
    rank = {"low": 0, "medium": 1, "high": 2}
    grouped["confidence_max"] = grouped["confidences"].apply(
        lambda lst: ["low", "medium", "high"][max(rank[c] for c in lst)]
    )
    return grouped


# ---------------------------------------------------------------------------
# Split clean lexicon vs hard negatives
# ---------------------------------------------------------------------------
def split_lexicon(merged: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """An item is a hard negative if EVERY slice that produced it was a
    hard-negative slice. If the same word appeared in BOTH a positive and
    a hard-negative slice, the positive evidence wins (item joins the
    clean lexicon, but a 'contested' flag is set)."""
    merged = merged.copy()
    merged["is_contested"] = (
        merged["is_hard_negative_any"] & ~merged["is_hard_negative_all"]
    )
    clean = merged[~merged["is_hard_negative_all"]].copy()
    hardneg = merged[merged["is_hard_negative_all"]].copy()
    return clean, hardneg


# ---------------------------------------------------------------------------
# Audit priority ranking
# ---------------------------------------------------------------------------
def audit_priority(clean: pd.DataFrame) -> pd.DataFrame:
    """Higher score => audit first. Risk factors:
       - low max-confidence
       - single-slice occurrence
       - 'contested' flag (also appeared in a hard-negative slice)
       - 'inflection' or 'phrase' types are slightly riskier"""
    df = clean.copy()
    rank_conf = {"low": 3, "medium": 2, "high": 0}
    df["risk_confidence"] = df["confidence_max"].map(rank_conf)
    df["risk_single_slice"] = (df["n_slices"] == 1).astype(int) * 2
    df["risk_contested"] = df["is_contested"].astype(int) * 4
    df["risk_score"] = (
        df["risk_confidence"] + df["risk_single_slice"] + df["risk_contested"]
    )
    df = df.sort_values(["risk_score", "category", "word_norm"], ascending=[False, True, True])
    return df


# ---------------------------------------------------------------------------
# Embedding overlap (paper-side comparison)
# ---------------------------------------------------------------------------
def overlap_with_embedding(
    clean: pd.DataFrame,
    hardneg: pd.DataFrame,
    embed_csv: Path,
    sim_threshold: float = 0.7,
) -> pd.DataFrame:
    edf = pd.read_csv(embed_csv)
    edf["expanded_norm"] = edf["expanded_word"].astype(str).map(normalise_word)
    edf_high = edf[edf["similarity_score"] >= sim_threshold]

    rows = []
    cats = set(clean["category"]) | set(hardneg["category"]) | set(edf["category"])
    for c in sorted(cats):
        gen_clean_words = set(clean[clean["category"] == c]["word_norm"])
        gen_hardneg_words = set(hardneg[hardneg["category"] == c]["word_norm"])
        embed_words = set(edf_high[edf_high["category"] == c]["expanded_norm"])
        overlap = gen_clean_words & embed_words
        embed_only = embed_words - gen_clean_words
        embed_only_caught_as_hardneg = embed_only & gen_hardneg_words
        union = gen_clean_words | embed_words
        rows.append({
            "category": c,
            "n_generated_clean": len(gen_clean_words),
            "n_generated_hardneg": len(gen_hardneg_words),
            f"n_embed_at_sim_geq_{sim_threshold}": len(embed_words),
            "n_overlap": len(overlap),
            "jaccard": len(overlap) / len(union) if union else 0.0,
            "embed_only": len(embed_only),
            "embed_only_caught_as_hardneg": len(embed_only_caught_as_hardneg),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Serialise
# ---------------------------------------------------------------------------
def to_lexicon_json(clean: pd.DataFrame) -> Dict:
    """Final shape: {category: [items...]}. Each item lean enough to drop
    into your downstream regex/lookup pipeline."""
    out: Dict[str, List[Dict]] = {}
    for cat, sub in clean.groupby("category"):
        items = []
        for _, r in sub.iterrows():
            items.append({
                "word": r["word_surface"],
                "registers": r["registers"],
                "types": r["types"],
                "confidence": r["confidence_max"],
                "n_slices": int(r["n_slices"]),
                "is_contested": bool(r["is_contested"]),
                "slices": r["slices"],
                "rationales": r["rationales"],
            })
        # sort: confidence desc, n_slices desc, word asc
        rank = {"high": 0, "medium": 1, "low": 2}
        items.sort(key=lambda x: (rank[x["confidence"]], -x["n_slices"], x["word"].lower()))
        out[cat] = items
    return out


def to_hardneg_json(hardneg: pd.DataFrame) -> Dict:
    out: Dict[str, List[Dict]] = {}
    for cat, sub in hardneg.groupby("category"):
        items = []
        for _, r in sub.iterrows():
            items.append({
                "word": r["word_surface"],
                "registers": r["registers"],
                "types": r["types"],
                "slices": r["slices"],
                "rationales": r["rationales"],
            })
        items.sort(key=lambda x: x["word"].lower())
        out[cat] = items
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="JSONL produced by generator_runner.py")
    p.add_argument("--out", required=True, help="Output directory")
    p.add_argument("--embedding-csv", default=None,
                   help="Optional: legacy embedding CSV for head-to-head overlap")
    p.add_argument("--embedding-sim-threshold", type=float, default=0.7,
                   help="Cosine threshold to consider an embedding-expansion item 'admitted' for the comparison baseline")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    items, metas = load_records(Path(args.input))
    print(f"[load] {len(items):,} item records, {len(metas):,} meta records")
    if not metas.empty:
        n_ok = (metas["_meta_status"] == "slice_ok").sum()
        n_fail = (metas["_meta_status"] == "slice_failed").sum()
        print(f"[load] slices: {n_ok} ok, {n_fail} failed")
    if items.empty:
        raise SystemExit("No items to process.")

    merged = merge_items(items)
    clean, hardneg = split_lexicon(merged)

    print(f"[stats] clean lexicon items:    {len(clean):,}")
    print(f"[stats] hard-negative items:    {len(hardneg):,}")
    print(f"[stats] contested items (positive evidence wins): {clean['is_contested'].sum():,}")

    # Per-category headline
    cat_summary = (
        clean.groupby("category")
             .agg(
                 n_items=("word_norm", "size"),
                 n_high_conf=("confidence_max", lambda s: (s == "high").sum()),
                 mean_n_slices=("n_slices", "mean"),
             )
             .round(2)
             .sort_values("n_items", ascending=False)
    )
    cat_summary.to_csv(out / "category_sizes.csv")
    print(f"[write] category_sizes.csv ({len(cat_summary)} rows)")

    # Final lexicon JSON
    (out / "lexicons.json").write_text(
        json.dumps(to_lexicon_json(clean), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[write] lexicons.json")

    # Hard negatives
    (out / "hard_negatives.json").write_text(
        json.dumps(to_hardneg_json(hardneg), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[write] hard_negatives.json")

    # Audit priority CSV
    audit_df = audit_priority(clean)
    audit_cols = [
        "category", "word_surface", "confidence_max", "n_slices",
        "is_contested", "risk_score", "registers", "types", "slices", "rationales",
    ]
    audit_df["registers"] = audit_df["registers"].apply(lambda lst: "|".join(lst))
    audit_df["types"] = audit_df["types"].apply(lambda lst: "|".join(lst))
    audit_df["slices"] = audit_df["slices"].apply(lambda lst: "|".join(lst))
    audit_df["rationales"] = audit_df["rationales"].apply(lambda lst: " ||| ".join(lst))
    audit_df[audit_cols].to_csv(out / "audit_priority.csv", index=False)
    print(f"[write] audit_priority.csv ({len(audit_df):,} rows; sort top-down for review)")

    # Optional overlap with embedding CSV
    if args.embedding_csv:
        overlap = overlap_with_embedding(
            clean, hardneg, Path(args.embedding_csv),
            sim_threshold=args.embedding_sim_threshold,
        )
        overlap.to_csv(out / "coverage_overlap.csv", index=False)
        print(f"[write] coverage_overlap.csv ({len(overlap)} rows)")
        print(
            f"[stats] mean Jaccard(generated_clean, embed@sim>={args.embedding_sim_threshold}): "
            f"{overlap['jaccard'].mean():.3f}"
        )

    # Summary
    summary = {
        "n_clean_items": int(len(clean)),
        "n_hardneg_items": int(len(hardneg)),
        "n_contested": int(clean["is_contested"].sum()),
        "n_categories": int(clean["category"].nunique()),
        "items_by_confidence": clean["confidence_max"].value_counts().to_dict(),
        "items_by_register_summary": (
            clean["registers"].apply(lambda lst: tuple(sorted(lst))).value_counts().head(10).to_dict()
        ),
    }
    # tuple keys are not JSON-serialisable; stringify
    summary["items_by_register_summary"] = {
        ", ".join(k): v for k, v in summary["items_by_register_summary"].items()
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[write] summary.json")
    print(f"[done] all outputs in {out}/")


if __name__ == "__main__":
    main()
