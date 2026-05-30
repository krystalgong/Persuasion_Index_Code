# LLM-as-Lexicographer Expansion

Theory-grounded LLM expansion of the Persuasion Index lexicons,
covering the 15 dimensions / 55 sub-categories defined in
`Section 3` of the paper. This module is **Step 4** of the lexicon
construction pipeline (see paper for Steps 1–3 and 5).

## What this module does

Given a JSON file of theoretical definitions (one per category, with
inclusion / exclusion criteria, theoretical anchors, and seed words),
this pipeline:

1. **Generates** candidate lexicon items in 9 register- and
   morphology-conditioned slices per category, using a strict-JSON
   prompt against an LLM (default `gpt-5.4-mini`).
2. **Post-processes** the raw items: deduplicates across slices,
   segregates hard-negatives, computes audit priority scores, and
   compares against an embedding-expansion baseline.
3. **Human audit** on `audit_priority.csv` — review and mark each
   item 1 for `keep` / 2 for `remove`.
4. **Flattens** the audited lexicon into a deployment-shape JSON suitable
   for downstream feature extraction, with optional union against the
   hand-curated raw lexicon (Step 1 output).

## Folder structure

```
lexicons/lexicon_expansion/LLM_expansion/
├── theory_definitions.json     # input: 55 category specs (Steps 1–3 output)
├── generation_prompts.py       # prompt builders for the 9 slices
├── generator_runner.py         # async LLM calls with resume + preflight
├── postprocess_generation.py   # merge slices, segregate hard-negatives
├── apply_audit.py              # apply human audit decisions to rich lexicon
├── archived/                   # superseded scripts kept for reference
└── README.md                   # this file

# inputs (provided by upstream pipeline)
helper_features/lexicons.json                       # Step 1 hand-curated seed lexicon
lexicons_expanded_embedding_report_round1.csv       # Step 4 embedding baseline
```

## File reference

### Inputs

| File | Source | Purpose |
|---|---|---|
| `theory_definitions.json` | Steps 1–3 of paper | 55 category definitions: function, theory anchor, include/exclude criteria, drift traps, canonical seeds |
| `helper_features/lexicons.json` | Step 1 (manual seeding) | Hand-curated raw seed lexicon — the gold-standard floor that must always survive into the final output |
| `lexicons_expanded_embedding_report_round1.csv` | Step 4 (embedding expansion) | Embedding-baseline candidates for head-to-head coverage comparison |

### Code

| File | What it does | Inputs | Outputs |
|---|---|---|---|
| `generation_prompts.py` | Builds the 9 slice prompts per category. Library only — never run directly. | — | — |
| `generator_runner.py` | Async calls to the LLM, one call per `(category, slice)` pair, with retry, resume, and preflight check | `theory_definitions.json` | `gen_*.jsonl` (one item per line + slice-status meta records) |
| `postprocess_generation.py` | Merges slice outputs, segregates hard-negatives, computes risk scores, optionally compares to embedding baseline | `gen_*.jsonl`, embedding CSV (optional) | directory with `lexicons.json`, `hard_negatives.json`, `audit_priority.csv`, `category_sizes.csv`, `coverage_overlap.csv`, `summary.json` |
| `apply_audit.py` | Applies human audit decisions (`1`=keep, `2`=remove, empty=keep) to produce the final flat lexicon | `lexicons.json`, `audit_priority_DONE.csv`, `helper_features/lexicons.json` (optional) | `lexicons_expanded_LLM_audited.json` |
<!-- | `flatten_lexicon.py` | Converts rich `lexicons.json` to flat `{category: [word, ...]}` shape; optionally merges in raw seed lexicon | `lexicons.json`, `helper_features/lexicons.json` (optional) | `lexicons_expanded_LLM.json` (deployment shape) | -->

### Outputs

After a full run completes, `full_out/` contains:

| File | Contents | When to use |
|---|---|---|
| `lexicons.json` | **Rich lexicon** — every item with rationale, register, slice provenance, confidence, contested flag | Paper supplementary; debugging |
| `lexicons_expanded_LLM_audited.json` | **Flat lexicon** — `{category: [word, ...]}` deployment shape, after human audit | Drop into downstream PI feature extractor |
| `hard_negatives.json` | Items the LLM generated as boundary cases / antonyms | Test cases to verify your downstream matcher correctly excludes them |
| `audit_priority.csv` | Every clean lexicon item, sorted by risk score (highest first) | Driver for human audit — see "Human in the loop" below |
| `category_sizes.csv` | Per-category headcount + high-confidence share | Sanity check; spot weak categories |
| `coverage_overlap.csv` | Per-category Jaccard with embedding baseline + same-source hard-negative agreement | Paper Step 6 head-to-head figure |
| `summary.json` | Global stats | Paper headline numbers |

