# Persuasion Index

Code and resources for **Persuasion Index: A Theory-Guided Framework for Persuasion Analysis**.

The Persuasion Index (PI) represents persuasive language through 15 theory-grounded rhetorical dimensions and 55 transparent lexicon- and rule-based subfeatures. It is designed for interpretable analysis of rhetorical cues in human- and AI-generated text.

Try the interactive web interface:

https://anonymous.4open.science/w/pi-1DE2/

## Framework at a glance

The 15 dimensions are organized under the Aristotelian triad:

| Appeal | Dimensions |
|---|---|
| **Logos** | Evidence, Logic/Cohesion, Argumentation, Specificity, Opponent's View |
| **Ethos** | Authority/Credibility, Politeness, Commitment, Style |
| **Pathos** | Sentiment, Impact, Engagement, Reciprocity, Scarcity/Urgency, Propaganda |

The taxonomy and its implementation are separate by design. The current scorer uses interpretable lexical and structural cues, while individual detectors can be replaced or extended without changing the 15-dimension framework.

## Repository contents

- `PI_score_generator.py`: low-level scoring functions for one English argument.
- `persuasion_runner.py`: simple public API for strings, lists, and DataFrames.
- `persuasion_profile.py`: raw PI scores plus UKP-derived weighted profile scores.
- `helper_features/lexicons.json`: original seed lexicons.
- `helper_features/lexicons_expanded_LLM_audited.json`: audited expanded lexicons used by default.
- `helper_features/regression_outputs/`: stored UKP coefficient files used by `get_persuasion_report`.
- `analysis_example.ipynb`: compact usage notebook for the public scoring API.
- `lexicons/lexicons_validation/lexicon_code_validation.ipynb`: validation notebook for scoring behavior and split-half lexicon checks.
- `lexicons/LLM_expansion/`: LLM-assisted lexicon expansion pipeline.
- `THIRD_PARTY_RESOURCES.md`: helper-resource provenance, citation, and license notes.

This repository focuses on scoring, interpretation, and lexicon construction. Evaluation corpora and other large experiment artifacts are not bundled. The paper reports evaluation on four public datasets: UKPConvArg1, ChangeMyView, IBM Argument Quality, and Anthropic Persuasion.

## Setup

Use Python 3.10 or newer. Python 3.11 or 3.12 is recommended.

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

The scorer still runs without the spaCy model, but NER-dependent features will be reduced.

Optional NRC-VAD setup for valence/arousal/dominance sentiment features:

```bash
mkdir -p helper_features
curl -L "https://saifmohammad.com/WebDocs/Lexicons/NRC-VAD-Lexicon-v2.1.zip" \
  -o /tmp/NRC-VAD-Lexicon-v2.1.zip
unzip -q -o /tmp/NRC-VAD-Lexicon-v2.1.zip -d helper_features
```

NRC-VAD is not bundled in this repository because the official terms permit non-commercial research/educational use but do not allow redistribution. The scorer expects the downloaded file at `helper_features/NRC-VAD-Lexicon-v2.1/Unigrams/unigrams-NRC-VAD-Lexicon-v2.1.txt`. If it is absent, the scorer still runs and sets the VAD subfeatures to `0.0`.

## Configuration

API keys and local path overrides live in `.env`.

```bash
cp .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY` only if you plan to run the LLM expansion pipeline. The scoring API and notebooks do not require an API key.

Important config values:

- `OPENAI_API_KEY`: required only for `lexicons/LLM_expansion/generator_runner.py`.
- `OPENAI_BASE_URL`: optional custom API endpoint.
- `OPENAI_MODEL`: default model for lexicon generation when `--model` is omitted.
- `PI_HELPER_DIR`: optional override for the `helper_features/` directory. Leave blank for normal repo use.
- `PI_LEXICON_FILE`: optional override for the lexicon JSON used by the scorer. Leave blank for normal repo use.
- `PI_DISABLE_SPACY=1`: disables spaCy loading if you do not need NER features.

Blank `PI_HELPER_DIR` and `PI_LEXICON_FILE` values are treated as unset. Relative path overrides are resolved from the repository root, not from the notebook or terminal working directory.

Do not commit `.env`, API keys, local paths, notebook checkpoints, `__pycache__/`, or `.DS_Store`.

## Quick usage

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

raw_scores, weighted_scores = get_persuasion_report(
    "This plan is practical and evidence-based."
)
```

The raw output keeps all 55 subfeatures visible. Dimension scores are transparent, unweighted averages of their constituent subfeatures. The weighted report is a separate empirical profile based on stored UKP logistic-regression coefficients.

## How scoring works

Each subfeature is mapped to `[0, 1]`. Most lexical cues use a saturating density transform,

```text
score = 1 - exp(-0.5 * r)
```

where `r` is the match rate per 100 tokens. Sparse cues are represented as binary presence/absence indicators. When lexicon matches overlap, the scorer retains the longest non-contained span. Each of the 15 dimension scores is the unweighted mean of its subfeatures.

PI scores describe cues present in a message. They should not be interpreted as a universal probability that the message will persuade a particular audience:

- **Evidence** features detect evidence-like signals such as statistics, attribution phrases, and named entities. They do not perform external fact-checking or verify whether a claim is true.
- **Logic/Cohesion** features detect explicit structural and discourse markers. They do not prove that an argument is formally valid.
- **Sentiment** combines VADER affective intensity, affective lexicons, LIWC-style categories, and optional NRC-VAD ratings.
- **Weighted profile scores** in `persuasion_profile.py` use stored UKP coefficients. They are an empirical UKP-oriented output, not a context-free persuasion score.

## Scope and limitations

The current implementation targets English argumentative text. Its lexicons, tokenization, concreteness resources, VADER model, LIWC-style categories, and optional NRC-VAD ratings are English-specific.

PI analyzes rhetorical choices encoded in a message. It does not observe audience attitudes, source reputation, relationship history, or the surrounding social context, all of which can affect persuasive outcomes. Surface-level detectors also have limited coverage of implicit framing, irony, sarcasm, long-range narrative structure, and cross-sentence argumentation.

Associations between PI dimensions and persuasive outcomes vary across datasets, topics, and stances. Before using PI in a new applied setting, examine local score distributions and check for systematic disparities across relevant groups. PI is intended for analysis and auditing of persuasive language, not for generating manipulative content.

## Notebooks

Open the notebooks with the repo virtual environment interpreter: `.venv/bin/python`. In VS Code, use "Select Kernel" / "Python Environments" and choose the `.venv` in this repository.

- `analysis_example.ipynb` demonstrates the public scoring API, seeded vs. expanded lexicons, DataFrame scoring, and weighted reports.
- `lexicons/lexicons_validation/lexicon_code_validation.ipynb` validates scoring behavior and runs split-half lexicon checks. If the UKP train/test CSVs are not present, it falls back to a small built-in validation corpus so the notebook still executes.

To execute from the command line:

```bash
python -m nbconvert --to notebook --execute analysis_example.ipynb --output /tmp/analysis_example.executed.ipynb
python -m nbconvert --to notebook --execute lexicons/lexicons_validation/lexicon_code_validation.ipynb --output /tmp/lexicon_code_validation.executed.ipynb
```

## LLM lexicon expansion

The expansion pipeline lives in `lexicons/LLM_expansion/` and is documented in `lexicons/LLM_expansion/README.md`. It follows the seven register- and morphology-conditioned slices described in the paper.

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

The default deployment lexicon in this repository is `helper_features/lexicons_expanded_LLM_audited.json`.
