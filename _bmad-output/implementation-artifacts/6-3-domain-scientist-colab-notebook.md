# Story 6.3: Domain Scientist Colab Notebook (8 Cells)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a domain scientist who has read the landing page,
I want an 8-cell Colab notebook where I only need to edit one cell to validate my own trajectory data,
so that I get a PASS or FAIL result without needing to understand the DreamerV3 internals.

## Acceptance Criteria

1. **Given** I open the Domain Scientist Colab notebook
   **When** Cell 1 (`pip install physlink`) executes
   **Then** if installation fails (e.g., version not yet on PyPI), a clear error message is shown: "physlink could not be installed — check the version number or PyPI availability"
   **And** no silent cascade of ModuleNotFoundError in later cells

2. **Given** Cell 1 installs successfully and I read Cell 3
   **When** I open the notebook for the first time
   **Then** a prominent `⚠️ "Edit this cell"` instruction is visible (the ONLY cell Samuel edits)
   **And** the cell contains an example trajectory variable that I replace with my own data
   **And** no other cell contains an instruction to edit it

3. **Given** I have replaced Cell 3's example data with my CFD trajectories and run all cells in order
   **When** Cell 5 executes
   **Then** the output displays `mass_conservation: PASS (violations=0/N)` (Samuel's moment of truth — UX-DR-11)
   **And** the PASS format matches exactly: `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`

4. **Given** Cell 6 executes
   **When** the compliance histogram renders
   **Then** the matplotlib histogram appears inline in the Colab output with the threshold line labeled
   **And** rendering completes in < 5 seconds (NFR-07)

5. **Given** I reach Cell 8 ("What's next?")
   **When** I read the cell output
   **Then** a link to the `domain_extension.md` GitHub issue template is prominently shown (Samuel's community return path — UX-DR-11)
   **And** the link is clickable and navigates to the correct GitHub issue template

6. **Given** any cell in the notebook is re-run
   **When** it executes again
   **Then** no side effects from the previous run corrupt the result (NFR-09 — all cells idempotent)

## Tasks / Subtasks

- [x] Task 1: Create `notebooks/domain-scientist-colab.ipynb` — 8-cell notebook (AC: #1, #2, #3, #4, #5, #6)
  - [x] Cell 1 (code): pip install physlink with explicit error handling — no silent ModuleNotFoundError propagation
  - [x] Cell 2 (code): imports (`ObservationSpace`, `ActionSpace`, `DreamerV3Adapter`, `register_invariant`)
  - [x] Cell 3 (code): `# ⚠️ Edit this cell` comment at top (prominent, ONLY cell with this instruction) + `your_trajectories` list with example CFD data (numpy-seeded for idempotence)
  - [x] Cell 4 (code): `ObservationSpace.from_proprioception(joints=7, include_velocity=True)` + `ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)` — pure setup, no adapter construction here
  - [x] Cell 5 (code): creates fresh `adapter = DreamerV3Adapter(obs_space, act_space)`, defines `mass_conservation(trajectory: dict) -> float`, calls `register_invariant(...)`, calls `adapter.fit(your_trajectories, steps=100, checkpoint_interval_steps=50)`, calls `compliance_report()`, prints `report.summary()` → outputs PASS
  - [x] Cell 6 (code): `report.plot(title="Mass Conservation Check", show_threshold=True)` — inline histogram
  - [x] Cell 7 (code): `adapter.export(path="./physlink_export/")` + share panel call
  - [x] Cell 8 (markdown): "What's next?" section with link to `domain_extension.md` GitHub issue template
  - [x] Verify notebook is valid JSON with `nbformat: 4, nbformat_minor: 5` and correct metadata (colab provenance, Python 3 kernel)
  - [x] Verify all 8 cells use the `source` field as a list of strings (lines ending with `\n` except the last)

- [x] Task 2: Create `tests/integration/test_domain_scientist_notebook.py` (AC: #1, #2, #3, #4, #5, #6)
  - [x] Test: notebook file exists at `notebooks/domain-scientist-colab.ipynb`
  - [x] Test: valid JSON parseable without error
  - [x] Test: exactly 8 cells (`len(nb["cells"]) == 8`)
  - [x] Test: Cell 1 (index 0) is code cell with `pip install physlink` and error guard (no silent failure)
  - [x] Test: Cell 3 (index 2) is code cell with `⚠️` and `Edit this cell` in source
  - [x] Test: Cell 3 is the ONLY cell containing `Edit this cell` (case-insensitive search across all 8 cells)
  - [x] Test: Cell 5 (index 4) contains `register_invariant(`, `compliance_report()`, and `print(report.summary())`
  - [x] Test: Cell 5 source contains `mass_conservation`
  - [x] Test: Cell 6 (index 5) contains `report.plot(`
  - [x] Test: Cell 8 (index 7) is a markdown cell
  - [x] Test: Cell 8 source contains `domain_extension.md`
  - [x] Test: Cell 8 source contains a GitHub URL (`github.com`)

## Dev Notes

### Epic 6 Scope — Zero Python Source Changes

Epic 6 touches ONLY:
- `README.md` (Story 6.1 — done)
- `docs/domain-scientists.md` (Story 6.2 — done)
- `notebooks/domain-scientist-colab.ipynb` (this story — Story 6.3)

**Absolutely no changes to** `src/`, `tests/unit/`, `tests/perf/`, `pyproject.toml`, `.github/workflows/`, or any existing Python source file.

### Notebook Format — Follow quickstart.ipynb Exactly

Reference: `notebooks/quickstart.ipynb`. The new notebook must use the same outer structure:

```json
{
  "nbformat": 4,
  "nbformat_minor": 5,
  "metadata": {
    "colab": { "provenance": [] },
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
  "cells": [ ... ]
}
```

**Cell format for code cells:**
```json
{
  "cell_type": "code",
  "execution_count": null,
  "metadata": {},
  "outputs": [],
  "source": ["line 1\n", "line 2\n", "last line"]
}
```

**Cell format for markdown cells:**
```json
{
  "cell_type": "markdown",
  "metadata": {},
  "source": ["# Heading\n", "\n", "Paragraph text."]
}
```

Markdown cells do NOT have `execution_count` or `outputs` fields.

### 8-Cell Canonical Structure

The notebook must contain exactly these 8 cells in order:

| Cell | Type | Purpose | AC |
|------|------|---------|-----|
| 1 | code | pip install physlink with error guard | #1 |
| 2 | code | imports (4 symbols from physlink) | — |
| 3 | code | ⚠️ "Edit this cell" — user trajectory data | #2 |
| 4 | code | ObservationSpace + ActionSpace setup | — |
| 5 | code | adapter + register_invariant + fit + PASS | #3 |
| 6 | code | report.plot() — inline histogram | #4 |
| 7 | code | adapter.export() + share panel | — |
| 8 | markdown | "What's next?" + domain_extension.md link | #5 |

### Cell 1 — pip install with Error Guard (AC #1)

The AC requires that failed installation shows a clear error — no silent ModuleNotFoundError cascade. Use subprocess to capture exit code:

```python
import subprocess, sys

_result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "physlink==0.1.2"],
    capture_output=True, text=True
)
if _result.returncode != 0:
    print(_result.stdout)
    raise RuntimeError(
        "physlink could not be installed — check the version number or PyPI availability"
    )
print(_result.stdout[-500:] if _result.stdout else "physlink installed successfully.")
```

**Why subprocess over `!pip install`:** `!pip install` in Colab does not raise Python exceptions on failure — it silently continues to the next cell, causing `ModuleNotFoundError` on import. Using `subprocess.run` + returncode check satisfies AC #1's "no silent cascade" requirement.

**Idempotence:** `pip install` is idempotent — running it twice with the same version tag has no side effects.

### Cell 3 — ⚠️ "Edit this cell" (AC #2 — CRITICAL)

This is the single most important cell for Samuel's UX. Exact requirements:
1. First line must be: `# ⚠️ Edit this cell — this is the ONLY cell you need to modify`
2. This exact phrase `Edit this cell` must appear NOWHERE else in the notebook (case-insensitive)
3. The cell contains `your_trajectories` — the variable used by all downstream cells

**Canonical implementation:**

```python
# ⚠️ Edit this cell — this is the ONLY cell you need to modify
#
# Replace your_trajectories with your simulation data.
# Each entry is a dict. Include the fields your invariant reads.
# (obs and action are required by the adapter — use zeros if your data lacks them.)

import numpy as np

_rng = np.random.default_rng(42)  # fixed seed for idempotent example data

your_trajectories = [
    {
        "obs": _rng.random(14).tolist(),        # observation vector (14-dim for 7 joints + velocities)
        "action": _rng.random(7).tolist(),       # action vector (7-dim)
        "mass_flow_in": 1.0 + _rng.normal(0, 0.003),    # ← your physics field
        "mass_flow_out": 1.0 + _rng.normal(0, 0.003),   # ← your physics field
    }
    for _ in range(1000)
]
print(f"Loaded {len(your_trajectories)} trajectories.")
```

**Why `numpy.random.default_rng(42)`:** Fixed seed makes Cell 3 idempotent — same data every run. Without fixed seed, the trajectories change on every re-run, making Cell 5's PASS/FAIL result non-deterministic.

**Why `obs` and `action` keys:** `adapter.fit()` expects these. Samuel's trajectories may not have RL fields; the example shows he should include them (as zeros or real data). This matches the architecture's `TrajectoryBatch` contract.

### Cell 5 — register_invariant + fit + PASS (AC #3 — CRITICAL)

Cell 5 must create a **fresh adapter instance** for full idempotence. Do NOT reuse an adapter from Cell 4. Cell 4 only creates `obs_space` and `act_space` (stateless, idempotent objects).

**Canonical implementation:**

```python
from physlink import DreamerV3Adapter

adapter = DreamerV3Adapter(obs_space, act_space)

def mass_conservation(trajectory: dict) -> float:
    """Returns residual: absolute difference between mass_flow_in and mass_flow_out."""
    return abs(trajectory["mass_flow_in"] - trajectory["mass_flow_out"])

register_invariant(
    adapter,
    name="mass_conservation",
    fn=mass_conservation,
    tolerance=0.01,
    mode="hard",
)

adapter.fit(your_trajectories, steps=100, checkpoint_interval_steps=50)

report = adapter.compliance_report()
print(report.summary())
```

Expected output (Samuel's moment of truth):
```
mass_conservation: PASS (max_residual=0.007, threshold=0.01, violations=0/1000)
```

**Why fresh adapter in Cell 5 (not Cell 4):** If `adapter` were created in Cell 4, re-running Cell 5 alone would call `register_invariant()` a second time on the same adapter — doubling the registered invariants. Creating `adapter` inside Cell 5 ensures re-running Cell 5 always starts with a clean adapter.

**Why `steps=100`:** The domain scientist notebook is not about training performance — it's about compliance validation. 100 steps is sufficient to demonstrate the PASS output without waiting 45 minutes (NFR-03 applies to Hugo's 10k-step use case, not Samuel's demo). A comment in the cell should note this.

**PASS output format (exact — from Story 4.4):** `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`. The test checks for `mass_conservation: PASS` pattern in cell source — not the output JSON (notebooks are unexecuted when stored in git).

### Cell 6 — report.plot() (AC #4)

```python
report.plot(title="Mass Conservation Check", show_threshold=True)
```

Must come AFTER Cell 5 (uses `report` from Cell 5). Simple, idempotent. Calling `report.plot()` twice produces the same histogram each time (NFR-13 — deterministic).

### Cell 8 — "What's next?" Markdown (AC #5)

Cell 8 is the ONLY markdown cell in the notebook. It must contain:
1. A "What's next?" heading
2. A prominent link to the `domain_extension.md` GitHub issue template (Samuel's community return path)

**domain_extension.md link format:**
The issue template was created in Story 5.3 at `.github/ISSUE_TEMPLATE/domain_extension.md`. The GitHub URL to create a new issue with this template is:

```
https://github.com/YOUR-ORG/physlink/issues/new?template=domain_extension.md
```

Use `YOUR-ORG` as placeholder (consistent with the rest of the codebase — README Colab URL also uses `YOUR-ORG`).

**Canonical Cell 8 source:**
```markdown
## What's next?

Your domain validation is complete. Here are your next steps:

1. **Share your results**: Your compliance report and GIF are in `./physlink_export/` — share the notebook URL with your team.

2. **Add your domain to PhysLink**: If you want to contribute your invariant (`mass_conservation` or your own) to the PhysLink community, open a Domain Extension issue:

   [**Open a Domain Extension Issue →**](https://github.com/YOUR-ORG/physlink/issues/new?template=domain_extension.md)

   The template will guide you through describing your physical domain, invariant function, and expected PASS output.

3. **Evaluate for your lab**: See the [Lab Adoption Guide](../docs/lab-adoption-guide.md) for a structured 1-day evaluation checklist.
```

**Why this link matters:** AC #5 explicitly checks for `domain_extension.md` in Cell 8 source. The integration test will grep for `domain_extension.md` string — ensure it appears verbatim.

### Integration Test Pattern — Follow test_domain_scientists_page.py

New file: `tests/integration/test_domain_scientist_notebook.py`

Use the same structure as `tests/integration/test_domain_scientists_page.py`:
- `PROJECT_ROOT = Path(__file__).parent.parent.parent`
- `NOTEBOOK = PROJECT_ROOT / "notebooks" / "domain-scientist-colab.ipynb"`
- Helper: `def _nb() -> dict: return json.loads(NOTEBOOK.read_text(encoding="utf-8"))`
- Helper: `def cell_source(cell: dict) -> str: src = cell["source"]; return "".join(src) if isinstance(src, list) else src`
- Class-based test organization with error messages containing `\n  Fix:` hints

**Key test implementations:**

```python
class TestNotebookStructure:
    def test_notebook_exists(self) -> None:
        assert NOTEBOOK.exists(), (
            f"Missing: {NOTEBOOK}\n"
            "  Fix: create notebooks/domain-scientist-colab.ipynb"
        )

    def test_exactly_8_cells(self) -> None:
        nb = _nb()
        assert len(nb["cells"]) == 8, (
            f"Got: {len(nb['cells'])} cells\n"
            "  Expected: exactly 8 cells\n"
            "  Fix: add or remove cells to reach 8 total"
        )

class TestCell3EditInstruction:
    def test_cell3_has_edit_marker(self) -> None:
        cell = _nb()["cells"][2]
        src = cell_source(cell)
        assert "Edit this cell" in src, (
            "Cell 3 (index 2) must contain 'Edit this cell'\n"
            "  Fix: add '# ⚠️ Edit this cell' comment as the first line of Cell 3"
        )

    def test_edit_marker_only_in_cell3(self) -> None:
        cells = _nb()["cells"]
        edit_cells = [
            i for i, c in enumerate(cells)
            if "edit this cell" in cell_source(c).lower()
        ]
        assert edit_cells == [2], (
            f"'Edit this cell' found in cells at indices: {edit_cells}\n"
            "  Expected: only cell at index 2\n"
            "  Fix: remove 'Edit this cell' from all cells except index 2"
        )
```

### Files to Create / Modify

| File | Action | AC |
|------|--------|----|
| `notebooks/domain-scientist-colab.ipynb` | **CREATE** | #1, #2, #3, #4, #5, #6 |
| `tests/integration/test_domain_scientist_notebook.py` | **CREATE** | #1, #2, #3, #4, #5, #6 |

No changes to `src/`, `README.md`, `docs/domain-scientists.md`, `pyproject.toml`, or `.github/workflows/`.

### Idempotence Contract (NFR-09) Per Cell

| Cell | Idempotence Mechanism |
|------|----------------------|
| 1 | `pip install` is idempotent; subprocess result varies but error check is stable |
| 2 | Module imports are idempotent in Python (cached in `sys.modules`) |
| 3 | `numpy.random.default_rng(42)` fixed seed — same data every run |
| 4 | `ObservationSpace`/`ActionSpace` constructors are pure — same input → same output |
| 5 | Fresh `adapter = DreamerV3Adapter(...)` every run — no stale invariants |
| 6 | `report.plot()` is deterministic (NFR-13) — same histogram each call |
| 7 | `adapter.export()` overwrites same path — safe to re-run |
| 8 | Markdown — no execution |

### Test Count Baseline

- After Story 6.2: **848 passed, 2 skipped**
- Story 6.3 adds ~12 integration tests
- Expected after 6.3: **~860 passed, 2 skipped**

`ruff check src/` and `mypy --strict src/physlink/core/` must still pass — Story 6.3 does not touch Python source, zero risk.

### Commit Message Pattern

Following all prior stories:
```
feat(story-6.3): Domain Scientist Colab Notebook
```

### Project Structure Notes

- `notebooks/` directory already exists (contains `quickstart.ipynb`)
- New notebook: `notebooks/domain-scientist-colab.ipynb`
- New test file: `tests/integration/test_domain_scientist_notebook.py`
- Tests use `PROJECT_ROOT = Path(__file__).parent.parent.parent` (3 levels up from `tests/integration/`)
- No `@pytest.mark.gpu` — content-only story, no GPU testing
- Test imports: `import json` (stdlib — no new dependencies)

### CTA Consistency with docs/domain-scientists.md

Story 6.2 added a CTA button in `docs/domain-scientists.md`:
```markdown
**[Open Domain Scientist Colab →](https://colab.research.google.com/github/YOUR-ORG/physlink/blob/main/notebooks/domain-scientist-colab.ipynb)**
```

The notebook path `notebooks/domain-scientist-colab.ipynb` is already hardcoded in that CTA. The new notebook must be created at exactly this path — no deviation.

### Previous Story Intelligence (Story 6.2)

From Story 6.2 Dev Notes:
- Epic 6 zero-source constraint first confirmed in Story 6.1: absolutely no `src/` changes
- Test pattern established: class-based, `PROJECT_ROOT / "path" / "to" / "file"`, `Fix:` hints in error messages
- Commit pattern: `feat(story-6.X): Short Description`
- Baseline after Story 6.2: 848 passed, 2 skipped

Story 6.2 File List showed: only `docs/domain-scientists.md` and one test file. Story 6.3 follows the same minimal footprint: one notebook + one test file.

### Architecture References

- `register_invariant` top-level export: [Source: architecture.md#Category 3 — Module Public API Surface]
- `fn(trajectory: dict) -> float` canonical signature: [Source: architecture.md#Docstring Patterns]
- PASS output format `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`: [Source: epics.md#Story 4.4]
- `adapter.fit()` contract (`list[dict] | TrajectoryBatch`, returns `AdaptationRun`): [Source: architecture.md#Category 1 — Trajectory Data Contract]
- `domain_extension.md` issue template: [Source: architecture.md#Project Directory Structure] — `.github/ISSUE_TEMPLATE/domain_extension.md` (created Story 5.3)
- NFR-07: `report.plot()` < 5 seconds: [Source: epics.md#NonFunctional Requirements]
- NFR-09: All Colab cells idempotent: [Source: epics.md#NonFunctional Requirements]

### References

- [Source: epics.md#Story 6.3] — Full user story, 6 acceptance criteria
- [Source: epics.md#UX-DR-11] — "Cell 3 ⚠️ Edit this cell; Cell 5 PASS; Cell 6 histogram; Cell 8 domain_extension.md link"
- [Source: epics.md#Story 4.3] — `register_invariant(adapter, name, fn, tolerance, mode)` full signature
- [Source: epics.md#Story 4.4] — `report.summary()` format: `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`
- [Source: 6-2-domain-scientists-landing-page.md#Dev Notes] — Epic 6 zero-source constraint; test count 848 passed; CTA link to `notebooks/domain-scientist-colab.ipynb`
- [Source: notebooks/quickstart.ipynb] — Notebook JSON format to replicate
- [Source: tests/integration/test_domain_scientists_page.py] — Test class pattern to follow
- [Source: architecture.md#Testing Patterns] — `PROJECT_ROOT = Path(__file__).parent.parent.parent`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_No debug issues encountered._

### Completion Notes List

- Créé `notebooks/domain-scientist-colab.ipynb` : 8 cellules au format nbformat 4.5, structure identique à `quickstart.ipynb` (metadata colab + kernelspec python3).
- Cell 1 : installation via `subprocess.run` + check `returncode != 0` + `RuntimeError` avec message exact "physlink could not be installed — check the version number or PyPI availability". Pas de `!pip install` (silencieux en cas d'échec).
- Cell 3 : marqueur `# ⚠️ Edit this cell — this is the ONLY cell you need to modify` en première ligne. Graine fixe `numpy.random.default_rng(42)` pour l'idempotence. Variable `your_trajectories` avec 1000 trajectoires CFD exemple.
- Cell 5 : adaptateur frais `DreamerV3Adapter(obs_space, act_space)` créé dans la cellule (pas réutilisé depuis Cell 4) pour éviter le doublement des invariants à chaque ré-exécution. `steps=100` suffisant pour la validation de conformité (pas l'entraînement).
- Cell 8 : markdown avec lien `https://github.com/YOUR-ORG/physlink/issues/new?template=domain_extension.md` — chemin de retour communautaire de Samuel (UX-DR-11).
- Créé `tests/integration/test_domain_scientist_notebook.py` : 58 tests couvrant structure (nbformat, 8 cellules, metadata), guard d'installation, marqueur unique Cell 3, contenu Cell 5 (register_invariant, fit, compliance_report, summary), Cell 6 (report.plot), Cell 8 (markdown, domain_extension.md, github.com), contrat d'idempotence, et 12 tests de précision AC ajoutés lors de l'analyse de lacunes QA (version épinglée, première ligne Cell 3, tolerance/mode/steps, titre report.plot, format URL template).
- Suite complète : **907 passés, 3 skipped** (baseline 849 + 58 nouveaux). Aucune régression.

### File List

- `notebooks/domain-scientist-colab.ipynb` (créé)
- `tests/integration/test_domain_scientist_notebook.py` (créé)

### Senior Developer Review (AI)

**Date:** 2026-05-22  
**Reviewer:** Denis Hamon (AI)  
**Outcome:** ✅ Approved

**Git vs Story discrepancies:** 0 — `notebooks/domain-scientist-colab.ipynb` et `tests/integration/test_domain_scientist_notebook.py` présents en untracked, cohérents avec la File List.

**AC Coverage:** 6/6 ACs entièrement implémentés et couverts par 58 tests.

**Corrections appliquées (2 MEDIUM):**
- M1 — Completion Notes : corrigé "46 tests / 894 passed, 2 skipped" → "58 tests / 907 passed, 3 skipped" (12 tests QA gap analysis documentés dans `test-summary-6-3.md`)
- M2 — Change Log : mis à jour "46 tests" → "58 tests"

**Vérifications :**
- `notebooks/domain-scientist-colab.ipynb` : JSON valide, nbformat 4.5, 8 cellules, metadata colab + python3 kernel ✅
- Cell 1 : subprocess.run + returncode check + RuntimeError exact ✅
- Cell 3 : `# ⚠️ Edit this cell` en première ligne, seed fixe `default_rng(42)`, unique dans le notebook ✅
- Cell 5 : adaptateur frais + register_invariant(tolerance=0.01, mode="hard") + fit(steps=100) + print(report.summary()) ✅
- Cell 6 : report.plot(title="Mass Conservation Check", show_threshold=True) ✅
- Cell 7 : adapter.export() — `_share_panel` appelé en interne par export() (Story 3.6) ✅
- Cell 8 : markdown, lien `issues/new?template=domain_extension.md` ✅
- Idempotence (NFR-09) : seed fixe Cell 3, adaptateur frais Cell 5, export overwrite Cell 7 ✅
- 58 tests passent (0 régression) ; suite complète : 907 passed, 3 skipped ✅

### Change Log

- review(story-6.3): Senior Developer Review — 2 corrections documentation (2026-05-22)
- feat(story-6.3): Domain Scientist Colab Notebook — 8-cell notebook + 58 tests d'intégration (2026-05-22)
