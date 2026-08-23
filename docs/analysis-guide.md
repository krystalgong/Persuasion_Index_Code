# Persuasion Index usage and analysis guide

Persuasion Index (PI) is a Python library for descriptive and comparative text
analysis. It extracts 55 interpretable subfeatures and aggregates them into 15
theory-guided dimensions. This guide covers the path from a clean installation
to an analysis table that can be inspected, exported, and reproduced. PI does
not require a web service or an API key for scoring.

## 1. Install in a clean environment

Create an isolated environment and install the package:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install persuasion-index
```

Avoid installing into an existing Conda `base` environment. Scientific
environments often contain compiled packages tied to a particular NumPy
version, and upgrading only part of that stack can make unrelated packages
fail to import.

For the current TestPyPI release candidate, install dependencies from PyPI and
PI itself from TestPyPI:

```bash
python -m pip install numpy pandas wordfreq vaderSentiment
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --no-deps \
  persuasion-index==0.2.0rc6
```

In a Jupyter notebook, use `%pip` rather than `!pip` so installation targets
the active kernel. Restart the kernel after installation if imports still
resolve to an older environment.

When installing from a local clone, replace the final command with:

```bash
python -m pip install .
```

The lightweight installation runs without spaCy and without locally licensed
resources. For named-entity features and Excel-formatted concreteness ratings:

```bash
python -m pip install "persuasion-index[spacy,excel]"
python -m spacy download en_core_web_sm
```

Optional LIWC, NRC-VAD, and concreteness data are not redistributed. See the
[resource and license notes](../THIRD_PARTY_RESOURCES.md) before configuring
them.

## 2. Analyze one text

```python
from persuasion_index import score

scores = score(
    "According to recent studies, this policy could reduce costs by 20%."
)

print(scores["Evidence"])
print(scores["Evidence"]["mean"])
```

The return value contains 15 dimension dictionaries. Each dictionary contains
its subfeature scores and a `mean` entry.

To inspect the strongest dimension means:

```python
top_dimensions = sorted(
    ((name, values["mean"]) for name, values in scores.items()),
    key=lambda item: item[1],
    reverse=True,
)

for name, value in top_dimensions[:5]:
    print(f"{name}: {value:.3f}")
```

PI scores describe cue intensity, not whether a claim is true and not the
probability that every audience will be persuaded.

## 3. Understand resource coverage

Check the environment before interpreting dimension means:

```bash
persuasion-index doctor
```

The base installation is useful for trying PI and for analyses that need only
the bundled features. It always returns the same 55-subfeature and 15-dimension
schema, even when optional resources are absent. Stable shape does not mean
identical feature coverage:

- NER-dependent features are `0.0` without spaCy and `en_core_web_sm`.
- LIWC-derived feature components are `0.0` without a configured licensed
  dictionary.
- NRC-VAD valence, arousal, and dominance are `0.0` without NRC-VAD.
- Lexical concreteness uses the available ratings source, or a neutral `0.5`
  fallback when neither source is configured.

Each dimension `mean` is the unweighted mean of its defined subfeatures, so
these fallback values affect the result. For example, a text can have a strong
VADER sentiment score but a modest overall Sentiment mean when LIWC and NRC-VAD
features are unavailable.

For meaningful comparisons, score every text with the same:

- PI package version;
- `expanded` or `seeded` lexicon choice;
- optional-resource configuration;
- preprocessing procedure.

Inspect relevant subfeatures alongside dimension means, especially in a base
installation. Use `strict_resources=True` only when the analysis requires the
complete optional feature configuration.

Use the original seeded lexicons for comparisons with earlier experiments:

```python
seeded_scores = score(text, lexicon="seeded")
expanded_scores = score(text, lexicon="expanded")
```

Record the selected lexicon in papers and analysis artifacts. The expanded,
audited lexicons are the default.

## 4. Analyze a list of texts

```python
from persuasion_index import score_batch

texts = [
    "This action is urgent.",
    "The available evidence remains mixed.",
]

subfeatures, dimensions = score_batch(texts)

print(subfeatures.shape)  # (2, 55)
print(dimensions.shape)   # (2, 15)
```

Both outputs are pandas DataFrames. Subfeature columns use names such as
`Evidence.statistical`; dimension columns use names such as `Evidence.mean`.

## 5. Analyze a DataFrame

```python
import pandas as pd
from persuasion_index import score_batch

data = pd.DataFrame(
    {
        "document_id": ["a", "b"],
        "text": [
            "This action is urgent.",
            "The available evidence remains mixed.",
        ],
    }
).set_index("document_id")

