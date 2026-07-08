# Third-party resources

The Persuasion Index scorer combines project-specific lexicons with external datasets and NLP tools. This page summarizes how those resources are used and which ones require separate installation.

## Project-specific resources

| Path | Role | Notes |
|---|---|---|
| `helper_features/lexicons.json` | Seed PI lexicons | Paper-specific seed lexicons. |
| `helper_features/lexicons_expanded_LLM_audited.json` | Default expanded PI lexicons | Final flat lexicon used by the scorer unless `PI_LEXICON_FILE` is set. |
| `lexicons/LLM_expansion/theory_definitions.json` | Theory definitions and seed items for expansion | Used by the LLM expansion pipeline. |
| `helper_features/regression_outputs/` | UKP coefficient files | Used only by `persuasion_profile.py` for weighted profile scores. |

## External helper resources

| Resource | Current use | Release note |
|---|---|---|
| spaCy `en_core_web_sm` | English named-entity features | Installed by the user with `python -m spacy download en_core_web_sm`. |
| VADER sentiment | Sentiment polarity | Installed through `vaderSentiment` in `requirements.txt`. |
| Brysbaert concreteness ratings | Lexical concreteness | Included under `helper_features/`; retain the original citation and provenance when redistributing. |
| Multiword-expression concreteness ratings | Phrase-level concreteness | Included under `helper_features/`; retain the original citation and provenance when redistributing. |
| LIWC-style dictionary (`helper_features/en_liwc.txt`) | Pronouns, affect, tense, perception, and related categories | Used for English lexical categories. Confirm that the source terms permit redistribution before repackaging this resource elsewhere. |
| ConvoKit politeness marker files | Politeness cues | Included under `helper_features/Convokit_Politeness/`; retain source attribution when redistributing. |
| NRC-VAD Lexicon v2.1 | Valence, arousal, dominance sentiment subfeatures | Not bundled. Users should download it from the official NRC-VAD page into `helper_features/` for local non-commercial research/educational use. The official terms include a no-redistribution condition. The scorer can run without NRC-VAD, but VAD subfeatures will fall back to `0.0`. |

## Resource handling

- Keep project-created lexicons with the scorer.
- Obtain non-redistributable resources from their official sources.
- Preserve source citations and license notices for all external resources.
- Do not assume that a repository-level license overrides the terms of third-party files.
