# Third-party resources and release notes

The Persuasion Index scorer uses several helper resources. Some are project-specific lexicons, and some come from external datasets or NLP tools. This file is meant to make the release easier to audit; it is not a legal opinion.

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
| Brysbaert concreteness ratings | Lexical concreteness | Keep citation/provenance with the manuscript and confirm redistribution rights before public archival. |
| Multiword-expression concreteness ratings | Phrase-level concreteness | Keep citation/provenance with the manuscript and confirm redistribution rights before public archival. |
| LIWC-style dictionary (`helper_features/en_liwc.txt`) | Pronouns, affect, tense, perception, and related categories | Verify that this file is redistributable. If it is derived from proprietary LIWC resources, replace it with a redistributable alternative before public release. |
| ConvoKit politeness marker files | Politeness cues | Keep source attribution and confirm redistribution terms. |
| NRC-VAD Lexicon v2.1 | Valence, arousal, dominance sentiment subfeatures | Not bundled. Users should download it from the official NRC-VAD page into `helper_features/` for local non-commercial research/educational use. The official terms include a no-redistribution condition. The scorer can run without NRC-VAD, but VAD subfeatures will fall back to `0.0`. |

## Recommended public-release handling

For anonymous review, the repository should be clean of author-identifying information and secrets. For a later public archival release, the resource layer should be made stricter:

- Keep project-created lexicons in the repository.
- Replace non-redistributable third-party data with official download instructions and checksums.
- Add a setup script that verifies expected external files under `helper_features/`.
- Add citations for every external resource in the manuscript and in this file.
- Do not apply a single repository license to third-party resources unless their licenses explicitly allow it.
