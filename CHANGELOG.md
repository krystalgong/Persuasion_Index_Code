# Changelog

All notable changes to Persuasion Index are documented here. Versions follow
PEP 440 and semantic-versioning conventions.

## [Unreleased]

## [0.3.0] - 2026-09-01

### Changed

- Promoted `0.3.0rc1` to the final release after TestPyPI acceptance testing of
  installation, single-text and batch scoring, DataFrame input, the CLI,
  optional-resource fallbacks, LIWC validation, and custom-lexicon isolation.
- Kept the scoring formulas, output schema, and resource behavior unchanged
  from `0.3.0rc1`.

## [0.3.0rc1] - 2026-09-01

### Fixed

- Preserved capitalization through scoring so APA-style citations, spaCy NER,
  and VADER's all-caps emphasis work on the text the user supplied.
- Corrected percent-expression boundaries for ordinary forms such as `20%`,
  `3.5%`, and `20 percent`, while rejecting word-attached forms such as
  `20%rate`.
- Made LIWC dictionary and regex caches follow the configured file identity,
  including files configured or replaced after an earlier score in the same
  process.
- Made `doctor` parse LIWC files and reject unreadable, malformed, and partial
  dictionaries instead of reporting that file existence alone is sufficient.
- Stopped public scoring functions from overwriting `PI_LEXICON_FILE` and
  added an explicit `lexicon_file` argument and `--lexicon-file` CLI option.
- Isolated lexicon selection and compiled-pattern caches by lexicon file so
  concurrent seeded, expanded, and custom scoring cannot contaminate results.

### Scoring changes

- Case-sensitive components can now distinguish cased and lowercased input.
  For example, `Smith (2020)` activates `Evidence.attribution`, and VADER
  retains its emphasis boost for words such as `GREAT`.
- Overlapping number and percentage matches are counted as one quantitative
  expression; a percentage is not double-counted as both a bare number and a
  percentage.
- Correctly loaded LIWC and custom lexicon resources may activate features
  that incorrectly remained zero in `0.2.x`.

## [0.2.1] - 2026-08-24

### Changed

- Added one link to the third-party resource guide when optional-resource
  warnings first appear, without repeating the link for every missing resource
  or subsequent scoring call.

## [0.2.0] - 2026-08-23

### Added

- Published the first public PyPI release of Persuasion Index, with 55
  inspectable features grouped into 15 rhetorical dimensions.
- Included single-text, batch, DataFrame, command-line, resource-diagnostic,
  and UKP-weighted analysis interfaces.

### Changed

- Promoted `0.2.0rc7` to the final release without scoring changes.
- Replaced the TestPyPI quick start with the standard
  `python -m pip install persuasion-index` installation path.

## [0.2.0rc7] - 2026-08-23

### Changed

- Split the README quick start into a package-only path and an editable source
  path for researchers who want to inspect or replace individual modules.
- Separated installation commands from running examples and documented the
  two-step TestPyPI installation needed to resolve dependencies from PyPI.

## [0.2.0rc6] - 2026-08-23

### Fixed

- Made empty, whitespace-only, punctuation-only, and emoji-only inputs return
  an all-zero result while preserving the 15-dimension/55-subfeature schema.
- Replaced substring searches in composite Commitment and Opponent’s View
  rules with boundary-aware, text-ordered lexicon matching.
- Prevented `commit` from matching words such as `committee`.
- Removed standalone `our` as a propaganda identity cue while retaining
  identity phrases such as `our nation` and `our homeland`.

### Changed

- Documented the all-zero contract for empty and missing texts and added
  semantic regression tests for the corrected edge cases.

## [0.2.0rc5] - 2026-08-23

### Fixed

- Made the bundled expanded lexicon retain every seeded category and item,
  restoring default coverage for Opponent’s View and other affected features.
- Kept `persuasion-index --version` and a plain package import from loading
  pandas, NumPy, and the scoring stack.

### Changed

- Expanded the usage and analysis guide with resource-aware interpretation,
  TestPyPI, export, troubleshooting, and reproducibility workflows.
- Added semantic cue checks and expanded-lexicon completeness tests alongside
  the existing schema and range tests.

## [0.2.0rc4] - 2026-08-23

### Changed

- Reworked the README around a short quick start, practical examples, and a
  compact optional-feature guide.
- Moved detailed testing and third-party resource notes out of the main README.
- Listed Zhiyang Wang and Liancheng Gong as the software package authors while
  retaining the full paper author list in the preferred citation.
- Added a GitHub Actions Trusted Publishing workflow for TestPyPI release
  candidates and approved final PyPI releases.
- Added cross-platform CI, distribution auditing, and a clean wheel-install
  smoke test.
- Made README links work from both GitHub and the PyPI project page.

## [0.2.0rc3] - 2026-08-22

### Changed

- Reframed spaCy, concreteness, LIWC, and NRC-VAD as optional feature
  resources that users install or configure themselves.
- Reworded strict resource checks around the full optional feature set.
- Added affected-feature names to human-readable and JSON resource diagnostics.
- Kept licensed and non-redistributable resources out of package artifacts.

## [0.2.0rc2] - 2026-08-22

### Added

- Release and testing documentation.
- Compliance-aware `persuasion-index doctor` resource checks.
- Strict optional-resource validation for scoring functions and the CLI.
- GitHub direct-install and editable research-install instructions.

## [0.2.0rc1] - 2026-08-21

### Added

- Machine-readable citation metadata in `CITATION.cff`.
- Citation instructions for the accepted EMNLP 2026 Main Conference paper.
- A research-oriented analysis guide and reproducibility checklist.
- PyPI project links, author metadata, and discovery keywords.
- Optional `spacy`, `excel`, and combined `all` installation extras.

### Changed

- Reduced the base installation to dependencies needed by the lightweight
  scoring configuration.
- Centralized the package version in `persuasion_index/_version.py`.

### Removed

- Removed the unused `click` runtime dependency. The CLI continues to use the
  Python standard library's `argparse` module.

[Unreleased]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.3.0rc1...v0.3.0
[0.3.0rc1]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.1...v0.3.0rc1
[0.2.1]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc7...v0.2.0
[0.2.0rc7]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc6...v0.2.0rc7
[0.2.0rc6]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc5...v0.2.0rc6
[0.2.0rc5]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc4...v0.2.0rc5
[0.2.0rc4]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc3...v0.2.0rc4
[0.2.0rc3]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc2...v0.2.0rc3
[0.2.0rc2]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc1...v0.2.0rc2
[0.2.0rc1]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.1.0...v0.2.0rc1
