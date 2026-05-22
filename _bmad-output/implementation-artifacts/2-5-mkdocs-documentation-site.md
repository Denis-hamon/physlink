# Story 2.5: MkDocs Documentation Site

Status: done

## Story

As a researcher evaluating PhysLink,
I want to browse API documentation on GitHub Pages with versioned docs,
so that I can find accurate reference documentation for the version I installed.

## Acceptance Criteria

1. **Given** the repository is set up with MkDocs Material + mkdocstrings[python]
   **When** `mkdocs build` is run in CI (test-cpu job)
   **Then** the documentation site builds without errors and produces a `site/` directory

2. **Given** the docs site is built
   **When** I browse the API reference section
   **Then** `ObservationSpace`, `ActionSpace`, `doctor`, and `PhysLinkError` appear in the API reference
   (Note: "all 7 physlink.__init__ exports" from the epic AC is the end state post-Story 2.6; for this story document the 4 symbols accessible now via their full module paths)

3. **Given** a commit is merged to `main`
   **When** the `Deploy Docs` GitHub Actions workflow runs
   **Then** the docs are published to GitHub Pages via `mkdocs gh-deploy`

4. **Given** the docs are deployed
   **When** a researcher reads the README
   **Then** a `[![Docs](...)]` badge is present and links to the GitHub Pages URL

## Tasks / Subtasks

