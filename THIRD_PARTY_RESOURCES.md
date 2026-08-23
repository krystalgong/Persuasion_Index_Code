# Third-party resources

The repository distributes project-created resources only. Third-party
dictionaries and rating datasets are not included unless redistribution
permission is clear. Users are responsible for obtaining them from their
official sources and complying with their terms.

## Project-specific resources

| Path | Role | Notes |
|---|---|---|
| `helper_features/lexicons.json` | Seed PI lexicons | Paper-specific seed lexicons. |
| `helper_features/lexicons_expanded_LLM_audited.json` | Default expanded PI lexicons | Final flat lexicon used by the scorer unless `PI_LEXICON_FILE` is set. |
| `lexicons/LLM_expansion/theory_definitions.json` | Theory definitions and seed items for expansion | Used by the LLM expansion pipeline. |
| `helper_features/regression_outputs/` | UKP coefficient files | Used only by `persuasion_profile.py` for weighted profile scores. |

## External helper resources

| Resource | Local configuration | Behavior when unavailable |
|---|---|---|
| spaCy `en_core_web_sm` | `python -m spacy download en_core_web_sm` | NER-dependent parts of `Evidence.named_entities` and `Authority/Credibility.organizations` are unavailable. |
| VADER sentiment | Installed through the package dependency `vaderSentiment` | `Sentiment.vader_compound` falls back to `0.0` if VADER cannot load. |
| [LIWC](https://www.liwc.app/download) dictionary | Obtain under a valid LIWC license and set `PI_LIWC_FILE` to the local `.dic` file. | LIWC-derived portions of affected Sentiment, Engagement, and Specificity subfeatures are unavailable. |
| [Brysbaert, Warriner, and Kuperman single-word concreteness ratings](https://biblio.ugent.be/publication/5774089) | Set `PI_CONCRETENESS_FILE` to a local `.xlsx`, `.txt`, `.tsv`, or `.csv` file with `Word` and `Conc.M` columns. | The scorer uses multiword ratings alone, or `0.5` if neither concreteness resource is available. |
| [Muraki et al. multiword-expression concreteness ratings](https://osf.io/ksypa/) | Set `PI_MWE_CONCRETENESS_FILE` to the processed summary CSV with `Expression` and `Mean_C` columns. | The scorer uses single-word ratings alone, or `0.5` if neither concreteness resource is available. |
| [NRC-VAD Lexicon v2.1](https://saifmohammad.com/WebPages/nrc-vad.html) | Download under the official terms and set `PI_NRC_VAD_FILE` to the unigram TSV file. | `Sentiment.valence`, `Sentiment.arousal`, and `Sentiment.dominance` are `0.0`. |

## Redistribution decisions

These decisions apply to the public GitHub repository, source distribution,
wheel, release artifacts, examples, tests, and CI artifacts:

| Resource | PI redistribution decision | Reason |
|---|---|---|
| spaCy `en_core_web_sm` | Not bundled; installed separately | It is a separately versioned model package. |
| Brysbaert et al. concreteness ratings | Not bundled | Redistribution permission has not been established for PI. |
| Muraki et al. MWE ratings | Not bundled | Users are directed to the authors' OSF project and its terms. |
| LIWC dictionaries | Never bundled | LIWC is licensed software and its EULA prohibits sharing or redistribution. |
| NRC-VAD | Never bundled | The provider explicitly prohibits redistribution and limits the public download to non-commercial research/educational use. |

PI does not automatically download any of these resources or accept a license
on a user's behalf. `persuasion-index doctor` reports official source links and
local configuration without copying the underlying data.

The current LIWC loader supports a legally obtained legacy `.dic` file. It does
not support LIWC-22 `.dicx`. Users must not convert, extract, or share LIWC data
in violation of their license. A future LIWC-22 integration should use the
official licensed CLI rather than parsing internal application data.

The former `helper_features/Convokit_Politeness/` marker files were not used by
the current scorer and have been removed. Current Politeness features use
project lexicons and rules from the main PI resource files.

Missing optional resources do not change the output schema: the scorer still
returns 15 dimensions and 55 subfeatures. They can change individual values,
so partial-resource output should not be treated as numerically equivalent to
the full paper configuration.

## Resource handling

- Keep project-created lexicons and derived coefficient files with the scorer.
- Store locally downloaded resources outside version control.
- Preserve source citations and license notices for every external resource.
- Do not assume that a repository-level license overrides third-party terms.
- Keep locally obtained resources outside Git and public CI.
- Record resource versions and SHA256 hashes in reproducibility artifacts.
- Use `persuasion-index doctor --strict` when an analysis requires every
  optional feature resource.
