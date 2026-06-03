# Persuasion Index Code

Code and lexicon resources for computing Persuasion Index features from
argumentative text. The repository includes:

- `PI_score_generator.py`: low-level feature scoring for one text.
- `persuasion_runner.py`: simple public API for strings, lists, and DataFrames.
- `persuasion_profile.py`: raw scores plus UKP-derived weighted persuasion reports.
- `analysis_example.ipynb`: compact usage notebook for the scoring API.
- `lexicons/lexicons_validation/lexicon_code_validation.ipynb`: validation notebook for lexicon split-half checks.
- `lexicons/LLM_expansion/`: LLM-assisted lexicon expansion pipeline.

## Setup

Use Python 3.10 or newer. Python 3.11/3.12 is a conservative choice for
academic reproducibility.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Optional, but recommended for named-entity features:

```bash
python -m spacy download en_core_web_sm
```

## Configuration

API keys and local path overrides live in `.env`.

```bash
cp .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY` before running the LLM expansion
pipeline. The scoring notebooks do not require an API key.

Important config values:

- `OPENAI_API_KEY`: required for `lexicons/LLM_expansion/generator_runner.py`.
- `OPENAI_BASE_URL`: optional custom API endpoint.
- `OPENAI_MODEL`: default model for lexicon generation when `--model` is omitted.
- `PI_HELPER_DIR`: optional override for the `helper_features/` directory. Leave blank for normal repo use.
- `PI_LEXICON_FILE`: optional override for the lexicon JSON used by the scorer. Leave blank for normal repo use.
- `PI_DISABLE_SPACY=1`: disables spaCy loading if you do not need NER features.

Blank `PI_HELPER_DIR` and `PI_LEXICON_FILE` values are treated as unset.
Relative path overrides are resolved from the repository root, not from the
notebook or terminal working directory.

Do not commit `.env`.

## Quick Usage

Score one argument:

```python
from persuasion_runner import score_persuasion

scores = score_persuasion("According to recent studies, this policy will reduce costs.")
print(scores["Evidence"]["mean"])
```

Score a DataFrame:

```python
import pandas as pd
from persuasion_runner import score_persuasion

df = pd.DataFrame({"argument": ["This is urgent.", "The evidence is mixed."]})
subfeatures, means = score_persuasion(df, text_col="argument")
```

Generate the weighted profile report:

```python
from persuasion_profile import get_persuasion_report

raw_scores, weighted_scores = get_persuasion_report("This plan is practical and evidence-based.")
```

## Notebooks

Open the notebooks with the repo virtual environment interpreter:
`.venv/bin/python`. In VS Code, use "Select Kernel" / "Python Environments"
and choose the `.venv` in this repository.

- `analysis_example.ipynb` demonstrates the public scoring API, seeded vs.
  expanded lexicons, DataFrame scoring, and weighted reports.
- `lexicons/lexicons_validation/lexicon_code_validation.ipynb` validates
  scoring behavior and runs split-half lexicon checks. If the UKP train/test
  CSVs are not present, it falls back to a small built-in validation corpus so
  the notebook still executes.

To execute from the command line:

```bash
python -m nbconvert --to notebook --execute analysis_example.ipynb --output /tmp/analysis_example.executed.ipynb
python -m nbconvert --to notebook --execute lexicons/lexicons_validation/lexicon_code_validation.ipynb --output /tmp/lexicon_code_validation.executed.ipynb
```

## LLM Lexicon Expansion

The expansion pipeline lives in `lexicons/LLM_expansion/` and is documented in
[lexicons/LLM_expansion/README.md](lexicons/LLM_expansion/README.md).

Minimal smoke run after configuring `.env`:

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

Then post-process:

```bash
python postprocess_generation.py --input gen_smoke.jsonl --out smoke_out
python apply_audit.py \
  --rich-lexicon smoke_out/lexicons.json \
  --audit-csv smoke_out/audit_priority.csv \
  --raw-lexicons ../../helper_features/lexicons.json \
  --out smoke_out/lexicons_expanded_LLM_audited.json
```
