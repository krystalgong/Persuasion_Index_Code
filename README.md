# Persuasion Index

Persuasion Index (PI) is a Python toolkit for asking a simple question: **what
persuasive moves does a text make?** It breaks English argumentative text into
55 inspectable signals and groups them into 15 rhetorical dimensions.

This repository accompanies **Persuasion Index: A Theory-Guided Framework for
Persuasion Analysis**, accepted to the **EMNLP 2026 Main Conference**. The
current paper is available on [arXiv](https://arxiv.org/abs/2606.14580).

## Quick start: choose how you want to use PI

Both options provide the same command-line and Python interfaces. Choose the
first if you only want to run PI. Choose the second if you want to inspect or
change how individual features are computed.

### Option 1: install the package without cloning the repository

This is the simplest route for analysis. pip installs PI and its required
dependencies from PyPI.

#### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install persuasion-index
```

In a Jupyter notebook, use `%pip` in place of `python -m pip`, then restart the
kernel.

#### Run

Score a text from the command line:

```bash
persuasion-index \
  "According to recent studies, this policy could reduce costs by 20%."
```

Or use the Python API:

```python
from persuasion_index import score

scores = score(
    "According to recent studies, this policy could reduce costs by 20%."
)
print(scores["Evidence"])
```

No repository checkout, web service, or API key is needed.

### Option 2: clone the repository to inspect or change modules

Use an editable install if you want to read the implementation, replace a
feature detector, modify a lexicon, or contribute code.

#### Install for development

```bash
git clone https://github.com/krystalgong/Persuasion_Index_Code.git
cd Persuasion_Index_Code
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,notebooks]"
```

#### Run and modify

Use the same `persuasion-index` command or Python API shown above. Because the
installation is editable, saved source changes are used the next time the code
runs; reinstalling the package is not necessary.

The main places to start are:

- `PI_score_generator.py` for individual feature implementations.
- `persuasion_runner.py` for string, list, and DataFrame scoring.
- `persuasion_index/api.py` for the public Python interface.
- `helper_features/` for the bundled lexicons and stored coefficients.

After a change, run the automated tests:

```bash
python -m pytest -q
```

See the [repository map](#repository-map) for the rest of the codebase.

That is enough to start in either mode. A few features can use additional
linguistic resources; the base package still runs when those resources are
absent.

For a complete first analysis—from checking resource coverage to exporting a
DataFrame—see the [usage and analysis guide](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/docs/analysis-guide.md).

## What PI returns

PI organizes its dimensions around the Aristotelian triad:

| Appeal | Dimensions |
|---|---|
| **Logos** | Evidence, Logic/Cohesion, Argumentation, Specificity, Opponent’s View |
| **Ethos** | Authority/Credibility, Politeness, Commitment, Style |
| **Pathos** | Sentiment, Impact, Engagement, Reciprocity, Scarcity/Urgency, Propaganda |

Every subfeature and dimension score is in `[0, 1]`. A result contains all 55
subfeatures as well as the mean for each of the 15 dimensions, so it is possible
to inspect why two texts receive different profiles.

Before comparing dimension means, run `persuasion-index doctor`. Missing
optional resources keep the output schema stable, but their fallback values
still affect the means. Compare texts only when they were scored with the same
PI version, lexicon choice, and resource configuration; the
[usage guide](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/docs/analysis-guide.md#3-understand-resource-coverage) explains this with examples.

## Installation notes

PI supports Python 3.10 and newer. Python 3.11 or 3.12 is recommended. If you
also plan to run the lexicon-expansion pipeline from a cloned repository,
install its dependencies with:

```bash
python -m pip install -e ".[lexicon,notebooks,dev]"
```

Version `0.3.0` was promoted from the tested `0.3.0rc1` package without
additional scoring changes. The
[acceptance checklist](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/docs/0.3.0rc1-testing.md)
records the TestPyPI installation and notebook checks used before release.

## Optional features

The bundled lexicons and lightweight detectors work immediately. The resources
below add the remaining features:

| Resource | Features it adds | Setup |
|---|---|---|
| spaCy `en_core_web_sm` | Named entities and organization mentions | Install spaCy, then run `python -m spacy download en_core_web_sm` |
| Single-word concreteness ratings | `Specificity.lexical_concreteness` | Set `PI_CONCRETENESS_FILE` |
| Multiword concreteness ratings | `Specificity.lexical_concreteness` | Set `PI_MWE_CONCRETENESS_FILE` |
| LIWC-compatible dictionary | LIWC cues used by Specificity, Sentiment, and Engagement | Set `PI_LIWC_FILE` to a compatible, locally licensed `.dic` file |
| NRC-VAD v2.1 | `Sentiment.valence`, `Sentiment.arousal`, and `Sentiment.dominance` | Set `PI_NRC_VAD_FILE` |

Example configuration:

```bash
python -m pip install "spacy>=3.7" "openpyxl>=3.1"
python -m spacy download en_core_web_sm

