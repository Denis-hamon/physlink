# Story 1.5: PyPI Publication via OIDC

Status: done

## Story

As a maintainer,
I want to publish physlink to PyPI using OIDC Trusted Publisher without storing any credentials,
so that releases can be made securely without token rotation or secrets management overhead.

## Acceptance Criteria

1. **Given** a version tag is pushed and the CI release workflow triggers
   **When** `pypa/gh-action-pypi-publish` runs with OIDC Trusted Publisher configuration
   **Then** the package is published to PyPI without any stored API tokens or GitHub secrets
   **And** zero credentials require rotation or expiration management

2. **Given** a blank Google Colab T4 instance
   **When** I run `pip install physlink`
   **Then** installation completes in < 60 seconds (NFR-02)
   **And** `import physlink` succeeds
   **And** `physlink.__all__` exposes at minimum `doctor` and `PhysLinkError` (the symbols available after Epic 1)
   **Note:** Full 7-symbol verification (`doctor`, `ObservationSpace`, `ActionSpace`, `DreamerV3Adapter`, `register_invariant`, `ComplianceReport`, `PhysLinkError`) is deferred to Story 4.5

3. **Given** a release is published to PyPI
   **When** the release CI workflow runs
   **Then** the quickstart Colab notebook URL is tested: the notebook must reference `physlink=={released_version}` explicitly (not `pip install physlink` without a pin)
   **And** a smoke test verifies that the pinned notebook cells execute without `AttributeError` or `ImportError` against the released version

## Tasks / Subtasks

