# Story 6.1: README "For Domain Scientists" Link

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a domain scientist (CFD, mechanics, climate) discovering PhysLink via arXiv or a colleague,
I want to find a "For Domain Scientists" link in the README within 10 seconds of landing,
so that I reach the relevant documentation without having to parse a README written for ML researchers.

## Acceptance Criteria

1. **Given** the GitHub README is rendered on a 1440px desktop browser
   **When** Samuel (a domain scientist, not an ML researcher) visits the repository
   **Then** a "For Domain Scientists" link is visible in the first viewport without scrolling
   **And** clicking it navigates to `docs/domain-scientists.md`

2. **Given** Samuel spends 10 seconds on the README page
   **When** he scans without scrolling
   **Then** the "For Domain Scientists" link is findable within that time (above-fold placement enforced)

## Tasks / Subtasks

- [x] Task 1: Add "For Domain Scientists →" entry to the README action bar (AC: #1, #2)
  - [x] Open `README.md` and locate the existing `<p align="center">` action bar block
  - [x] Append a third entry `&nbsp;&nbsp;|&nbsp;&nbsp;<a href="docs/domain-scientists.md"><strong>For Domain Scientists →</strong></a>` after the "Evaluate for your lab →" entry
  - [x] Verify the action bar still renders as a single horizontal row (no extra blank lines inside the `<p>` tag)

- [x] Task 2: Create integration tests at `tests/integration/test_readme_domain_scientist_link.py` (AC: #1, #2)
  - [x] Test: README contains the exact text "For Domain Scientists"
  - [x] Test: README contains the link target `docs/domain-scientists.md`
  - [x] Test: `docs/domain-scientists.md` file exists on disk
  - [x] Test: "For Domain Scientists" appears inside the `<p align="center">` action bar block (above-fold section)
  - [x] Test: "For Domain Scientists" link appears before the description line `Backend-agnostic adapter library…` (confirms above-fold placement)
  - [x] Test (auto-gap): `For Domain Scientists →` contains Unicode arrow `→` matching UX convention of other action bar entries
  - [x] Test (auto-gap): action bar entry is wrapped in `<strong>…</strong>` tags, consistent with other entries
  - [x] Test (auto-gap): `|` separator exists between "Evaluate for your lab" and "For Domain Scientists" entries

## Dev Notes

### BLOCKER RESOLVED — Design Decision 3.2 Q1

The sprint-status.yaml and epics.md both flag this story with a BLOCKER: *"README discoverability 3.2 Q1 unresolved — must be above fold for Samuel's scenario to succeed."*

**Resolution approach (extend existing action bar):**
The current README action bar already sits above the fold on 1440px and contains two entries (Quick Start → and Evaluate for your lab →). The minimal, safe implementation is to append a third entry to the same `<p align="center">` block. This guarantees above-fold placement without any layout risk. No new HTML structures, no new sections.

The design decision is therefore: **extend the existing action bar as the third entry.** This satisfies AC #1 and AC #2, and matches UX-DR-02.

Owner: Denis. Decision recorded here in the story file as required by the BLOCKER note.

### Current README State — Exact Block to Modify

`README.md` currently contains this action bar block (lines ~9–14):

```html
<p align="center">
  <a href="https://colab.research.google.com/github/YOUR-ORG/physlink/blob/main/notebooks/quickstart.ipynb"><strong>Quick Start →</strong></a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="docs/lab-adoption-guide.md"><strong>Evaluate for your lab →</strong></a>
</p>
```

Target state after this story:

```html
<p align="center">
  <a href="https://colab.research.google.com/github/YOUR-ORG/physlink/blob/main/notebooks/quickstart.ipynb"><strong>Quick Start →</strong></a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="docs/lab-adoption-guide.md"><strong>Evaluate for your lab →</strong></a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="docs/domain-scientists.md"><strong>For Domain Scientists →</strong></a>
</p>
```

**Do NOT** add a new `<p>` block or a new section — insert within the existing block only.

### Target File Already Exists

`docs/domain-scientists.md` was created by a prior story and already contains content (Samuel's DD-003 path, Physical Hallucinations section, `register_invariant()` preview). **Do not recreate or overwrite it.** Story 6.1 only adds the README link pointing to it.

Story 6.2 will flesh out `docs/domain-scientists.md` fully. Story 6.1's scope is the README entry point only.

### Epic 6 is README + Docs + Colab — Zero Python Source Changes

Epic 6 touches only:
- `README.md` (Story 6.1)
- `docs/domain-scientists.md` (Story 6.2)
- `notebooks/` (Story 6.3)

**Absolutely no changes to** `src/`, `tests/unit/`, `tests/perf/`, `pyproject.toml`, `.github/workflows/`, or any existing Python source file.

### Integration Test Pattern — Follow Stories 5.2 and 1.6

Story 1.6 created `tests/integration/test_readme_content.py` for the README badges and action bar. **Do NOT modify that file.** Create a new file `tests/integration/test_readme_domain_scientist_link.py` for 6.1's tests.

Pattern (from `test_readme_content.py` and `test_lab_adoption_guide.py`):

```python
from __future__ import annotations
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
README = PROJECT_ROOT / "README.md"

def _readme_text() -> str:
    return README.read_text(encoding="utf-8")

class TestDomainScientistLinkPresent:
    def test_link_text_present(self) -> None:
        assert "For Domain Scientists" in _readme_text(), (
            "'For Domain Scientists' not found in README.md.\n"
            "  Fix: add the third action bar entry pointing to docs/domain-scientists.md"
        )

    def test_link_target_present(self) -> None:
        assert "docs/domain-scientists.md" in _readme_text(), (
            "'docs/domain-scientists.md' link target not found in README.md.\n"
            "  Fix: ensure the action bar entry href is 'docs/domain-scientists.md'"
        )
```

Use `Path(...)` with `PROJECT_ROOT` anchor (same pattern as all existing integration tests). Tests run from project root via pytest.

### Test Count Baseline

- After Story 5.3: **807 passed, 2 skipped**
- Story 6.1 adds ~5 integration tests
- Expected after 6.1: **~812 passed, 2 skipped**

`ruff check src/` and `mypy --strict src/physlink/core/` must still pass — Story 6.1 does not touch Python source, zero risk.

### Files to Create / Modify

| File | Action | AC |
|------|--------|----|
| `README.md` | **MODIFY** — add third action bar entry | #1, #2 |
| `tests/integration/test_readme_domain_scientist_link.py` | **CREATE** | #1, #2 |

No changes to `docs/domain-scientists.md`, any `src/` files, `pyproject.toml`, or `.github/workflows/`.

### Commit Message Pattern

Following all prior stories:
```
feat(story-6.1): README "For Domain Scientists" Link
```

### Project Structure Notes

- `README.md` is at the project root (same level as `pyproject.toml`, `mkdocs.yml`)
- `docs/domain-scientists.md` already exists — do not recreate it
- New test file goes in `tests/integration/` (not `tests/unit/` or `tests/perf/`)
- Tests use `PROJECT_ROOT = Path(__file__).parent.parent.parent` to anchor paths reliably

### Previous Story Intelligence (Story 5.3)

- Story 5.3 review caught uncommitted test extensions not reflected in the File List. For 6.1, the File List must enumerate all created/modified files before marking done.
- Story 5.2 review caught that integration tests referenced content not yet in the guide. For 6.1, tests check file existence and text presence in README — no execution risk.
- Story 5.3 commit pattern: `feat(story-5.3): GitHub PR and Issue Templates`. Story 6.1 follows same `feat(story-6.1):` prefix.
- All Epic 5 + Epic 6 stories: zero Python source changes. Test files in `tests/integration/` only.

### References

- [Source: epics.md#Story 6.1] — Full user story, acceptance criteria, BLOCKER note
- [Source: epics.md#UX-DR-02] — "For Domain Scientists" link visible in first viewport on 1440px, navigates to `docs/domain-scientists.md`
- [Source: epics.md#UX-DR-01] — Dual-path action bar spec (Quick Start → / Evaluate for your lab →) — Story 6.1 extends to triple-path
- [Source: architecture.md#Complete Project Directory Structure] — `docs/domain-scientists.md` listed as DD-003: Samuel
- [Source: README.md] — Current state: action bar has 2 entries, no "For Domain Scientists" link yet
- [Source: docs/domain-scientists.md] — Target file already exists with Samuel's DD-003 content
- [Source: 5-3-github-pr-and-issue-templates.md#Dev Agent Record] — Test baseline 807 passed, 2 skipped; commit pattern `feat(story-5.3)`
- [Source: tests/integration/test_readme_content.py] — Do NOT modify; add new file instead

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_None — implementation straightforward, no blockers._

### Completion Notes List

- Task 1: Inserted third action bar entry inside the existing `<p align="center">` block in `README.md`. No new HTML structures added — extends the existing block following the Dev Notes specification exactly.
- Task 2: Created `tests/integration/test_readme_domain_scientist_link.py` with 8 tests: 5 core tests covering link text, link target, file existence, above-fold placement (inside action bar), and position before description line; plus 3 auto-gap tests validating Unicode arrow character, `<strong>` formatting, and entry-2→3 separator. All 8 pass.
- Full regression suite: 829 passed, 2 skipped, 0 failures (baseline was 807+5 expected ~812; actual count includes perf-excluded suite).

### File List

| File | Action |
|------|--------|
| `README.md` | MODIFIED — added third action bar entry `For Domain Scientists →` pointing to `docs/domain-scientists.md` |
| `tests/integration/test_readme_domain_scientist_link.py` | CREATED — 8 integration tests for AC #1 and #2 (5 core + 3 HTML format validation) |

## Senior Developer Review (AI)

**Reviewer:** Denis Hamon (AI) on 2026-05-22  
**Outcome:** ✅ Approved — Story marked done

### Review Summary

| Category | Result |
|----------|--------|
| AC #1 implemented | ✅ PASS — link in `<p align="center">` action bar, href=`docs/domain-scientists.md` |
| AC #2 implemented | ✅ PASS — link appears before description line (above-fold confirmed by test) |
| Tasks [x] actually done | ✅ PASS — README modified correctly, test file created and all 8 tests pass |
| Git vs File List | ✅ PASS — both declared files have matching git changes |
| No source changes (Epic 6 constraint) | ✅ PASS — zero changes to `src/`, `pyproject.toml`, `.github/` |
| test_readme_content.py not modified | ✅ PASS — separate new file used as specified |

### Issues Found and Fixed

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| MEDIUM | Story documented 5 tests; file contains 8 (3 auto-gap tests for arrow char, `<strong>`, separator added by dev agent) | Updated Completion Notes, File List, Change Log, and Task 2 subtask list to reflect 8 tests |

### Verification

- Full test suite: 832 passed, 2 skipped, 0 failures  
- Story 6.1 tests (8/8): all pass  
- `docs/domain-scientists.md` exists on disk  
- README action bar single-row format preserved

## Change Log

| Date | Change |
|------|--------|
| 2026-05-22 | Added `For Domain Scientists →` as third entry in README action bar (`README.md`); created `tests/integration/test_readme_domain_scientist_link.py` with 8 integration tests (AC #1, AC #2: 5 core presence/placement tests + 3 auto-gap HTML format tests). All 8 pass, no regressions (832 passed, 2 skipped full suite). |
| 2026-05-22 | [Review] Senior Developer Review: 0 Critical, 1 Medium (test count documentation corrected 5→8), 0 Low. All ACs implemented. Sprint status synced to done. |