export PI_CONCRETENESS_FILE=/absolute/path/to/concreteness_ratings.xlsx
export PI_MWE_CONCRETENESS_FILE=/absolute/path/to/mwe_concreteness.csv
export PI_LIWC_FILE=/absolute/path/to/LIWC.dic
export PI_NRC_VAD_FILE=/absolute/path/to/nrc_vad.tsv
```

From an editable source checkout, install the corresponding extras with:

```bash
python -m pip install -e ".[spacy,excel]"
```

Run the resource checker to see what is active and which features are affected:

```bash
persuasion-index doctor
```

Missing resources produce warnings but do not stop ordinary scoring. If that is
the configuration you intend to use, you can silence those warnings with
`PI_QUIET_OPTIONAL_WARNINGS=1`.

Download links, expected file columns, citations, and license notes live in
[THIRD_PARTY_RESOURCES.md](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/THIRD_PARTY_RESOURCES.md). These external files are
not included in the package.

## Python usage

### Score several texts

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

### Score a DataFrame

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

PI preserves the DataFrame index, which makes it easy to join scores back to
document IDs and other metadata.

### Use the UKP-weighted profile

```python
from persuasion_index import get_report

raw_scores, ukp_profile = get_report(
    "This proposal is practical and evidence-based."
)
```

The raw scores describe the text directly. The optional weighted profile uses
coefficients estimated on UKP data and is most useful when that empirical
context matches the analysis.

The expanded, audited lexicons are used by default. For comparisons with the
original seed lexicons, pass `lexicon="seeded"` to `score`, `score_batch`, or
`get_report`.

To use a custom lexicon for one call, pass its path explicitly:

```python
custom_scores = score(text, lexicon_file="/absolute/path/to/custom.json")
```

The CLI equivalent is:

```bash
persuasion-index --lexicon-file /path/to/custom.json "Text to score"
```

If neither `lexicon_file` nor `lexicon` is passed, PI honors `PI_LEXICON_FILE`
when it is set and otherwise uses the expanded lexicon. Explicit arguments take
precedence and PI does not rewrite the environment variable. Lexicon choices
are isolated across concurrent scoring calls.

For more examples, output details, and a reproducibility checklist, see the
[analysis guide](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/docs/analysis-guide.md).

## Command line

The CLI accepts text as an argument or through standard input:

```bash
persuasion-index "This plan is urgent."
echo "This plan is urgent." | persuasion-index --profile
```

Useful commands:

```bash
persuasion-index --version
persuasion-index doctor
persuasion-index doctor --json
```

Use `--compact` for single-line JSON and `--profile` to include the
UKP-weighted profile.

## How scoring works

Most lexical cues are counted per 100 tokens and passed through a saturating
transform:

```text
score = 1 - exp(-0.5 * r)
```

Here, `r` is the match rate per 100 tokens. Sparse signals use binary
presence/absence scores. When lexicon matches overlap, PI keeps the longest
non-contained span. A dimension score is the unweighted mean of its
subfeatures.

PI preserves input capitalization for case-sensitive components such as
APA-style citations, spaCy NER, and VADER emphasis. Case-insensitive lexical
features normalize text inside their own detector. Overlapping number and
percentage matches, such as the `20` inside `20%`, count as one quantitative
expression.

PI measures rhetorical cues rather than whether a claim is true or whether a
particular audience will ultimately be persuaded. For example, Evidence finds
statistics, attribution phrases, and named entities; it does not fact-check
them. Keeping that distinction in mind makes the scores much easier to
interpret.

## Repository map

- `persuasion_index/`: public Python API and CLI.
- `PI_score_generator.py`: individual feature implementations.
- `persuasion_runner.py`: string, list, and DataFrame scoring.
- `persuasion_profile.py`: raw scores and the UKP-weighted profile.
- `helper_features/`: bundled PI lexicons and stored UKP coefficients.
- `analysis_example.ipynb`: a short analysis walkthrough.
- `lexicons/`: lexicon expansion and validation code.
- `docs/`: the analysis guide and release documentation.

The repository focuses on scoring, interpretation, and lexicon construction.
The evaluation datasets used in the paper are not bundled here.

## Notebooks and development

`analysis_example.ipynb` demonstrates the public API, seeded versus expanded
lexicons, DataFrame scoring, and weighted reports. The validation notebook at
`lexicons/lexicons_validation/lexicon_code_validation.ipynb` exercises scoring
behavior and split-half lexicon checks.

Run the package tests with:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

The full release checklist is in
[docs/testing-and-release.md](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/docs/testing-and-release.md). The LLM-assisted
expansion pipeline has its own instructions in
[lexicons/LLM_expansion/README.md](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/lexicons/LLM_expansion/README.md).

## Scope and limitations

PI currently works best on English argumentative text. It sees the text itself,
not the audience, speaker reputation, relationship history, or broader social
setting. It will also miss some implicit framing, irony, sarcasm, and long-range
argument structure.

Treat PI scores as interpretable features for describing and comparing texts,
not as a universal probability of persuasion. When applying PI in a new domain,
we recommend looking at score distributions and reading representative
high-scoring and low-scoring examples before drawing conclusions.

## Citation

If you use Persuasion Index in academic work, please cite our paper:

> Liancheng Gong, Zhiyang Wang, Yiwei Xu, and Julia Mendelsohn. 2026.
>
> *Persuasion Index: A Theory-Guided Framework for Persuasion Analysis.*
>
> Accepted to the EMNLP 2026 Main Conference.
>
> [arXiv:2606.14580](https://arxiv.org/abs/2606.14580).

```bibtex
@misc{gong2026persuasionindex,
  title         = {Persuasion Index: A Theory-Guided Framework for Persuasion Analysis},
  author        = {Gong, Liancheng and Wang, Zhiyang and Xu, Yiwei and Mendelsohn, Julia},
  year          = {2026},
  eprint        = {2606.14580},
  archiveprefix = {arXiv},
  primaryclass  = {cs.CL},
  doi           = {10.48550/arXiv.2606.14580},
  note          = {Accepted to the EMNLP 2026 Main Conference},
  url           = {https://arxiv.org/abs/2606.14580}
}
```

Machine-readable citation metadata is available in
[CITATION.cff](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/CITATION.cff). We will replace the arXiv entry with the ACL
Anthology citation when the proceedings are published.

## License

Project code, documentation, and project-created PI lexicons are released under
the [Apache License 2.0](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/LICENSE). External resources keep their own terms; see
[THIRD_PARTY_RESOURCES.md](https://github.com/krystalgong/Persuasion_Index_Code/blob/main/THIRD_PARTY_RESOURCES.md) for details.
