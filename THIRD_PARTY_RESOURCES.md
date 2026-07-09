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
