# Story 6.2: Domain Scientists Landing Page

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a domain scientist worried that ML tools will ignore the laws of physics,
I want to read a documentation page that names "physical hallucinations" explicitly and shows me how to register my own invariant check,
so that I understand PhysLink respects domain knowledge and I can validate my own data.

## Acceptance Criteria

1. **Given** I navigate to `docs/domain-scientists.md`
   **When** I read the Philosophy section
   **Then** the term "physical hallucinations" appears explicitly by name (not paraphrased)
   **And** the section explains why physics-blind ML models hallucinate physically impossible trajectories

2. **Given** I continue reading the page
   **When** I reach the API section
   **Then** a complete `mass_conservation` worked example is shown: the function definition, the `register_invariant()` call, and the `PASS` output in the exact format `"mass_conservation: PASS (max_residual=X, threshold=Y, violations=0/N)"`
   **And** the example is explicitly labeled as illustrative — a note states that any physical domain works (CFD: energy conservation, robotics: momentum conservation, climate: mass conservation) with the same pattern

3. **Given** I finish reading the page
   **When** I look for next steps
   **Then** a CTA button or prominent link points to the Domain Scientist Colab notebook (Story 6.3, path: `notebooks/domain-scientist-colab.ipynb`)

## Tasks / Subtasks

