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

- `persuasion_index/`: installable package and stable public API.
- `pyproject.toml`: package metadata, dependencies, and command-line entry point.
- `PI_score_generator.py`: low-level scoring functions for one English argument.
- `persuasion_runner.py`: backward-compatible API for strings, lists, and DataFrames.
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

Install the package from this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

For an editable research environment with the lexicon-expansion and notebook
dependencies:

```bash
python -m pip install -e ".[lexicon,notebooks,dev]"
```

## Optional external resources

This repository and its wheel do not redistribute third-party dictionaries or
rating datasets unless redistribution permission is clear. The scorer still
returns the same 15 dimensions and 55 subfeatures without them, but some values
will be partial or will use documented fallback values.

Install the spaCy English model for named-entity features:

```bash
python -m spacy download en_core_web_sm
```

Without this model, NER-dependent parts of `Evidence.named_entities` and
`Authority/Credibility.organizations` are unavailable.

For LIWC-derived cues, obtain a dictionary through the
[official LIWC site](https://www.liwc.app/download) under an appropriate
license, then point the scorer to the local `.dic` file:

```bash
export PI_LIWC_FILE=/absolute/path/to/LIWC.dic
```

The loader supports standard LIWC `.dic` files and the compact
`Category: term1 term2 ...` format. The implementation uses the categories
`Ppron`, `I`, `You`, `Past`, `See`, `Anger`, `Sad`, `Anx`, and `Posemo`.
Without a compatible file, the LIWC-derived portions of several Sentiment,
Engagement, and Specificity subfeatures are unavailable.

For single-word concreteness, obtain the Brysbaert, Warriner, and Kuperman
ratings from the [Ghent University record](https://biblio.ugent.be/publication/5774089)
or its official data source. The loader accepts `.xlsx`, tab-delimited
`.txt`/`.tsv`, or `.csv` files containing `Word` and `Conc.M` columns:

```bash
export PI_CONCRETENESS_FILE=/absolute/path/to/concreteness_ratings.txt
```

For multiword concreteness, download the processed summary file from the
[authors' OSF project](https://osf.io/ksypa/) and provide the CSV containing
`Expression` and `Mean_C` columns:

```bash
export PI_MWE_CONCRETENESS_FILE=/absolute/path/to/mwe_concreteness.csv
```

If neither concreteness resource is available,
`Specificity.lexical_concreteness` uses the neutral fallback value `0.5`.
When only one is available, the score is computed from that resource alone.

For NRC-VAD, download the lexicon under its official terms and keep it outside
version control:

```bash
mkdir -p local_resources
curl -L "https://saifmohammad.com/WebDocs/Lexicons/NRC-VAD-Lexicon-v2.1.zip" \
  -o local_resources/NRC-VAD-Lexicon-v2.1.zip
unzip -q -o local_resources/NRC-VAD-Lexicon-v2.1.zip -d local_resources
export PI_NRC_VAD_FILE="$PWD/local_resources/NRC-VAD-Lexicon-v2.1/Unigrams/unigrams-NRC-VAD-Lexicon-v2.1.txt"
```

Without NRC-VAD, `Sentiment.valence`, `Sentiment.arousal`, and
`Sentiment.dominance` are set to `0.0`.

These fallbacks keep the API and vector dimensions stable. They are intended
for graceful execution, not as a claim of complete feature reproduction.
See `THIRD_PARTY_RESOURCES.md` for the full resource table.

Missing-resource warnings are enabled by default so partial output is visible.
For a known minimal configuration, they can be suppressed explicitly:

```bash
export PI_QUIET_OPTIONAL_WARNINGS=1
```

This setting only suppresses warnings for absent optional resources. Invalid
configured files and required-resource failures are still reported.

## Configuration

The LLM expansion scripts load API settings from a repository-level `.env`:

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
- `PI_LIWC_FILE`: path to a locally licensed LIWC-compatible dictionary.
- `PI_CONCRETENESS_FILE`: path to single-word concreteness ratings.
- `PI_MWE_CONCRETENESS_FILE`: path to multiword-expression concreteness ratings.
- `PI_NRC_VAD_FILE`: optional path to a separately downloaded NRC-VAD unigram file.
- `PI_DISABLE_SPACY=1`: disables spaCy loading if you do not need NER features.
- `PI_QUIET_OPTIONAL_WARNINGS=1`: suppresses known missing-resource warnings.

The scoring library reads `PI_*` values from the process environment. The
repository's LLM expansion runner also loads them from `.env`. Blank path
values are treated as unset, and relative paths resolve from the installed
module or repository root.

Do not commit `.env`, API keys, local paths, notebook checkpoints, `__pycache__/`, or `.DS_Store`.

## Quick usage

Score one argument:

```python
from persuasion_index import score

scores = score("According to recent studies, this policy will reduce costs.")
print(scores["Evidence"]["mean"])
```

Score a DataFrame:

```python
import pandas as pd
from persuasion_index import score_batch

df = pd.DataFrame({"argument": ["This is urgent.", "The evidence is mixed."]})
subfeatures, dimensions = score_batch(df, text_col="argument")
```

Generate the weighted profile report:

```python
from persuasion_index import get_report

raw_scores, weighted_scores = get_report(
    "This plan is practical and evidence-based."
)
```

The raw output keeps all 55 subfeatures visible. Dimension scores are transparent, unweighted averages of their constituent subfeatures. The weighted report is a separate empirical profile based on stored UKP logistic-regression coefficients.

The original imports from `persuasion_runner.py`, `persuasion_profile.py`, and
`PI_score_generator.py` remain available for existing notebooks.

## Command line

Installation also provides a `persuasion-index` command:

```bash
persuasion-index "According to recent studies, this policy will reduce costs."
```

Use `--profile` to include the UKP-weighted empirical profile, or pipe text
through standard input:

```bash
echo "This plan is urgent." | persuasion-index --profile
```

For a compact smoke test without optional-resource warnings:

```bash
PI_DISABLE_SPACY=1 PI_QUIET_OPTIONAL_WARNINGS=1 \
  persuasion-index --compact "This is urgent."
```

## Quick verification

The following checks installation, the 15-dimension/55-subfeature schema,
batch scoring, and the stored UKP profile:

```bash
python -m pip install -e ".[dev,notebooks]"
python -m pytest -q

python - <<'PY'
from persuasion_index import get_report, score, score_batch
import pandas as pd

scores = score(
    "According to recent studies, this policy will reduce costs by 20%."
)
assert len(scores) == 15
assert sum(len(values) - 1 for values in scores.values()) == 55

subfeatures, dimensions = score_batch(
    pd.DataFrame(
        {"argument": ["This is urgent.", "The evidence is mixed."]}
    )
)
assert subfeatures.shape == (2, 55)
assert dimensions.shape == (2, 15)

raw, weighted = get_report(
    "This proposal is practical and evidence-based."
)
assert len(raw) == 15
assert weighted is not None

print("Persuasion Index smoke test passed.")
PY
```

## How scoring works

Each subfeature is mapped to `[0, 1]`. Most lexical cues use a saturating density transform,

```text
score = 1 - exp(-0.5 * r)
```

where `r` is the match rate per 100 tokens. Sparse cues are represented as binary presence/absence indicators. When lexicon matches overlap, the scorer retains the longest non-contained span. Each of the 15 dimension scores is the unweighted mean of its subfeatures.

PI scores describe cues present in a message. They should not be interpreted as a universal probability that the message will persuade a particular audience:

- **Evidence** features detect evidence-like signals such as statistics, attribution phrases, and named entities. They do not perform external fact-checking or verify whether a claim is true.
- **Logic/Cohesion** features detect explicit structural and discourse markers. They do not prove that an argument is formally valid.
- **Sentiment** combines VADER affective intensity, project lexicons, and, when locally configured, LIWC categories and NRC-VAD ratings.
- **Weighted profile scores** in `persuasion_profile.py` use stored UKP coefficients. They are an empirical UKP-oriented output, not a context-free persuasion score.

## Scope and limitations

The current implementation targets English argumentative text. Its lexicons,
tokenization, VADER model, and optional external resources are English-specific.
Scores produced without optional third-party resources are valid partial
outputs but are not numerically equivalent to the full configuration described
in the paper.

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

## License

Unless otherwise stated, the project code, documentation, and project-created
PI lexicons are released under the [Apache License 2.0](LICENSE).

Third-party resources are not redistributed and remain subject to their
original licenses and terms. See `THIRD_PARTY_RESOURCES.md`.
