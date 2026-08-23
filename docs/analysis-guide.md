# Persuasion Index analysis guide

Persuasion Index (PI) is a Python library for descriptive and comparative text
analysis. It extracts 55 interpretable subfeatures and aggregates them into 15
theory-guided dimensions. PI does not require a web service or an API key for
scoring.

## 1. Installation

Create an isolated environment and install the package:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install persuasion-index
```

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

Use the original seeded lexicons for comparisons with earlier experiments:

```python
seeded_scores = score(text, lexicon="seeded")
expanded_scores = score(text, lexicon="expanded")
```

Record the selected lexicon in papers and analysis artifacts. The expanded,
audited lexicons are the default.

## 3. Analyze a list of texts

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

## 4. Analyze a DataFrame

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
currently treated as empty strings.

If an analysis requires every optional feature resource, reject incomplete
configurations explicitly:

```python
subfeatures, dimensions = score_batch(
    data,
    text_col="text",
    strict_resources=True,
)
```

## 5. Generate the UKP-weighted research profile

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

## 6. Optional resources

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

Warnings about absent optional resources are intentional: they make partial
feature coverage visible. Suppress them only when a minimal configuration is a
deliberate choice:

```bash
export PI_QUIET_OPTIONAL_WARNINGS=1
```

## 7. Reproducibility checklist

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

Save an environment snapshot alongside the results:

```bash
python -m pip freeze > requirements-lock.txt
```

PI scores describe rhetorical cues encoded in a text. They do not verify facts,
prove logical validity, or measure a context-free probability of persuasion.

## 8. Citation

If PI is used in academic work, cite:

> Liancheng Gong, Zhiyang Wang, Yiwei Xu, and Julia Mendelsohn. 2026.
> *Persuasion Index: A Theory-Guided Framework for Persuasion Analysis.*
> Accepted to the EMNLP 2026 Main Conference.
> [arXiv:2606.14580](https://arxiv.org/abs/2606.14580).

Copyable BibTeX and machine-readable citation metadata are available in the
repository [README](../README.md#citation) and [`CITATION.cff`](../CITATION.cff).