- [x] Task 1: Rewrite `docs/domain-scientists.md` to satisfy all 3 ACs (AC: #1, #2, #3)
  - [x] Replace the existing file completely — current content is pre-Epic-4 placeholder with wrong API, wrong import path, and missing "physical hallucinations" Philosophy section
  - [x] Write Philosophy section: paragraph naming "physical hallucinations" explicitly, explaining why physics-blind ML models produce physically impossible trajectories
  - [x] Write API section: `mass_conservation` worked example — fn definition with `fn(trajectory: dict) -> float` signature, `register_invariant()` call, and PASS output line in exact format
  - [x] Add illustrative note: "any physical domain works with the same pattern" (CFD: energy conservation, robotics: momentum conservation, climate: mass conservation)
  - [x] Add CTA link pointing to `notebooks/domain-scientist-colab.ipynb` (GitHub Colab URL pattern — Story 6.3 creates this notebook)

- [x] Task 2: Create `tests/integration/test_domain_scientists_page.py` (AC: #1, #2, #3)
  - [x] Test: `docs/domain-scientists.md` file exists and is non-empty
  - [x] Test: "physical hallucinations" appears verbatim in the file
  - [x] Test: Philosophy section explains ML hallucinations (checks for keyword "physics-blind" or equivalent concept)
  - [x] Test: `mass_conservation` function definition appears inside a Python fenced code block
  - [x] Test: `register_invariant(` call appears inside a Python fenced code block
  - [x] Test: PASS output line in exact format `"mass_conservation: PASS"` appears in file
  - [x] Test: exact string `violations=0/` appears (matching format `violations=0/N`)
  - [x] Test: illustrative note about multiple physical domains exists (checks for at least "CFD" or "energy conservation" or "momentum conservation" in context)
  - [x] Test: CTA link to Colab notebook present (`notebooks/domain-scientist-colab.ipynb` in file)

## Dev Notes

### Epic 6 Scope — Zero Python Source Changes

Epic 6 touches ONLY:
- `README.md` (Story 6.1 — done)
- `docs/domain-scientists.md` (this story — Story 6.2)
- `notebooks/` (Story 6.3)

**Absolutely no changes to** `src/`, `tests/unit/`, `tests/perf/`, `pyproject.toml`, `.github/workflows/`, or any existing Python source file. The dev agent must not touch any Python source under `src/physlink/`.

### Current State of docs/domain-scientists.md — Must Be Replaced

The file at `docs/domain-scientists.md` already exists but contains pre-Epic-4 placeholder content. It is **entirely wrong** and must be rewritten from scratch:

**Problems with current content:**
1. Wrong import path: `from physlink.compliance import register_invariant` — **WRONG.** Correct: `from physlink import register_invariant` (it's a top-level export in `physlink.__init__`)
2. Wrong `register_invariant` API: current file shows `register_invariant(space=obs_space, name=..., fn=..., severity=...)` — **WRONG.** Correct signature: `register_invariant(adapter, name, fn, tolerance, mode)` where `adapter` is a `DreamerV3Adapter` instance
3. Wrong fn signature: current file uses a lambda with boolean return — **WRONG.** Correct: `fn(trajectory: dict) -> float` returning a residual
4. Wrong output format: current shows emoji ✅/⚠️/❌ table format — **WRONG.** Correct: `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`
5. Missing "physical hallucinations" Philosophy section — this is AC #1 and a hard requirement (UX-DR-10)
6. "(preview — Epic 4)" labels scattered throughout — Epic 4 is complete; remove all preview markers
7. Missing CTA to Colab notebook — required by AC #3

**The dev agent must write the entire file from scratch.** Do not attempt to patch the existing content.

### Correct register_invariant() API

From `physlink/__init__.py` (Category 3 architecture decision — top-level export):

```python
from physlink import register_invariant, DreamerV3Adapter, ComplianceReport
```

Full signature (from `src/physlink/core/validation.py`):

```python
register_invariant(
    adapter: DreamerV3Adapter,   # DreamerV3Adapter instance (already fit())
    name: str,                    # human-readable invariant name
    fn: Callable[[dict], float],  # returns residual — 0.0 = perfect compliance
    tolerance: float,             # max acceptable residual
    mode: Literal["hard", "soft"] = "soft",
) -> None
```

- `adapter` is a `DreamerV3Adapter` (not an ObservationSpace or ActionSpace)
- `fn` signature is `fn(trajectory: dict) -> float` — returns a float residual
- `mode="hard"` rejects trajectories where `fn(trajectory) > tolerance`
- `mode="soft"` penalizes the loss without rejecting

### Correct mass_conservation Worked Example

The mass_conservation example must follow this exact pattern (from epics.md AC #2 and UX-DR-10):

```python
from physlink import DreamerV3Adapter, register_invariant

# Assume adapter is already constructed (see getting-started.md)
def mass_conservation(trajectory: dict) -> float:
    """Returns residual: absolute difference between mass_in and mass_out."""
    return abs(trajectory["mass_flow_in"] - trajectory["mass_flow_out"])

register_invariant(
    adapter,
    name="mass_conservation",
    fn=mass_conservation,
    tolerance=0.01,
    mode="hard",
)

report = adapter.compliance_report()
print(report.summary())
```

Expected output (exact format from `report.summary()` — see `src/physlink/core/validation.py` Story 4.4):

```
mass_conservation: PASS (max_residual=0.007, threshold=0.01, violations=0/1000)
```

**Key: the PASS line uses the exact format defined in Story 4.4: `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`**

### Philosophy Section — "physical hallucinations" Required

From UX-DR-10: *"Philosophy section naming 'physical hallucinations' explicitly."*
From epics.md AC #1: *"the term 'physical hallucinations' appears explicitly by name (UX-DR-10 — not paraphrased)"*

The Philosophy section must:
1. Use the exact phrase "physical hallucinations" (not "physically invalid trajectories" alone, not paraphrased)
2. Explain WHY physics-blind ML models hallucinate (statistically plausible but physically impossible outputs)
3. Name the mechanism: trained on simulation data, standard loss functions are blind to physical constraints

From `docs/domain-scientists.md` current content — this paragraph can be kept as a starting point but must be enhanced to include "physical hallucinations" explicitly:
> "Standard ML models trained on simulation data frequently produce physical hallucinations — predictions that are statistically plausible but physically impossible"

This sentence already contains "physical hallucinations" — the Philosophy section must build on this.

### CTA to Colab Notebook

Story 6.3 will create the notebook at `notebooks/domain-scientist-colab.ipynb`. The CTA must link to this file using the GitHub Colab URL pattern (same as the "Quick Start" button in the README):

```
https://colab.research.google.com/github/YOUR-ORG/physlink/blob/main/notebooks/domain-scientist-colab.ipynb
```

Use the same placeholder `YOUR-ORG` as the rest of the README — this is consistent with the existing Colab badge in the README action bar.

The CTA should be a prominent link or button, framed as the next step: e.g., "**[Open Domain Scientist Colab →](https://colab.research.google.com/...)**"

### Recommended File Structure

```markdown
# For Domain Scientists

[intro paragraph — brief, empathetic: this page is for you if you need ML that respects physics]

## Philosophy: Physical Hallucinations

[paragraph naming "physical hallucinations" explicitly — explains the mechanism]
[examples of hallucinations: impossible joint angles, energy non-conservation, etc.]

## Registering a Physical Invariant

[brief intro: "Register your domain constraint as a plain Python callable"]

### mass_conservation Example

[python code block: fn definition + register_invariant call]
[output code block: PASS line in exact format]
[note: any domain works with the same pattern]

## What's Next?

[CTA link/button to Domain Scientist Colab notebook]
```

### Integration Test Pattern — Follow test_lab_adoption_guide.py

New file: `tests/integration/test_domain_scientists_page.py`

Use the exact same structure as `tests/integration/test_lab_adoption_guide.py`:
- `PROJECT_ROOT = Path(__file__).parent.parent.parent`
- `GUIDE = PROJECT_ROOT / "docs" / "domain-scientists.md"`
- `def _guide_text() -> str: return GUIDE.read_text(encoding="utf-8")`
- Class-based test organization
- Error messages with `\n  Fix:` hints

Python code block helper (from `test_lab_adoption_guide.py` pattern):
```python
@staticmethod
def _python_code_blocks() -> list[str]:
    return re.findall(r"```python\n(.*?)```", _guide_text(), re.DOTALL)
```

### Test Count Baseline

- After Story 6.1: **832 passed, 2 skipped**
- Story 6.2 adds ~9 integration tests
- Expected after 6.2: **~841 passed, 2 skipped**

`ruff check src/` and `mypy --strict src/physlink/core/` must still pass — Story 6.2 does not touch Python source, zero risk.

### Files to Create / Modify

| File | Action | AC |
|------|--------|----|
| `docs/domain-scientists.md` | **REWRITE** (replace entirely — existing content is pre-Epic-4 placeholder) | #1, #2, #3 |
| `tests/integration/test_domain_scientists_page.py` | **CREATE** | #1, #2, #3 |

No changes to `src/`, `README.md`, `pyproject.toml`, or `.github/workflows/`.

### Commit Message Pattern

Following all prior stories:
```
feat(story-6.2): Domain Scientists Landing Page
```

### Project Structure Notes

- `docs/domain-scientists.md` is at `docs/` (same level as `lab-adoption-guide.md`, `getting-started.md`, `changelog.md`)
- New test file: `tests/integration/test_domain_scientists_page.py`
- Tests use `PROJECT_ROOT = Path(__file__).parent.parent.parent` (3 levels up from `tests/integration/`)
- Fixtures: no fixtures needed — pure file reading tests
- No `@pytest.mark.gpu` — content-only story, no GPU testing

### Previous Story Intelligence (Story 6.1)

- Story 6.1 Dev Notes confirmed: `docs/domain-scientists.md` already exists with DD-003 placeholder content. Story 6.1's scope was README only — it explicitly deferred 6.2 for this full rewrite.
- Story 6.1 established test count baseline: **832 passed, 2 skipped** after the full suite.
- Story 6.1 File List pattern: enumerate every created/modified file before marking done.
- Story 5.3 review caught uncommitted test extensions — ensure File List matches actual changes.
- Epic 6 zero-source constraint first confirmed in Story 6.1 Dev Notes: no changes to `src/`, `pyproject.toml`, `.github/workflows/`.

### Architecture References

- `register_invariant` top-level export: [Source: architecture.md#Category 3 — Module Public API Surface]
- `fn(trajectory: dict) -> float` signature: [Source: architecture.md#Docstring Patterns] and [Source: epics.md#Story 4.3]
- PASS output format: [Source: epics.md#Story 4.4] — `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`
- `physlink.core.validation` — Protocol `_HasInvariants` used for core/adapters boundary: [Source: architecture.md#Architectural Boundaries]
- `docs/` directory structure: [Source: architecture.md#Complete Project Directory Structure] — `docs/domain-scientists.md` listed as "DD-003: Samuel"

### References

- [Source: epics.md#Story 6.2] — Full user story, 3 acceptance criteria
- [Source: epics.md#UX-DR-10] — "Domain Scientists landing page: Philosophy section naming 'physical hallucinations' explicitly; mass_conservation worked example; CTA to Colab notebook"
- [Source: architecture.md#Category 3] — `register_invariant` at top level `physlink.__init__`
- [Source: epics.md#Story 4.3] — `register_invariant(adapter, name, fn, tolerance, mode)` full signature
- [Source: epics.md#Story 4.4] — `report.summary()` format: `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`
- [Source: docs/domain-scientists.md] — Current state: pre-Epic-4 placeholder, wrong API, must be replaced entirely
- [Source: 6-1-readme-for-domain-scientists-link.md#Dev Notes] — Epic 6 zero-source constraint; test count baseline 832 passed, 2 skipped
- [Source: tests/integration/test_lab_adoption_guide.py] — Test pattern to follow for docs content validation
- [Source: DD-003-samuels-dignity-validation.yaml] — Samuel's success criteria: "physical hallucinations" named, mass_conservation PASS, community return path

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was straightforward.

### Completion Notes List

- Rewrote `docs/domain-scientists.md` from scratch: replaced pre-Epic-4 placeholder with correct API, correct import path (`from physlink import DreamerV3Adapter, register_invariant`), explicit "physical hallucinations" Philosophy section, mass_conservation worked example with `fn(trajectory: dict) -> float` signature and exact PASS output format, illustrative note (CFD/robotics/climate), and Colab CTA link.
- Created `tests/integration/test_domain_scientists_page.py` with 16 integration tests covering all 3 ACs (initial 10 + 6 added by QA-gaps workflow: full PASS format regex, correct import path, wrong import absent, `-> float` type hint, all-three-domains note, Colab URL format).
- All 16 new tests pass. Full suite: 848 passed, 2 skipped (baseline 832 + 16 new).
- No changes to `src/`, `pyproject.toml`, or `.github/workflows/` — Epic 6 zero-source constraint respected.

### File List

- `docs/domain-scientists.md` — REWRITTEN (AC #1, #2, #3)
- `tests/integration/test_domain_scientists_page.py` — CREATED (AC #1, #2, #3)

## Change Log

- 2026-05-22: feat(story-6.2): Rewrote Domain Scientists landing page — correct API, "physical hallucinations" section, mass_conservation worked example with exact PASS format, Colab CTA. Created integration test suite (16 tests, 848 passed total).
- 2026-05-22: review(story-6.2): Adversarial code review passed — 0 CRITICAL, 0 HIGH issues. Fixed MEDIUM: Completion Notes updated to reflect 16 tests (10 + 6 QA-gaps additions) and 848 passed baseline. Status → done.
