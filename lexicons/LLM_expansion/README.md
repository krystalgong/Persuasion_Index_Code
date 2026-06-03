# LLM-as-Lexicographer Expansion

This folder contains the LLM-assisted lexicon expansion pipeline for the
Persuasion Index. It takes theory definitions, prompts an OpenAI model for
candidate lexicon items, post-processes the raw generations, supports human
audit, and produces a flat lexicon JSON that can be used by the scorer.

## Files

| File | Purpose |
|---|---|
| `theory_definitions.json` | Category-level theory definitions, inclusion rules, exclusions, drift traps, and canonical seeds. |
| `generation_prompts.py` | Prompt builder for the nine generation slices per category. |
| `generator_runner.py` | Async OpenAI generation runner with retries, resume support, and a one-call preflight. |
| `postprocess_generation.py` | Deduplicates raw JSONL generations, splits hard negatives, writes audit files and summaries. |
| `apply_audit.py` | Applies human audit decisions and writes the final flat deployment lexicon. |
| `build_theory_definitions.py` | Source script used to generate `theory_definitions.json`. |

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4-mini
OPENAI_BASE_URL=
```

`OPENAI_BASE_URL` is optional. Leave it blank unless your institution/account
requires a custom endpoint. If preflight says `incorrect regional hostname`,
set:

```text
OPENAI_BASE_URL=https://us.api.openai.com/v1
```

The runner loads repo-root `.env` automatically. You can also pass a different
file:

```bash
python generator_runner.py --config path/to/config.env ...
```

## Smoke Test

Run one category and one slice before a larger generation job:

```bash
cd lexicons/LLM_expansion
python generator_runner.py \
  --theory theory_definitions.json \
  --output gen_smoke.jsonl \
  --only-categories LOGIC_CAUSAL \
  --only-slices formal_single \
  --concurrency 1 \
  --yes
```

Expected output:

- `gen_smoke.jsonl`: raw generated items plus one `slice_ok` metadata record.

Post-process the smoke output:

```bash
python postprocess_generation.py \
  --input gen_smoke.jsonl \
  --out smoke_out
```

Expected output directory:

- `smoke_out/lexicons.json`: rich lexicon entries with rationale/provenance.
- `smoke_out/hard_negatives.json`: generated hard negatives.
- `smoke_out/audit_priority.csv`: audit spreadsheet, sorted by risk.
- `smoke_out/category_sizes.csv`: per-category counts.
- `smoke_out/summary.json`: global counts.

Apply audit decisions. If `audit_priority.csv` has no `audit_decision` column,
the script treats every item as kept, which is useful for smoke tests.

```bash
python apply_audit.py \
  --rich-lexicon smoke_out/lexicons.json \
  --audit-csv smoke_out/audit_priority.csv \
  --raw-lexicons ../../helper_features/lexicons.json \
  --out smoke_out/lexicons_expanded_LLM_audited.json
```

## Full Run

```bash
cd lexicons/LLM_expansion
python generator_runner.py \
  --theory theory_definitions.json \
  --output gen_full.jsonl \
  --concurrency 8 \
  --yes

python postprocess_generation.py \
  --input gen_full.jsonl \
  --out full_out
```

If you have an embedding-baseline CSV, add:

```bash
--embedding-csv path/to/lexicons_expanded_embedding_report_round1.csv
```

## Human Audit

After post-processing, open `full_out/audit_priority.csv` and add an
`audit_decision` column:

- `1` or blank: keep the item.
- `2`: remove the item.

Then write the final flat lexicon:

```bash
python apply_audit.py \
  --rich-lexicon full_out/lexicons.json \
  --audit-csv full_out/audit_priority_DONE.csv \
  --raw-lexicons ../../helper_features/lexicons.json \
  --out full_out/lexicons_expanded_LLM_audited.json
```

To use the new audited lexicon in the main scorer, either copy it into
`helper_features/lexicons_expanded_LLM_audited.json` or set:

```bash
export PI_LEXICON_FILE=/absolute/path/to/full_out/lexicons_expanded_LLM_audited.json
```

## Notes

- `generator_runner.py` is resumable. Re-running the same command skips slice
  pairs already marked with `slice_ok` in the output JSONL.
- GPT-5-family and reasoning models use `max_completion_tokens`; GPT-4-family
  models use `max_tokens`. The runner chooses the parameter based on model id.
- Generated files are ignored by repo-level `.gitignore`.