## Setup

```bash
# From the repo root
cd lexicons/lexicon_expansion/LLM_expansion

# Make sure your venv is active and dependencies are installed
pip install openai pydantic tqdm pandas

# Verify .env file has the API key
cat ../../../.env
```

Your `.env` (at the repo root) needs at minimum:

```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://us.api.openai.com/v1     # required for UMD enterprise accounts
```

## Running the pipeline

### Smoke test (2 categories, ~3 min, ~$0.30)

Run this first to verify your environment and confirm prompt quality
on a small slice before committing to the full 55-category run.

```bash
# Load env vars into the shell
set -a && source ../../../.env && set +a

# Sanity check — should show first 10 chars of API key
echo "API key starts with: ${OPENAI_API_KEY:0:10}..."

# Step 1: Generate
python3 generator_runner.py \
    --theory theory_definitions.json \
    --output gen_smoke.jsonl \
    --only-categories "LOGIC_CAUSAL,IMPACT_GAIN" \
    --model gpt-5.4-mini-2026-03-17 \
    --concurrency 6 \
    --yes

# Step 2: Post-process (produces audit_priority.csv for human review)
python3 postprocess_generation.py \
    --input gen_smoke.jsonl \
    --out smoke_out \
    --embedding-csv ../../lexicons_expanded_embedding_report_round1.csv

# Step 3: Human audit — open smoke_out/audit_priority.csv, add audit_decision column,
#          save as smoke_out/audit_priority_DONE.csv

# Step 4: Apply audit decisions + flatten
python3 apply_audit.py \
    --rich-lexicon smoke_out/lexicons.json \
    --audit-csv smoke_out/audit_priority_DONE.csv \
    --raw-lexicons ../../../helper_features/lexicons.json \
    --out smoke_out/lexicons_expanded_LLM_audited.json
```

### Full run (all 55 categories, ~20 min, ~$4)

```bash
set -a && source ../../../.env && set +a

# Step 1: Generate
python3 generator_runner.py \
    --theory theory_definitions.json \
    --output gen_full.jsonl \
    --model gpt-5.4-mini-2026-03-17 \
    --concurrency 8 \
    --yes

# Step 2: Post-process (produces full_out/audit_priority.csv for human review)
python3 postprocess_generation.py \
    --input gen_full.jsonl \
    --out full_out \
    --embedding-csv ../../lexicons_expanded_embedding_report_round1.csv

# Step 3: Human audit — open full_out/audit_priority.csv, add audit_decision column,
#          save as full_out/audit_priority_DONE.csv

# Step 4: Apply audit decisions + flatten
python3 apply_audit.py \
    --rich-lexicon full_out/lexicons.json \
    --audit-csv full_out/audit_priority_DONE.csv \
    --raw-lexicons ../../../helper_features/lexicons.json \
    --out full_out/lexicons_expanded_LLM_audited.json
```

The `&&` chains the four steps so each only runs if the previous
succeeds. If anything dies mid-way, just re-run the same
`generator_runner.py` command — it's resumable and will skip
already-completed `(category, slice)` pairs.

## Human in the loop

This is the part the paper calls "prioritized human audit". The audit happens **between** Step 2 (post-process) and Step 4 (apply + flatten), once you have `audit_priority.csv` in hand.

### When to audit

You audit **once**, after post-process finishes (Step 2). The output
you care about is `full_out/audit_priority.csv`.

You don't have to review all 6,950 items. The CSV is sorted so the
riskiest items appear first; in our run, only 1,323 items have a
risk score ≥ 5 — these are the ones worth a human pass. Items with
risk score 0 (high confidence + multi-slice + uncontested) can be
trusted as-is.

### What the risk score means

Each item gets a score derived from three factors:

| Factor | Points | Why |
|---|---|---|
| `is_contested = True` | +4 | Item appeared in both positive and adversarial slices — the LLM disagrees with itself |
| `confidence = low` | +3 | Generator is unsure |
| `confidence = medium` | +2 | Generator has reservations |
| `n_slices = 1` | +2 | Only one slice surfaced this item — no cross-slice corroboration |

Score interpretation:

| Score | Action |
|---|---|
| ≥ 5 | **Human review required.** These are your audit targets. |
| 3–4 | Review if time permits. |
| ≤ 2 | Trust as-is unless something looks wrong on a spot-check. |


### Audit workflow

1. **Open `audit_priority.csv` in a spreadsheet tool**
   (Excel, Google Sheets, or a CSV viewer). It has columns
   `category`, `word_surface`, `confidence_max`, `n_slices`,
   `is_contested`, `risk_score`, `registers`, `types`, `slices`,
   `rationales` (with `|||` as separator between multiple rationales).

2. **Add an `audit_decision` column.** Two values:
   - `1` — keep (also the default if left empty)
   - `2` — remove (item is wrong or a boundary case)

3. **Read top-down.** Items are pre-sorted by risk_score (descending).
   For each row, look at the `word_surface`, the `rationales`, and the
   `slices` it came from. Mark `2` to remove, leave empty or `1` to keep.

4. **Two-annotator workflow:** have two
   annotators independently fill in the column, then compute
   Cohen's κ on the verdicts. This is the validity number reviewers
   will ask for in Step 6 of your paper.

5. **Apply the decisions** with the helper script below.

### Removing or moving items after the audit

Run the apply script — this is a one-shot edit that produces a corrected
flat lexicon:

```bash
python3 apply_audit.py \
    --rich-lexicon full_out/lexicons.json \
    --audit-csv full_out/audit_priority_DONE.csv \
    --raw-lexicons ../../../helper_features/lexicons.json \
    --out full_out/lexicons_expanded_LLM_audited.json
```

### Adding items the LLM missed

If during the audit (or while testing downstream) you discover a
term the LLM should have generated but didn't — for example, you
spot `because of which` in a real argument and the LLM never
produced it — you have two options:

**Option A: Fast path.** Add it to your raw seed lexicon
(`helper_features/lexicons.json`) and re-run **only the flatten step**:

```bash
python3 flatten_lexicon.py \
    --rich-lexicon full_out/lexicons.json \
    --raw-lexicons ../../../helper_features/lexicons.json \
    --out full_out/lexicons_expanded_LLM.json \
    --min-confidence medium
```

The flat output is just a set union with the raw lexicon — adding to
raw guarantees the term appears in the final output. Cost: zero. Time:
seconds. Recommended for individual additions.

**Option B: Re-generate.** Add the term to the `canonical_seeds` of
the relevant category in `theory_definitions.json`, delete
`gen_full.jsonl`, and re-run the full pipeline. The LLM will
generate around the new seed and you may discover related items it
missed before. Cost: ~$5–8. Time: ~40 minutes. Use when you suspect
a category has systematic gaps.

### Removing items that are wrong

The `apply_audit.py` script handles this — items marked
`remove` in the audit CSV are dropped from the flat lexicon. If you
spot something later (after the audit is "done"), you have two options:

**Option A: Re-edit the audit CSV** and re-run `apply_audit.py`.
The script is idempotent — it always reads from the rich lexicon and
applies the current audit decisions, so subsequent edits work
correctly.

**Option B: Direct edit of `lexicons_expanded_LLM.json`.** If you only
need to remove one or two items and don't care about audit
provenance, you can just hand-edit the flat JSON. But this is
dangerous if you later re-run the pipeline — your manual edit will be
lost. Use Option A for anything you'll need to defend in the paper.

## Common errors

| Error | Fix |
|---|---|
| `OPENAI_API_KEY not set` | You didn't `set -a && source ../../../.env && set +a` in this shell session |
| `incorrect_hostname` 401 | Set `OPENAI_BASE_URL=https://us.api.openai.com/v1` (UMD enterprise) |
| `Unsupported parameter: 'max_tokens'` | You're on an old `generator_runner.py`. The latest version auto-detects GPT-5 family models and uses `max_completion_tokens` |
| `No module named 'openai'` | Wrong venv. `which python3` to check |
| Generator dies mid-run | Re-run the same `generator_runner.py` command; it auto-resumes |
| `postprocess_generation.py` says "No items to process" | Your JSONL only contains `_meta_status` records (all slices failed). Inspect with `head -3 gen_*.jsonl` |


<!-- ## Citing

If you use this pipeline, see Section 4 of the paper for full method
attribution. The lexicon was constructed using
`gpt-5.4-mini-2026-03-17` between [insert dates], with code archived
in this directory at commit `[insert hash]`. -->