- [x] Task 1: Add docs optional-dependencies to `pyproject.toml` (AC: #1)
  - [x] Add `[project.optional-dependencies] docs = [...]` group with `mkdocs-material>=9.5`, `mkdocstrings[python]>=0.25`, `mike>=2.1`
  - [x] Verify `pip install -e ".[docs]"` resolves without conflicts with existing `dev` group

- [x] Task 2: Create `mkdocs.yml` at project root (AC: #1, #2)
  - [x] Create `mkdocs.yml` with: site_name, site_url, repo_url, theme (material), plugins (search + mkdocstrings google style), nav, extra (mike version provider)
  - [x] Set `site_url` and `repo_url` using `YOUR-ORG` placeholder (consistent with README)
  - [x] Configure mkdocstrings: `docstring_style: google`, `show_source: false`

- [x] Task 3: Create `docs/` content files (AC: #1, #2)
  - [x] `docs/index.md` — home page with project description and navigation links
  - [x] `docs/getting-started.md` — DD-001: Hugo's 5-step Colab path (pip install → doctor() → ObservationSpace → ActionSpace → fit())
  - [x] `docs/domain-scientists.md` — DD-003: Samuel content (physical hallucinations, register_invariant usage preview)
  - [x] `docs/api/index.md` — API reference using mkdocstrings directives for all 4 current symbols
  - [x] `docs/changelog.md` — mirror CHANGELOG.md (link or copy)
  - [x] `docs/lab-adoption-guide.md` — DD-002: Petra evaluation guide

- [x] Task 4: Add `mkdocs build` step to CI (AC: #1)
  - [x] In `.github/workflows/ci.yml`, add a new `docs` job (parallel to `test-cpu`, no `needs:` dependency)
  - [x] Job steps: checkout, setup-python 3.12, `pip install -e ".[docs]"`, `mkdocs build --strict`
  - [x] The `--strict` flag turns warnings into errors (broken nav links, missing pages)

- [x] Task 5: Create `.github/workflows/docs.yml` GitHub Pages deploy workflow (AC: #3)
  - [x] Trigger: `push` to `main` branch only
  - [x] Permissions: `contents: write` (required by `mkdocs gh-deploy`)
  - [x] Steps: checkout (fetch-depth: 0 for git history), setup-python 3.12, `pip install -e ".[docs]"`, `mkdocs gh-deploy --force`
  - [x] Do NOT use `mike deploy` for v0.1 — mike versioning deferred to v0.2 per architecture

- [x] Task 6: Update `README.md` — add docs badge (AC: #4)
  - [x] Insert `[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://YOUR-ORG.github.io/physlink/)` badge in the existing badge block (line 3-5 of README)
  - [x] The badge line goes between existing CI badge and arXiv badge

## Dev Notes

### Current Repository State

**Files that exist:** `pyproject.toml`, `README.md`, `.github/workflows/ci.yml`, `src/physlink/`, `tests/`, `docs/` (empty dir)

**Files that do NOT exist yet (all NEW in this story):**
- `mkdocs.yml`
- `docs/index.md`
- `docs/getting-started.md`
- `docs/domain-scientists.md`
- `docs/api/index.md`
- `docs/changelog.md`
- `docs/lab-adoption-guide.md`
- `.github/workflows/docs.yml`

**Files to MODIFY:**
- `pyproject.toml` — add `[project.optional-dependencies] docs = [...]`
- `.github/workflows/ci.yml` — add `docs` job
- `README.md` — add docs badge

### Current `physlink/__init__.py` State (Critical)

```python
__version__ = "0.1.0"

from physlink.core.exceptions import PhysLinkError
from physlink.utils.diagnostics import doctor

__all__ = [
    "PhysLinkError",
    "doctor",
    # Story 2.2/2.3: ObservationSpace, ActionSpace — deferred to Story 2.6
    # Story 3.1: DreamerV3Adapter
    # Story 4.3/4.4: register_invariant, ComplianceReport
]
```

**DO NOT add ObservationSpace or ActionSpace to `__init__.py`** — that is Story 2.6's scope. Reference them by full module path in the docs API reference.

### `pyproject.toml` Change

Current `[project.optional-dependencies]` section has `dev = [...]` only. ADD a `docs` group:

```toml
[project.optional-dependencies]
dev = [
    "ruff>=0.4",
    "mypy>=1.9",
    "pytest>=8.0",
    "pytest-benchmark>=4.0",
    "pre-commit>=3.7",
    "build>=1.2",
    "torch",
]
docs = [
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.25",
    "mike>=2.1",
]
```

### `mkdocs.yml` Specification

```yaml
site_name: PhysLink
site_description: Backend-agnostic adapter library for physical simulation ML
site_url: https://YOUR-ORG.github.io/physlink/
repo_url: https://github.com/YOUR-ORG/physlink
repo_name: YOUR-ORG/physlink
edit_uri: edit/main/docs/

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest
    - search.highlight
    - content.code.copy
  palette:
    - scheme: default
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: google
            show_source: false
            show_root_heading: true
            show_root_full_path: false

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Domain Scientists: domain-scientists.md
  - API Reference: api/index.md
  - Changelog: changelog.md
  - Lab Adoption Guide: lab-adoption-guide.md

extra:
  version:
    provider: mike
```

**Critical `paths: [src]` setting** — mkdocstrings must know the src-layout. Without it, `:::physlink.core.spaces.ObservationSpace` won't resolve. This is the most common mkdocstrings failure mode with src/ layout.

### `docs/api/index.md` — mkdocstrings Directives

```markdown
# API Reference

## Public Interface (`physlink`)

::: physlink.core.exceptions.PhysLinkError

::: physlink.utils.diagnostics.doctor

## Space Configuration (`physlink.core.spaces`)

::: physlink.core.spaces.ObservationSpace

::: physlink.core.spaces.ActionSpace
```

**Why this structure:** `ObservationSpace` and `ActionSpace` are not in `physlink.__init__` yet (Story 2.6). Document them from their canonical module path. mkdocstrings renders the full class including `from_proprioception()` classmethod, `explain()` method, and `__repr__`.

**AC note:** The epic says "all 7 physlink.__init__ exports" — this is the target END STATE after Epic 2 + 3 + 4. Story 2.5 documents the 4 symbols available now. Story 2.6 will add docstrings; future epics will add more symbols. The docs infrastructure built in this story handles all of them automatically.

### CI Job Addition (`.github/workflows/ci.yml`)

Add a parallel `docs` job — it does NOT depend on `test-cpu` and runs independently:

```yaml
  docs:
    name: docs-build
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install docs dependencies
        run: pip install -e ".[docs]"

      - name: Build docs — strict
        run: mkdocs build --strict
```

**Why `--strict`:** Catches broken internal links, missing nav pages, unresolvable mkdocstrings references before merge.

### GitHub Pages Deploy Workflow (`.github/workflows/docs.yml`)

```yaml
name: Deploy Docs

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  deploy:
    name: deploy-docs
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install docs dependencies
        run: pip install -e ".[docs]"

      - name: Configure git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Deploy to GitHub Pages
        run: mkdocs gh-deploy --force
```

**Why `fetch-depth: 0`:** `mkdocs gh-deploy` pushes to the `gh-pages` branch and needs full history to avoid force-push conflicts. Also required by `mike` when it's adopted in v0.2.

**Why NOT `mike deploy` here:** Architecture explicitly says "Versioning via mike dès v0.2" — for v0.1, `mkdocs gh-deploy` is the correct command. The `mike` package is installed but not used yet.

### README Badge Update

Current README badge block (lines 3–5):
```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/YOUR-ORG/physlink/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-ORG/physlink/actions/workflows/ci.yml)
[![arXiv](https://img.shields.io/badge/arXiv-coming%20soon-b31b1b.svg)](https://arxiv.org/abs/PLACEHOLDER)
```

Insert docs badge BETWEEN the CI badge and arXiv badge:
```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/YOUR-ORG/physlink/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-ORG/physlink/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://YOUR-ORG.github.io/physlink/)
[![arXiv](https://img.shields.io/badge/arXiv-coming%20soon-b31b1b.svg)](https://arxiv.org/abs/PLACEHOLDER)
```

**Keep `YOUR-ORG` placeholder** — consistent with all other `YOUR-ORG` references in README. Do NOT replace with a real org name.

### `docs/getting-started.md` Key Content

Hugo's DD-001 5-step Colab path (must align with architecture):
1. `pip install physlink` (or `pip install physlink[gpu]`)
2. `physlink.doctor()` — Go/No-Go < 15s
3. `ObservationSpace.from_proprioception(joints=7, include_velocity=True)`
4. `ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)`
5. `adapter.fit(trajectories)` (shown as preview — DreamerV3Adapter is Epic 3)

Steps 1–4 are implemented now; step 5 is a preview with a note "DreamerV3Adapter available after Epic 3".

### `docs/domain-scientists.md` Key Content

Samuel's DD-003 path:
- Physical hallucinations problem statement (model violates physical laws)
- `register_invariant` usage (shown as preview — Epic 4)
- `ComplianceReport` output preview
- Link to lab-adoption-guide for Petra

These previews are intentional — the docs infrastructure is live; the API content grows with each epic.

### Docstrings State Warning

**Story 2.6 adds Google-style docstrings to all public functions.** Story 2.5 runs BEFORE 2.6. The `mkdocs build --strict` will succeed because mkdocstrings renders classes even with minimal/missing docstrings (it shows the signature). The rendered API pages may be sparse until Story 2.6 completes — this is expected and acceptable.

**Do NOT add docstrings in this story** to compensate. That work belongs in Story 2.6. The CI docs build must pass with whatever docstrings exist today.

### Architecture Compliance Checklist

- ✅ MkDocs Material + mkdocstrings[python] + GitHub Pages — AR-09 from architecture.md
- ✅ mike installed as dev dependency, deferred to v0.2 for actual use
- ✅ Google-style docstrings configured in mkdocstrings options (consistent with architecture decision Category 4)
- ✅ `paths: [src]` in mkdocstrings config — required for src-layout (most common failure mode)
- ✅ Badge on README pointing to GitHub Pages URL — architecture "Signal Petra" requirement
- ✅ No `physlink/__init__.py` changes — that is Story 2.6 scope

### Testing This Story

No unit tests are added — this is infrastructure/configuration work. Validation is:
1. `pip install -e ".[docs]"` succeeds locally
2. `mkdocs build --strict` produces `site/` with no errors or warnings
3. The `site/api/index.html` contains the class signatures for ObservationSpace, ActionSpace
4. CI green: the new `docs` job passes on the PR

### Project Structure Notes

The architecture `Complete Project Directory Structure` defines:
```
physlink/
├── mkdocs.yml                            # MkDocs Material config ← NEW
└── docs/
    ├── index.md
    ├── getting-started.md                # DD-001: Hugo 5-step Colab path ← NEW
    ├── domain-scientists.md              # DD-003: Samuel ← NEW
    ├── api/
    │   └── (auto-généré par mkdocstrings) ← docs/api/index.md NEW
    ├── changelog.md                      # mirror CHANGELOG.md ← NEW
    └── lab-adoption-guide.md             # DD-002: Petra ← NEW
```

All new files are exactly in the locations defined by architecture.

### Previous Story Intelligence

**From Story 2.4 (done — ObservationSpace.explain() + ActionSpace.explain()):**
- All 301 tests pass, 0 regressions
- `src/physlink/core/spaces.py` contains fully implemented `ObservationSpace` and `ActionSpace` with `.explain()` and Google-style docstrings started but minimal
- Commit format: `feat(story-2.4): Space Explain Introspection`

**From git context:**
- Last 5 commits: all `feat(story-X.Y): Title Case Description` pattern — follow this convention
- No `mkdocs.yml` or `docs/` content exists yet — this is greenfield

### References

- [Source: architecture.md#Category 4 — Documentation] — MkDocs Material + mkdocstrings + GitHub Pages decision
- [Source: architecture.md#Complete Project Directory Structure] — docs/ layout, mkdocs.yml at root
- [Source: architecture.md#Integration Points — CI/CD] — existing CI pipeline structure to extend
- [Source: epics.md#Story 2.5] — Acceptance Criteria
- [Source: epics.md#Epic 2] — Goal: researcher configures 7-DOF arm in <15 lines
- [Source: .github/workflows/ci.yml] — existing CI structure for parallel jobs pattern
- [Source: pyproject.toml] — existing optional-deps structure for docs group

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `mkdocs build --strict` failed initially: `mkdocs_autorefs` misinterpreted `info["bounds"][0]` in `ActionSpace.explain()` docstring as a Markdown cross-reference to symbol `0`. Fixed by replacing `>>> info["bounds"][0]` / `[-1.0, 1.0]` with `>>> len(info["bounds"])` / `7` — minimal change to existing docstring, within Story 2.5 scope since CI docs build must pass.

### Completion Notes List

- All 6 tasks completed. `pip install -e ".[docs]"` resolves without conflicts.
- `mkdocs build --strict` passes locally: `site/` produced, `site/api/index.html` contains all 4 symbols (ObservationSpace ×19, ActionSpace ×19, doctor ×5, PhysLinkError ×7 occurrences).
- 301 existing tests pass, 2 skipped, 0 regressions.
- No new `physlink/__init__.py` changes — Story 2.6 scope respected.
- `mike` installed but not used — versioning deferred to v0.2 per architecture.
- `--strict` flag in CI docs job catches broken nav links and unresolvable mkdocstrings references before merge.

### File List

- `pyproject.toml` — added `docs` optional-dependencies group
- `mkdocs.yml` — new MkDocs Material configuration at project root
- `docs/index.md` — new home page
- `docs/getting-started.md` — new Hugo DD-001 5-step Colab guide
- `docs/domain-scientists.md` — new Samuel DD-003 physical hallucinations guide
- `docs/api/index.md` — new API reference with mkdocstrings directives
- `docs/changelog.md` — new changelog page (v0.1.0 summary)
- `docs/lab-adoption-guide.md` — new Petra DD-002 evaluation guide
- `.github/workflows/ci.yml` — added parallel `docs` job with `mkdocs build --strict`
- `.github/workflows/docs.yml` — new GitHub Pages deploy workflow
- `README.md` — inserted Docs badge between CI and arXiv badges
- `src/physlink/core/spaces.py` — fixed `[0]` cross-reference bug in `ActionSpace.explain()` docstring example
- `tests/integration/test_docs_infrastructure.py` — new integration tests (54 tests) validating all 4 ACs without running mkdocs build

## Change Log

- 2026-05-22: Story 2.5 — MkDocs documentation site infrastructure. Added docs optional-deps, mkdocs.yml config, 6 docs content pages, CI docs build job, GitHub Pages deploy workflow, README docs badge. Fixed mkdocs_autorefs cross-reference bug in ActionSpace.explain() docstring.
- 2026-05-22: Senior Developer Review (AI) — 0 Critical, 2 Medium fixed (site/ added to .gitignore, test file added to File List), 1 Low fixed (encoding="utf-8" in _load_yaml). 54/54 tests pass. Status → done.