subfeatures, dimensions = score_batch(data, text_col="text")

analysis = data.join(dimensions).join(subfeatures)
analysis.to_csv("pi_scores.csv")
```

PI preserves the DataFrame index, so document identifiers can be joined back
onto the results without relying on row order alone. Missing text values are
treated as empty strings and receive an all-zero 15-dimension/55-subfeature
row. Empty, whitespace-only, punctuation-only, and emoji-only strings follow
the same contract.

If an analysis requires every optional feature resource, reject an incomplete
configuration explicitly:

```python
subfeatures, dimensions = score_batch(
    data,
    text_col="text",
    strict_resources=True,
)
```

## 6. Generate the UKP-weighted research profile

```python
from persuasion_index import get_report

raw_scores, ukp_profile = get_report(
    "This proposal is practical and evidence-based."
)
```

The first object contains descriptive PI features. The second applies stored
logistic-regression coefficients estimated from UKP data. Its probability is a
UKP-oriented model output, not a universal probability that the text will
persuade a particular person or audience.

For general descriptive analysis, report the raw 15-dimension or 55-subfeature
representation. Use the UKP profile only when its empirical context is relevant
and identify it explicitly in the methods section.

## 7. Configure optional resources

Resource paths are configured through environment variables:

```bash
export PI_LIWC_FILE=/absolute/path/to/LIWC.dic
export PI_CONCRETENESS_FILE=/absolute/path/to/concreteness.tsv
export PI_MWE_CONCRETENESS_FILE=/absolute/path/to/mwe_concreteness.csv
export PI_NRC_VAD_FILE=/absolute/path/to/nrc_vad.tsv
```

PI does not download these resources. Obtain each resource from the official
source, review its terms, and keep it outside Git. In particular, LIWC requires
a valid license and NRC-VAD prohibits redistribution.

Inspect the current environment before starting an analysis:

```bash
persuasion-index doctor
persuasion-index doctor --strict
persuasion-index doctor --json > pi-resource-manifest.json
```

The JSON output includes resource availability, installed versions, source
links, license notes, configured paths, and SHA256 hashes for local files.

Warnings about absent optional resources make partial feature coverage visible.
After recording the configuration, suppress repeated warnings when a minimal
configuration is deliberate:

```bash
export PI_QUIET_OPTIONAL_WARNINGS=1
```

## 8. Export and reproduce an analysis

For a typical DataFrame analysis, save dimension means, subfeatures, and the
resource manifest together:

```python
subfeatures.to_csv("pi-subfeatures.csv")
dimensions.to_csv("pi-dimensions.csv")
```

```bash
persuasion-index doctor --json > pi-resource-manifest.json
python -m pip freeze > requirements-lock.txt
```

These files answer three different questions: what PI returned, which optional
features were available, and which package versions produced the result.

## 9. Reproducibility checklist

For an academic analysis, record:

- the `persuasion-index` package version;
- Python and dependency versions;
- seeded or expanded lexicons;
- which optional resources were available;
- the resource-file SHA256 hashes reported by `persuasion-index doctor --json`;
- the spaCy model name and version, if used;
- whether results use 55 subfeatures, 15 dimension means, or the UKP profile;
- preprocessing applied before PI scoring;
- the number and handling of empty or missing texts.

PI scores describe rhetorical cues encoded in a text. They do not verify facts,
prove logical validity, or measure a context-free probability of persuasion.

## 10. Troubleshooting

### The first command is slow

The first real scoring call imports pandas, NumPy, and the scorer. Later calls
in the same process are usually much faster. `persuasion-index --version` does
not load the scoring stack as of `0.2.0rc5`.

### NumPy reports `_ARRAY_API not found`

The active environment contains a compiled package built for a different NumPy
major version. Create a clean virtual or Conda environment instead of repairing
`base` in place, then select that environment as the Jupyter kernel.

### Optional-resource warnings fill the notebook

Run `persuasion-index doctor` once, save the resource manifest, and set
`PI_QUIET_OPTIONAL_WARNINGS=1` when the missing resources are intentional.

## 11. Citation

If PI is used in academic work, cite:

> Liancheng Gong, Zhiyang Wang, Yiwei Xu, and Julia Mendelsohn. 2026.
> *Persuasion Index: A Theory-Guided Framework for Persuasion Analysis.*
> Accepted to the EMNLP 2026 Main Conference.
> [arXiv:2606.14580](https://arxiv.org/abs/2606.14580).

Copyable BibTeX and machine-readable citation metadata are available in the
repository [README](../README.md#citation) and [`CITATION.cff`](../CITATION.cff).
