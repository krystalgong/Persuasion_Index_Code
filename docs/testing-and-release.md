# Testing, releasing, and version management

This document is the release checklist for the Persuasion Index Python
distribution. Publishing is performed from reviewed Git tags, not from a
developer's working directory.

## Release gates

A release candidate is ready for TestPyPI only when all of these gates pass:

1. Unit and package API tests pass.
2. The 15-dimension and 55-subfeature schemas are unchanged unless the change
   is intentional and documented.
3. All scores are finite and within `[0, 1]` for the regression corpus.
4. Repeated scoring with the same configuration is deterministic.
5. Both seeded and expanded lexicon configurations are tested.
6. Optional-resource configurations are tested with resources present and
   absent.
7. `persuasion-index doctor --strict` passes for a full-feature acceptance run.
8. A wheel and source distribution build successfully and pass `twine check`.
9. The wheel installs and runs outside the source checkout.
10. The example notebook and analysis guide have been smoke-tested.
11. The changelog, package version, citation metadata, and documentation agree.

The final PyPI release has two additional gates:

1. The exact release candidate was installed and tested from TestPyPI.
2. A human reviewer approves the protected GitHub `pypi` environment.

## Test plan

### A. Automated tests

Run in a fresh virtual environment from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

Required CI matrix:

| Operating system | Python | Required configuration |
|---|---:|---|
| Ubuntu | 3.10, 3.11, 3.12, 3.13 | Base installation |
| macOS | 3.12 | Base installation |
| Windows | 3.12 | Base installation |
| Ubuntu | 3.12 | `spacy,excel` extras plus `en_core_web_sm` |

Do not advertise a Python version in `pyproject.toml` until its CI job passes.

### B. Analysis regression tests

Maintain a small, redistribution-safe corpus containing:

- empty and whitespace-only strings;
- very short and long arguments;
- statistics and attribution cues;
- explicit logical connectives;
- positive and negative affect;
- opponent acknowledgment and refutation;
- Unicode, punctuation, URLs, and line breaks;
- missing DataFrame values and non-default indexes.

For each release, check:

- output shapes are exactly 55 subfeatures and 15 dimensions;
- feature and dimension names are stable;
- values remain in `[0, 1]`;
- output indexes match input indexes;
- seeded and expanded lexicons do not contaminate each other's results;
- score changes from the previous release are reviewed, quantified, and listed
  under `Scoring changes` in `CHANGELOG.md`.

Numerical snapshots should use a documented tolerance rather than exact binary
float equality. Unexpected score changes block the release.

### C. Optional-resource matrix

Test these configurations separately:

1. Base installation with every optional resource absent.
2. spaCy installed but `en_core_web_sm` absent.
3. spaCy with `en_core_web_sm` installed.
4. Each external dictionary configured individually.
5. All legally available external resources configured together.
6. Invalid configured paths, which must remain visible to the user.

Never put licensed resource files into public CI artifacts or the wheel.
CI should test parsers with small synthetic fixtures, not copies or excerpts of
licensed dictionaries.

### D. Distribution test

Build both standard distribution formats:

```bash
python -m build
python -m twine check dist/*
```

Inspect the artifacts and make sure no `.env`, credentials, licensed datasets,
notebooks with private data, or local paths are included.

Install the wheel into a fresh environment outside the checkout and run:

```python
import persuasion_index as pi

scores = pi.score("According to the evidence, this action is urgent.")
assert pi.__version__ == "0.2.1"
assert len(scores) == 15
assert sum(len(dimension) - 1 for dimension in scores.values()) == 55
```

Repeat the installation from the source distribution to catch files that are
present in the checkout but missing from release artifacts.

### E. Researcher acceptance test

Before the final release, one project author should analyze a small real dataset
that was not written as a unit-test fixture. Review:

- installation instructions on a clean machine or environment;
- runtime and memory on a representative batch;
- warnings for unavailable resources;
- DataFrame indexes and exported column names;
- whether high-scoring examples are qualitatively plausible;
- whether the methods and citation text are sufficient for a paper appendix.

This is the part that requires a human researcher rather than only CI.

## TestPyPI rehearsal

The `0.2.0` release was rehearsed as `0.2.0rc7` on TestPyPI. For future release
candidates, install dependencies from PyPI and PI itself from TestPyPI:

```bash
python3 -m venv .venv-testpypi
source .venv-testpypi/bin/activate
python -m pip install numpy pandas wordfreq vaderSentiment
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --no-deps \
  persuasion-index==0.2.0rc7
```

Run the distribution smoke test from a directory that is not the source
checkout. TestPyPI and PyPI are separate services and require separate account
and Trusted Publisher configuration.

## Recommended publishing workflow

Use GitHub Actions Trusted Publishing rather than storing a long-lived PyPI API
token in repository secrets.

1. Review the package branch and merge it into the canonical GitHub repository.
2. Protect `main`; require CI and code review before merge.
3. Create `testpypi` and `pypi` GitHub environments. Require manual approval for
   the `pypi` environment.
4. On TestPyPI and PyPI, register pending Trusted Publishers for the repository,
   workflow filename, and matching environment.
5. A release workflow builds the source distribution and wheel once, runs
   artifact checks, and uploads those same artifacts.
6. Tags ending in `rcN` publish only to TestPyPI.
7. A final tag such as `v0.2.0` publishes to PyPI after environment approval.
8. Create a GitHub Release from the same tag and copy the matching changelog
   section into its release notes.
9. Install the published PyPI version in a clean environment and rerun the smoke
   test.

PyPI does not allow a published filename or version to be overwritten. If an
upload is wrong, increment the version and publish a new release.

## Version policy

Persuasion Index uses PEP 440-compatible semantic versions:

| Version | Use |
|---|---|
| `0.2.0rcN` | Release candidates for TestPyPI and researcher testing |
| `0.2.0` | Final feature release |
| `0.2.1` | Backward-compatible bug or packaging fix |
| `0.3.0` | New features or intentional scoring changes before 1.0 |
| `1.0.0` | First stable scoring and output contract |
| `2.0.0` | Breaking API, feature-name, or result-schema change after 1.0 |

Before 1.0, intentional feature-definition or formula changes still require a
minor-version bump, regression analysis, and a changelog entry. A patch release
must not intentionally change existing scores.

The package version is defined once in `persuasion_index/_version.py`. For each
release, also update `CITATION.cff` and the changelog, then create a matching Git
tag prefixed with `v`.

Long-term reproducibility needs identifiers in addition to the package version:

- feature schema version;
- bundled lexicon version;
- empirical profile/model version;
- optional resource names and versions.

These identifiers should be included in exported analysis metadata before the
stable 1.0 release.

## Maintenance policy

- `main` is always releasable and protected by CI.
- Work happens on short-lived branches and enters `main` through review.
- Every user-visible change is added to `CHANGELOG.md`.
- Deprecated public functions remain available for at least one minor release
  and emit a documented warning before removal.
- Scoring changes include before/after regression summaries.
- Security and incorrect-result bugs receive a patch release promptly.
- Release tags and GitHub Releases are never moved or silently replaced.