- [x] Task 1: Create `.github/workflows/publish.yml` (AC: #1, #3)
  - [x] Trigger on `push` tags matching `v*`
  - [x] Set `permissions: id-token: write` at top-level for OIDC token generation + `contents: read`
  - [x] Set `environment: pypi` to use the GitHub environment with OIDC Trusted Publisher
  - [x] Steps: `actions/checkout@v4` → `actions/setup-python@v5` (Python 3.12) → `pip install build` → `python -m build` → `pypa/gh-action-pypi-publish@release/v1`
  - [x] Add notebook pin validation step BEFORE publish: extract version from `GITHUB_REF_NAME` tag (strip `v` prefix) and `grep` for `pip install physlink=={version}` in `notebooks/quickstart.ipynb`; fail with clear error if not found
  - [x] Add post-publish smoke test step: `pip install physlink=={version}` (after PyPI propagation delay of 60s via `sleep 60`) then `python -c "import physlink; assert 'doctor' in physlink.__all__; assert 'PhysLinkError' in physlink.__all__; from physlink import doctor, PhysLinkError"`
  - [x] Do NOT add `needs: test-cpu` — publish.yml is a separate workflow; add a comment noting the maintainer must ensure CI passes before pushing a version tag (see CONTRIBUTING.md)

- [x] Task 2: Remove `@pytest.mark.skip` from `tests/integration/test_api_stability.py` (AC: #2)
  - [x] Remove line: `@pytest.mark.skip(reason="Activated by Story 1.5 once doctor and PhysLinkError are implemented")`
  - [x] Do NOT change any other line in the file — function body stays identical
  - [x] Verify: running `pytest tests/integration/test_api_stability.py -v` now shows the test as PASSED (not SKIPPED)
  - [x] The test checks `{"doctor", "PhysLinkError"}.issubset(set(physlink.__all__))` — both symbols are already exported in `src/physlink/__init__.py`

- [x] Task 3: Create `notebooks/quickstart.ipynb` (AC: #3)
  - [x] Create `notebooks/` directory at project root
  - [x] Create a minimal valid Colab-compatible `.ipynb` file with JSON structure (nbformat 4, nbformat_minor 5)
  - [x] Cell 1 (code): `!pip install physlink==0.1.0` — explicit pin matching current version in `pyproject.toml`
  - [x] Cell 2 (code): `import physlink\nphyslink.doctor()` — smoke test cell
  - [x] Cell 3 (markdown): `## Next Steps\nSee the [Lab Adoption Guide](../docs/lab-adoption-guide.md) for named-run examples.` — placeholder linking to Story 5.2 content
  - [x] Set `"metadata": {"colab": {"provenance": []}, "kernelspec": {"display_name": "Python 3", "name": "python3"}}` so Colab recognizes the runtime
  - [x] Verify notebook JSON is valid with `python3 -c "import json; json.load(open('notebooks/quickstart.ipynb'))"`

- [x] Task 4: Add OIDC setup instructions to `CONTRIBUTING.md` (AC: #1)
  - [x] Append a new section `## PyPI Publication (OIDC Trusted Publisher)` to the existing `CONTRIBUTING.md`
  - [x] Document the one-time PyPI setup: maintainer must register a Trusted Publisher on PyPI (Settings → Publishing → Add a new pending publisher) with: owner=`<owner>`, repository=`physlink`, workflow=`publish.yml`, environment=`pypi`
  - [x] Document the release process: (1) update `notebooks/quickstart.ipynb` pin to the new version, (2) update `pyproject.toml` version, (3) commit + push tag `v{version}`, (4) CI test-cpu validates → publish.yml triggers automatically
  - [x] Document that `id-token: write` permission is required on the GitHub Actions workflow level (already in publish.yml)

- [x] Task 5: Verify all ACs
  - [x] `pytest tests/integration/test_api_stability.py -v` → 1 PASSED (no longer skipped)
  - [x] `pytest -m "not gpu" tests/ -v` → all tests pass including test_api_stability
  - [x] `ruff check src/` → 0 issues
  - [x] `mypy --strict src/physlink/core/` → 0 issues
  - [x] `python3 -c "import json; json.load(open('notebooks/quickstart.ipynb'))"` → valid JSON
  - [x] `cat .github/workflows/publish.yml | grep "id-token: write"` → present
  - [x] `cat .github/workflows/publish.yml | grep "pypa/gh-action-pypi-publish"` → present

## Dev Notes

### File 1: `.github/workflows/publish.yml` — CREATE

This file does NOT exist yet. `.github/` directory already exists from Story 1.4.

**Full implementation:**

```yaml
name: Publish

on:
  push:
    tags: ['v*']

permissions:
  contents: read
  id-token: write  # Required for OIDC token generation — cannot be narrowed further

jobs:
  publish:
    name: Build and publish to PyPI
    runs-on: ubuntu-latest
    environment: pypi  # GitHub Actions environment linked to PyPI Trusted Publisher

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Validate notebook version pin
        run: |
          VERSION=$(echo "$GITHUB_REF_NAME" | sed 's/^v//')
          echo "Validating notebooks/quickstart.ipynb pin for physlink==${VERSION}"
          if ! grep -q "pip install physlink==${VERSION}" notebooks/quickstart.ipynb; then
            echo "ERROR: notebooks/quickstart.ipynb must reference 'pip install physlink==${VERSION}'"
            echo "  Got:      $(grep 'pip install physlink' notebooks/quickstart.ipynb || echo 'no pip install physlink line found')"
            echo "  Expected: pip install physlink==${VERSION}"
            echo "  Fix:      update notebooks/quickstart.ipynb cell 1 to '!pip install physlink==${VERSION}' before pushing tag"
            exit 1
          fi
          echo "OK: notebook pin matches release version"

      - name: Install build dependencies
        run: pip install build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # No with.password or with.user — OIDC Trusted Publisher handles auth automatically

      - name: Smoke test — verify PyPI install
        run: |
          VERSION=$(echo "$GITHUB_REF_NAME" | sed 's/^v//')
          echo "Waiting 60s for PyPI to propagate physlink==${VERSION}..."
          sleep 60
          pip install "physlink==${VERSION}"
          python -c "
          import physlink
          assert 'doctor' in physlink.__all__, f'doctor missing from __all__: {physlink.__all__}'
          assert 'PhysLinkError' in physlink.__all__, f'PhysLinkError missing from __all__: {physlink.__all__}'
          from physlink import doctor, PhysLinkError
          print(f'OK: physlink=={\"$VERSION\"} smoke test passed — doctor and PhysLinkError importable')
          "
```

**Key design decisions:**
- `id-token: write` is the minimum OIDC permission needed; it is required at the workflow level (not job level) because `pypa/gh-action-pypi-publish` exchanges the token with PyPI.
- `environment: pypi` references the GitHub Actions environment where the OIDC Trusted Publisher is configured. The maintainer must create this environment on GitHub (Settings → Environments → pypi) and configure PyPI to trust it (one-time setup, documented in CONTRIBUTING.md).
- The notebook pin validation runs BEFORE the build, so a misconfigured notebook fails fast without building or publishing anything.
- `sleep 60` before smoke test: PyPI CDN propagation typically takes 30-90 seconds after publication. 60s is a reasonable default; if it fails with "package not found", the publish already succeeded — this is a best-effort post-publish check.
- No `needs: test-cpu` in publish.yml: GitHub Actions does not support cross-workflow `needs`. The release process (documented in CONTRIBUTING.md) requires the maintainer to verify CI passes before pushing the tag.
- `pypa/gh-action-pypi-publish@release/v1` — use the floating `release/v1` ref (PyPA's recommended form) which tracks the latest stable v1.x release. This is the canonical form used in PyPA's own documentation.

### File 2: `tests/integration/test_api_stability.py` — SURGICAL CHANGE

**Current state (Story 1.4 left it with):**
```python
@pytest.mark.skip(reason="Activated by Story 1.5 once doctor and PhysLinkError are implemented")
def test_epic1_api_symbols() -> None:
    import physlink

    expected = {"doctor", "PhysLinkError"}
    actual = set(physlink.__all__)
    assert expected.issubset(actual), f"Missing Epic 1 symbols: {expected - actual}"
```

**Change required:** Remove ONLY the `@pytest.mark.skip(...)` decorator line. Nothing else.

**After change:**
```python
def test_epic1_api_symbols() -> None:
    import physlink

    expected = {"doctor", "PhysLinkError"}
    actual = set(physlink.__all__)
    assert expected.issubset(actual), f"Missing Epic 1 symbols: {expected - actual}"
```

**Why this passes immediately:** `src/physlink/__init__.py` already exports both `PhysLinkError` and `doctor` in `__all__`:
```python
__all__ = [
    "PhysLinkError",
    "doctor",
    # Story 2.2/2.3: ObservationSpace, ActionSpace
    # Story 3.1: DreamerV3Adapter
    # Story 4.3/4.4: register_invariant, ComplianceReport
]
```

**Test count impact:** After this change, `pytest -m "not gpu" tests/ -v` will show this test as PASSED instead of SKIPPED. Total skipped count drops from 3 to 2 (the 2 `TestSrcLayoutEnforcement` methods still skip when editable install is present).

### File 3: `notebooks/quickstart.ipynb` — CREATE

**Location:** `notebooks/quickstart.ipynb` (new `notebooks/` directory at project root)

**Full content (valid nbformat 4 JSON):**

```json
{
  "nbformat": 4,
  "nbformat_minor": 5,
  "metadata": {
    "colab": {
      "provenance": []
    },
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "version": "3.12.0"
    }
  },
  "cells": [
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "!pip install physlink==0.1.0"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "import physlink\n",
        "physlink.doctor()"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "## Next Steps\n",
        "\n",
        "- [Lab Adoption Guide](../docs/lab-adoption-guide.md) — named-run examples, TrajectoryBuffer persistence, BibTeX citation\n",
        "- [Domain Scientists Guide](../docs/domain-scientists.md) — register_invariant() with mass_conservation example"
      ]
    }
  ]
}
```

**Why explicit pin `==0.1.0`:** The publish.yml workflow validates that the notebook pin matches the release tag version. When preparing a new release (e.g., `v0.2.0`), the maintainer updates this cell to `!pip install physlink==0.2.0` before pushing the tag. The CI notebook pin check enforces this.

### File 4: `CONTRIBUTING.md` — APPEND SECTION

The existing `CONTRIBUTING.md` (created by Story 1.4) covers GPU test protocol and RC process. Append a new section at the end:

```markdown
## PyPI Publication (OIDC Trusted Publisher)

### One-Time PyPI Setup

Before the first release, configure a Trusted Publisher on PyPI:
1. Log in to pypi.org → project settings → Publishing → Add a new pending publisher
2. Enter:
   - Owner: `<github-username-or-org>`
   - Repository: `physlink`
   - Workflow filename: `publish.yml`
   - Environment name: `pypi`
3. Create the matching GitHub Actions environment: repository Settings → Environments → New environment → name: `pypi`

No credentials are stored — PyPI validates the OIDC token from GitHub Actions automatically.

### Release Process

For each release:
1. Update `notebooks/quickstart.ipynb` cell 1 to `!pip install physlink==X.Y.Z`
2. Update `version = "X.Y.Z"` in `pyproject.toml`
3. Update `CHANGELOG.md` with the release entry (`## [X.Y.Z] - YYYY-MM-DD`)
4. Commit all changes: `git commit -m "chore: release vX.Y.Z"`
5. Push the tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
6. `publish.yml` triggers automatically — notebook pin is validated, package is built and published, smoke test confirms the install works

**Important:** Ensure `test-cpu` CI passes on the release commit before pushing the tag.
```

### Architecture Boundaries This Story Must Respect

| Rule | How to comply |
|------|--------------|
| `test_api_stability.py` skip removed | Remove `@pytest.mark.skip` only — do NOT change the test logic |
| `physlink.__all__` already correct | `src/physlink/__init__.py` already exports `PhysLinkError` and `doctor` — do NOT modify it |
| `ci.yml` untouched | `publish.yml` is a separate workflow; do NOT add publish steps to `ci.yml` |
| `pyproject.toml` version unchanged | Do NOT change the version number — this story sets up the infrastructure, not the first release itself |
| No credentials in workflow YAML | `pypa/gh-action-pypi-publish` uses OIDC automatically; no `with.password` or secrets |
| `id-token: write` at workflow level | Required by OIDC — cannot be at job level for this action |

### What NOT to Implement in This Story

- Removing the `# Story 2.2/2.3: ...` comments in `src/physlink/__init__.py` — those are accurate stubs for future epics
- Changing `pyproject.toml` version from `0.1.0` — version bump happens at actual release time
- Full 7-symbol `test_api_stability.py` verification — deferred to Story 4.5 which adds a separate test or updates this one
- README "Open in Colab" button linking to the notebook — Story 1.6
- `CHANGELOG.md` entry for v0.1.0 — Story 5.1 establishes the CHANGELOG format
- `pypa/gh-action-pypi-publish@release/v1` `with.skip-existing: true` — not needed; version tag discipline handles this

### Previous Story Intelligence

Critical learnings from Stories 1.1–1.4:

- **Module docstring order:** docstring FIRST, then blank line, then `from __future__ import annotations`. Not applicable to YAML/JSON files.
- **Commit format:** `feat(story-X.Y): Short Description` — use `feat(story-1.5): PyPI Publication via OIDC`.
- **`test_api_stability.py` skip:** Story 1.4 explicitly documented "Removing `@pytest.mark.skip` from `test_api_stability.py` — Story 1.5 activates this". Confirmed: the skip reason string mentions "Story 1.5" directly.
- **pytest-benchmark `benchmark.stats.stats.mean`:** Not relevant to this story (no new benchmark tests).
- **`TestSrcLayoutEnforcement` still skips:** The 2 tests in `test_toolchain_compliance.py` will still skip when editable install is present. This is expected — do NOT attempt to fix them in this story.
- **`ruff` excludes `.agents/`, `.claude/`, `_bmad/`, `_bmad-output/`:** The `notebooks/` directory is NOT excluded. If the notebook contained Python source, ruff might flag it. Notebooks are JSON, not `.py` files — ruff will ignore them by default (it only lints `.py` files unless `--include` specifies `.ipynb`).
- **`pyproject.toml` has no notebooks path in ruff `exclude`:** Not needed — ruff doesn't lint `.ipynb` by default.

### Git Intelligence

Most recent commits:
- `18f6092 feat(story-1.4): GitHub Actions CI Pipeline`
- `ad8868c feat(story-1.3): PhysLink Doctor Diagnostic Scan`
- `1f7b259 feat(story-1.2): Exception Hierarchy Foundation`

Patterns established:
- Commit message format: `feat(story-X.Y): Title Case Description`
- No `@pytest.mark.skip` left in integration tests once the guarded feature is implemented

### Project Structure Notes

| File | Action | Notes |
|------|--------|-------|
| `.github/workflows/publish.yml` | **NEW** | OIDC workflow; `.github/workflows/` already exists |
| `tests/integration/test_api_stability.py` | **UPDATE** (remove 1 line) | Remove `@pytest.mark.skip(...)` decorator only |
| `notebooks/quickstart.ipynb` | **NEW** | Create `notebooks/` directory + notebook file |
| `CONTRIBUTING.md` | **UPDATE** (append section) | Add PyPI OIDC setup + release process |
| `src/physlink/__init__.py` | **DO NOT TOUCH** | Already has correct `__all__` exports |
| `pyproject.toml` | **DO NOT TOUCH** | Version stays `0.1.0` |
| `.github/workflows/ci.yml` | **DO NOT TOUCH** | Separate workflow — no changes needed |
| `tests/perf/baselines/benchmark_baseline.json` | **DO NOT TOUCH** | Immutable baseline |
| All `src/physlink/` source files | **DO NOT TOUCH** | No source changes needed for this story |

### References

- AR-04 (PyPI OIDC Trusted Publisher spec): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- NFR-02 (`pip install physlink` < 60s): [Source: _bmad-output/planning-artifacts/epics.md#NonFunctional Requirements]
- Architecture publish.yml location: [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- Architecture CI/CD flow: [Source: _bmad-output/planning-artifacts/architecture.md#Integration Points — CI/CD]
- Story 1.4 "What NOT to Implement" — publish.yml and test_api_stability.py skip removal: [Source: _bmad-output/implementation-artifacts/1-4-github-actions-ci-pipeline.md#Dev Notes]
- `test_api_stability.py` skip reason: [Source: tests/integration/test_api_stability.py#L13]
- `pypa/gh-action-pypi-publish` canonical usage: https://docs.pypi.org/trusted-publishers/using-a-publisher/

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_No blockers encountered._

### Completion Notes List

- ✅ Task 1: `.github/workflows/publish.yml` créé avec OIDC Trusted Publisher, validation du pin notebook avant build, smoke test post-publication avec `sleep 60` pour la propagation PyPI.
- ✅ Task 2: Suppression du `@pytest.mark.skip` dans `tests/integration/test_api_stability.py` — le test passe immédiatement car `doctor` et `PhysLinkError` sont déjà exportés dans `__all__`.
- ✅ Task 3: `notebooks/quickstart.ipynb` créé (nbformat 4, compatible Colab) avec pin explicite `physlink==0.1.0`, cellule smoke test, cellule markdown Next Steps.
- ✅ Task 4: Section `## PyPI Publication (OIDC Trusted Publisher)` ajoutée à `CONTRIBUTING.md` avec setup PyPI one-time et release process.
- ✅ Task 5: Toutes les vérifications passent — 119 passed, 2 skipped (expected), ruff 0 issues, mypy 0 issues, JSON notebook valide.
- 🔧 Review fix: `publish.yml` smoke test corrigé — `physlink.__version__` remplacé par `$VERSION` (shell variable) car `__version__` n'est pas défini dans `__init__.py`.

### File List

- `.github/workflows/publish.yml` — NEW: workflow de publication PyPI via OIDC Trusted Publisher
- `tests/integration/test_api_stability.py` — MODIFIED: suppression du `@pytest.mark.skip`
- `tests/integration/test_publish_workflow_config.py` — NEW: 38 tests validant publish.yml, notebook et CONTRIBUTING.md
- `notebooks/quickstart.ipynb` — NEW: notebook Colab quickstart avec pin `physlink==0.1.0`
- `CONTRIBUTING.md` — MODIFIED: ajout section `## PyPI Publication (OIDC Trusted Publisher)`

## Change Log

- 2026-05-22: feat(story-1.5): PyPI Publication via OIDC — création du workflow publish.yml (OIDC Trusted Publisher), activation du test API stability, création du notebook quickstart.ipynb, documentation release process dans CONTRIBUTING.md.
- 2026-05-22: review(story-1.5): fix smoke test — `physlink.__version__` → `$VERSION` (AttributeError, module has no attribute '__version__'); ajout test_publish_workflow_config.py au File List.
