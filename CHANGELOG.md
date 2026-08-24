# Changelog

All notable changes to Persuasion Index are documented here. Versions follow
PEP 440 and semantic-versioning conventions.

## [Unreleased]

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

[Unreleased]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc7...HEAD
[0.2.0rc7]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc6...v0.2.0rc7
[0.2.0rc6]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc5...v0.2.0rc6
[0.2.0rc5]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc4...v0.2.0rc5
[0.2.0rc4]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc3...v0.2.0rc4
[0.2.0rc3]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc2...v0.2.0rc3
[0.2.0rc2]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.2.0rc1...v0.2.0rc2
[0.2.0rc1]: https://github.com/krystalgong/Persuasion_Index_Code/compare/v0.1.0...v0.2.0rc1
