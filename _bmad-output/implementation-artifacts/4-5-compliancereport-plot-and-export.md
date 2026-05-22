# Story 4.5: ComplianceReport Plot and Export

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a domain scientist reviewing compliance results,
I want report.plot() to render a histogram inline in Colab and report.export() to save a JSON file,
so that I have both a visual proof and a machine-readable record of my invariant validation.

## Acceptance Criteria

1. **Given** a `ComplianceReport` object in a Colab environment
   **When** I call `report.plot(title="Mass Conservation Check", show_threshold=True)`
   **Then** a matplotlib histogram is rendered inline in the Colab output in < 5 seconds (NFR-07)
   **And** a vertical threshold line is drawn and clearly labeled on the histogram
   **And** the same plot is produced on repeated calls (NFR-13 — deterministic)

2. **Given** a `ComplianceReport` object
   **When** I call `report.export(path="./compliance_report.json")`
   **Then** a valid JSON file is written at the specified path
   **And** the JSON contains at minimum: invariant name, PASS/FAIL status, max_residual, threshold, violation count, and violation details
   **And** the file is parseable by Python's `json.load()` without errors

3. **Given** `compliance_report()` is called on 1000 trajectories in a CPU-only environment
   **When** the report is generated
   **Then** it completes in < 30 seconds (NFR-05)

4. **Given** Epic 4 is complete and all 7 public symbols are implemented
   **When** I access `physlink.__all__`
   **Then** it contains **exactly and only**: `doctor`, `ObservationSpace`, `ActionSpace`, `DreamerV3Adapter`, `register_invariant`, `ComplianceReport`, `PhysLinkError`
   **And** `test_api_stability.py` is updated to verify the full 7-symbol list with an equality check (final API stability gate)

## Tasks / Subtasks

- [x] Task 1: Extend `ComplianceReport.__init__` to accept `_residuals_by_invariant` (AC: #1, #2)
  - [x] Add optional parameter `_residuals_by_invariant: dict[str, list[float]] | None = None` as third positional param
  - [x] Store defensively: `self._residuals_by_invariant: dict[str, list[float]] = {k: list(v) for k, v in _residuals_by_invariant.items()} if _residuals_by_invariant is not None else {}`
  - [x] Update class docstring: add `_residuals_by_invariant` to Args section
  - [x] Backward-compatible: existing `ComplianceReport(_stats=[], _violation_list=[])` calls must still work (no positional change, new param is optional)

- [x] Task 2: Implement `ComplianceReport.plot()` method in `src/physlink/core/validation.py` (AC: #1)
  - [x] Signature: `def plot(self, title: str = "", show_threshold: bool = True) -> None:`
  - [x] Lazy import: `import matplotlib.pyplot as plt` INSIDE the method body (not at module level — avoids import failure in headless test environments for users without matplotlib)
  - [x] If `len(self._stats) == 0`: return early (nothing to plot — not an error)
  - [x] Create subplots: `fig, axes = plt.subplots(1, n_invariants, figsize=(6 * n_invariants, 4))` — wrap `axes` in list if `n_invariants == 1` (matplotlib returns a scalar, not list, for single subplot)
  - [x] If `title`: call `fig.suptitle(title)`
  - [x] For each `(ax, s)` in `zip(axes, self._stats)`: get `residuals = self._residuals_by_invariant.get(s["name"], [])`. If residuals: `ax.hist(residuals, bins=20, label="Residuals")`. Else: `ax.text(0.5, 0.5, "No residual data", ha="center", va="center", transform=ax.transAxes)`
  - [x] If `show_threshold`: `ax.axvline(x=s["threshold"], color="red", linestyle="--", label=f"threshold={s['threshold']:.4f}")` — draws labeled vertical threshold line
  - [x] `ax.set_title(f"{s['name']}: {'PASS' if s['violation_count'] == 0 else 'FAIL'}")`
  - [x] `ax.set_xlabel("Residual")`, `ax.set_ylabel("Count")`, `ax.legend()`
  - [x] After loop: `plt.tight_layout()`, then `plt.show()`
  - [x] Google-style docstring: Args (title, show_threshold), Raises (ImportError if matplotlib missing), Example

- [x] Task 3: Implement `ComplianceReport.export()` method in `src/physlink/core/validation.py` (AC: #2)
  - [x] Signature: `def export(self, path: str) -> None:`
  - [x] Import `json` at the top of the method body (standard library — not truly lazy, but consistent with `plot()` isolation pattern; alternatively import at module level — either is acceptable since json is stdlib)
  - [x] Build output list: one dict per invariant in `self._stats`. Each dict contains: `"invariant_name"`, `"status"` (`"PASS"` or `"FAIL"`), `"max_residual"`, `"threshold"`, `"violation_count"`, `"total"`, `"violations"` (list of violation dicts from `self._violation_list` filtered by invariant name)
  - [x] Write: `with open(path, "w", encoding="utf-8") as f: json.dump(output, f, indent=2)`
  - [x] Google-style docstring: Args (path), Raises (OSError), Example

- [x] Task 4: Update `DreamerV3Adapter.compliance_report()` in `src/physlink/adapters/dreamer.py` (AC: #1, #2, #3)
  - [x] Pass `_residuals_by_invariant` to `ComplianceReport`: add `_residuals_by_invariant={inv.name: list(self._invariant_residuals.get(inv.name, [])) for inv in self._invariants}` as the third argument
  - [x] The `stats` and `violation_list` construction logic is UNCHANGED — only add the third argument
  - [x] Verify the return line becomes: `return ComplianceReport(_stats=stats, _violation_list=violation_list, _residuals_by_invariant={...})`

- [x] Task 5: Add `TestComplianceReportPlot` class to `tests/unit/core/test_validation.py` (AC: #1)
  - [x] Add a module-level import: nothing new (matplotlib is imported lazily inside `plot()`)
  - [x] Use an `autouse` fixture to switch to Agg (non-interactive) backend and close figures after each test:
    ```python
    @pytest.fixture(autouse=True)
    def _agg_backend(self) -> Generator[None, None, None]:
        import matplotlib.pyplot as plt
        plt.switch_backend("Agg")
        yield
        plt.close("all")
    ```
  - [x] Add `from collections.abc import Generator` to test file imports (needed for fixture type hint)
  - [x] `test_plot_runs_without_error`: build report with 1 invariant + residuals, call `plot()` — must not raise
  - [x] `test_plot_no_threshold_runs_without_error`: `show_threshold=False` — must not raise
  - [x] `test_plot_with_title_runs_without_error`: `title="My Title"` — must not raise
  - [x] `test_plot_empty_stats_returns_early`: `ComplianceReport(_stats=[], _violation_list=[])` → `plot()` returns None without error (early return)
  - [x] `test_plot_no_residuals_shows_fallback`: `_residuals_by_invariant={}` (or not provided) → `plot()` runs without error (shows "No residual data" fallback)
  - [x] `test_plot_deterministic`: build same report, call `plot()` twice — must not raise on second call (NFR-13)
  - [x] `test_plot_multi_invariant`: `_stats` with 2 invariants — `plot()` runs without error

- [x] Task 6: Add `TestComplianceReportExport` class to `tests/unit/core/test_validation.py` (AC: #2)
  - [x] `test_export_creates_file(tmp_path)`: call `export(str(tmp_path / "report.json"))` — file exists after call
  - [x] `test_export_valid_json(tmp_path)`: call `export()`, then `json.load(f)` — must not raise
  - [x] `test_export_contains_required_fields(tmp_path)`: verify each entry has: `invariant_name`, `status`, `max_residual`, `threshold`, `violation_count`, `total`, `violations`
  - [x] `test_export_pass_status(tmp_path)`: 0 violations → `status == "PASS"`
  - [x] `test_export_fail_status(tmp_path)`: 1 violation → `status == "FAIL"`
  - [x] `test_export_violation_details(tmp_path)`: 1 violation → `violations` list has 1 entry with expected keys
  - [x] `test_export_zero_violations_empty_list(tmp_path)`: 0 violations → `violations == []`
  - [x] `test_export_multi_invariant(tmp_path)`: 2 invariants → JSON has 2 entries, one per invariant
  - [x] `test_export_deterministic(tmp_path)`: export twice → same JSON content (NFR-13)
  - [x] `test_export_empty_report(tmp_path)`: `_stats=[]` → JSON is `[]`, parseable by `json.load()`

- [x] Task 7: Add `TestComplianceReportStory45` class to `tests/unit/adapters/test_dreamer_cpu.py` (AC: #1, #2, #3)
  - [x] `test_compliance_report_has_residuals_by_invariant`: after `fit()`, `adapter.compliance_report()._residuals_by_invariant` is a dict and not empty
  - [x] `test_compliance_report_residuals_match_invariant_name`: residuals keyed by the invariant name registered via `register_invariant()`
  - [x] `test_compliance_report_export_produces_valid_json(tmp_path)`: adapter flow → `compliance_report()` → `export()` → `json.load()` succeeds
  - [x] `test_compliance_report_plot_runs_via_adapter` (with `_agg_backend` fixture from conftest or inline): adapter flow → `compliance_report()` → `plot()` does not raise

- [x] Task 8: Finalize `tests/integration/test_api_stability.py` — add `test_story45_final_api_symbols()` (AC: #4)
  - [x] Add function:
    ```python
    def test_story45_final_api_symbols() -> None:
        """Story 4.5: Epic 4 complete — verify EXACTLY 7 public symbols, no more, no less."""
        import physlink
        expected_all_7 = {
            "ActionSpace",
            "ComplianceReport",
            "DreamerV3Adapter",
            "ObservationSpace",
            "PhysLinkError",
            "doctor",
            "register_invariant",
        }
        actual = set(physlink.__all__)
        assert actual == expected_all_7, (
            f"Epic 4 final API surface mismatch.\n"
            f"  Got:      {sorted(actual)}\n"
            f"  Expected: {sorted(expected_all_7)}\n"
            f"  Fix:      physlink.__all__ must contain exactly these 7 symbols — "
            f"no extras, no omissions (AR-10)"
        )
    ```
  - [x] Remove the comment `# Epic 4 (Story 4.5) will update to assert the full 7-symbol set.` — it is now resolved

- [x] Task 9: Add NFR-05 benchmark to `tests/perf/test_nfr_benchmarks.py` (AC: #3)
  - [x] Add `TestComplianceReportNFR` class:
    - `test_compliance_report_1000_trajectories_under_30s(self, benchmark)`:
      1. Create `DreamerV3Adapter(obs, act)` with `joints=7`
      2. `register_invariant(adapter, "mass", fn, tolerance=0.01)`
      3. Directly set `adapter._invariant_residuals["mass"] = rng.random(1000).tolist()` (bypass `fit()` — tests report computation only; `fit()` requires GPU and is out of CPU CI scope)
      4. `result = benchmark(adapter.compliance_report)`
      5. `mean_s = benchmark.stats.stats.mean; assert mean_s < 30.0` — include Got/Expected/Fix in assertion message
      6. `assert result is not None` — sanity check

- [x] Task 10: Run full test suite — zero regressions (AC: all)
  - [x] `pytest tests/ -x -m "not gpu"` — 721 passed, 3 skipped (baseline 698 + 23 nouveaux)
  - [x] `ruff check src/` — zero warnings
  - [x] `mypy --strict src/physlink/core/` — zero type errors
  - [x] `mkdocs build --strict` — non installé localement (non bloquant pour CI)
  - [x] File List complete AND Change Log entry added before marking done

## Dev Notes

### What Story 4.5 Does and Does NOT Do

**This story implements:**
- `ComplianceReport.plot(title, show_threshold)` — lazy matplotlib histogram with threshold line
- `ComplianceReport.export(path)` — JSON file with full compliance data
- `_residuals_by_invariant` parameter added to `ComplianceReport.__init__` (backward-compatible)
- `DreamerV3Adapter.compliance_report()` updated to pass full residuals to `ComplianceReport`
- `test_api_stability.py` final equality check for exactly 7 symbols (AR-10 gate)
- NFR-05 benchmark: `compliance_report()` on 1000 trajectories < 30s

**Not in scope — do NOT implement:**
- No changes to `summary()` or `violations()` — they are complete and tested
- No changes to `register_invariant()` — it is complete
- No changes to `physlink.__init__` — the 7-symbol `__all__` is already correct (from Story 4.4)
- No changes to `DreamerV3Adapter.fit()` or `_apply_invariants()`
- Epic 5 or 6 content is NOT part of this story

### `ComplianceReport.__init__` Backward-Compatible Extension

**Current signature (Story 4.4):**
```python
def __init__(
    self,
    _stats: list[dict[str, Any]],
    _violation_list: list[dict[str, Any]],
) -> None:
```

**New signature (Story 4.5):**
```python
def __init__(
    self,
    _stats: list[dict[str, Any]],
    _violation_list: list[dict[str, Any]],
    _residuals_by_invariant: dict[str, list[float]] | None = None,
) -> None:
    self._stats: list[dict[str, Any]] = list(_stats)
    self._violation_list: list[dict[str, Any]] = list(_violation_list)
    self._residuals_by_invariant: dict[str, list[float]] = (
        {k: list(v) for k, v in _residuals_by_invariant.items()}
        if _residuals_by_invariant is not None
        else {}
    )
```

**Why defensive copy for `_residuals_by_invariant`:** Prevents mutation of the dict or inner lists after construction. Consistent with the pattern used for `_stats` and `_violation_list` in Story 4.4.

**Existing tests that create `ComplianceReport` directly (e.g., `test_story44_api_symbols`):**
```python
report = physlink.ComplianceReport(_stats=[], _violation_list=[])
```
These continue to work unchanged — `_residuals_by_invariant` defaults to `None` → stored as `{}`.

### `ComplianceReport.plot()` Implementation

```python
def plot(self, title: str = "", show_threshold: bool = True) -> None:
    """Render a matplotlib histogram of invariant residuals inline.

    Imports matplotlib lazily — avoids ImportError in headless environments
    for users who have not called plot() explicitly.

    Each invariant gets its own subplot. If ``show_threshold=True``, a red
    dashed vertical line is drawn at the tolerance threshold. Deterministic:
    same data produces the same plot (NFR-13).

    Args:
        title: Overall figure title. Defaults to empty string (no title).
        show_threshold: If True, draw a labeled vertical threshold line on
            each subplot. Defaults to True.

    Raises:
        ImportError: If matplotlib is not installed.

    Example:
        >>> report = adapter.compliance_report()
        >>> report.plot(title="Mass Conservation Check", show_threshold=True)
    """
    import matplotlib.pyplot as plt  # lazy import — optional dep

    n_invariants = len(self._stats)
    if n_invariants == 0:
        return

    fig, axes = plt.subplots(1, n_invariants, figsize=(6 * n_invariants, 4))
    if n_invariants == 1:
        axes = [axes]  # plt.subplots returns scalar when ncols=1

    if title:
        fig.suptitle(title)

    for ax, s in zip(axes, self._stats):
        residuals = self._residuals_by_invariant.get(s["name"], [])
        if residuals:
            ax.hist(residuals, bins=20, label="Residuals")
        else:
            ax.text(
                0.5, 0.5, "No residual data",
                ha="center", va="center",
                transform=ax.transAxes,
            )

        if show_threshold:
            ax.axvline(
                x=s["threshold"],
                color="red",
                linestyle="--",
                label=f"threshold={s['threshold']:.4f}",
            )

        status = "PASS" if s["violation_count"] == 0 else "FAIL"
        ax.set_title(f"{s['name']}: {status}")
        ax.set_xlabel("Residual")
        ax.set_ylabel("Count")
        ax.legend()

    plt.tight_layout()
    plt.show()
```

**Why lazy import:** Architecture states "Évite d'importer Pillow/matplotlib dans les jobs de test headless" [Source: architecture.md#Cross-Cutting Concerns, point 5]. The lazy import means `import physlink` never fails even if matplotlib is not installed.

**Single subplot scalar wrap:** `plt.subplots(1, 1, ...)` returns `(fig, Axes)` (scalar), not `(fig, [Axes])`. Wrapping in `[axes]` ensures the `zip(axes, self._stats)` loop works identically for 1 or N invariants.

**Why `plt.show()` and not `fig.show()`:** `plt.show()` triggers inline rendering in Colab (via IPython magic). `fig.show()` requires a display connection.

### `ComplianceReport.export()` Implementation

```python
def export(self, path: str) -> None:
    """Write a JSON compliance report to disk.

    Produces a list of per-invariant dicts containing summary statistics and
    full violation details. The output is parseable by ``json.load()`` with
    no custom decoder needed (all values are JSON-native types).

    Args:
        path: File path for the output JSON file. Parent directory must exist.

    Raises:
        OSError: If the file cannot be written (permission error, missing
            parent directory, disk full, etc.).

    Example:
        >>> report = adapter.compliance_report()
        >>> report.export("./compliance_report.json")
        >>> import json
        >>> with open("./compliance_report.json") as f:
        ...     data = json.load(f)
        >>> data[0]["status"]  # "PASS" or "FAIL"
        'PASS'
    """
    import json

    output = []
    for s in self._stats:
        status = "PASS" if s["violation_count"] == 0 else "FAIL"
        violations = [
            v for v in self._violation_list
            if v["invariant_name"] == s["name"]
        ]
        output.append({
            "invariant_name": s["name"],
            "status": status,
            "max_residual": s["max_residual"],
            "threshold": s["threshold"],
            "violation_count": s["violation_count"],
            "total": s["total"],
            "violations": violations,
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
```

**JSON structure (one element per invariant):**
```json
[
  {
    "invariant_name": "mass_conservation",
    "status": "PASS",
    "max_residual": 0.0042,
    "threshold": 0.01,
    "violation_count": 0,
    "total": 50,
    "violations": []
  }
]
```

**Why not raise when empty (`_stats=[]`):** An empty report exports as `[]` — a valid, parseable JSON array. This is consistent with how `summary()` returns `""` and `violations()` returns `[]` for empty reports.

### Update to `DreamerV3Adapter.compliance_report()`

**Only change: add `_residuals_by_invariant=` argument to the return statement.**

Current return (line ~490 in dreamer.py):
```python
return ComplianceReport(_stats=stats, _violation_list=violation_list)
```

New return:
```python
return ComplianceReport(
    _stats=stats,
    _violation_list=violation_list,
    _residuals_by_invariant={
        inv.name: list(self._invariant_residuals.get(inv.name, []))
        for inv in self._invariants
    },
)
```

**Do NOT change** the `stats` or `violation_list` computation — only the return statement is modified. The `list()` copy ensures the caller cannot mutate the adapter's internal residuals by modifying the report.

### Test Fixture for `plot()` Tests (Headless CI)

The `TestComplianceReportPlot` tests must run headlessly in GitHub Actions (no display server). The required fixture pattern:

```python
from __future__ import annotations
from collections.abc import Generator

# in TestComplianceReportPlot:
@pytest.fixture(autouse=True)
def _agg_backend(self) -> Generator[None, None, None]:
    """Switch to non-interactive backend and close all figures after each test."""
    import matplotlib.pyplot as plt
    plt.switch_backend("Agg")  # safe to call even after pyplot is imported
    yield
    plt.close("all")  # prevent figure accumulation across tests
```

**Why `switch_backend("Agg")` instead of `matplotlib.use("Agg")`:**
- `matplotlib.use()` raises if called after pyplot has been imported (or emits a warning in newer versions)
- `plt.switch_backend("Agg")` is safe at any time
- The Agg backend renders to memory buffer — no display server required

**Where to place this fixture:** Inside `TestComplianceReportPlot` class only — not module-level, not in conftest.py. Other test classes in the same file do not use matplotlib.

**Add `from collections.abc import Generator` to the imports at the top of `test_validation.py`** (needed for the fixture type hint). If `Generator` is already imported, skip this.

### `test_api_stability.py` — Final 7-Symbol Equality Check

Story 4.5 finalizes the API stability gate. The check uses `==` (not `issubset`), verifying no extras were accidentally added:

```python
def test_story45_final_api_symbols() -> None:
    """Story 4.5: Epic 4 complete — physlink.__all__ must be EXACTLY these 7 symbols."""
    import physlink

    expected_all_7 = {
        "ActionSpace",
        "ComplianceReport",
        "DreamerV3Adapter",
        "ObservationSpace",
        "PhysLinkError",
        "doctor",
        "register_invariant",
    }
    actual = set(physlink.__all__)
    assert actual == expected_all_7, (
        f"Epic 4 final API surface mismatch.\n"
        f"  Got:      {sorted(actual)}\n"
        f"  Expected: {sorted(expected_all_7)}\n"
        f"  Fix:      physlink.__all__ must contain exactly these 7 symbols — "
        f"no extras, no omissions (AR-10)"
    )
```

**Note:** `physlink.__init__.py` already has the correct 7 symbols from Story 4.4. This test does not require any changes to `__init__.py` — it only adds the verification.

**Remove the stale comment** in `test_api_stability.py` (line ~83):
```python
# Epic 4 (Story 4.5) will update to assert the full 7-symbol set.
```
This is now resolved.

### NFR-05 Benchmark Design

The performance spec is: `compliance_report()` on 1000 trajectories < 30 seconds. The `fit()` call requires GPU and is out of CPU CI scope; the benchmark directly injects synthetic residuals to test the report computation path only.

```python
class TestComplianceReportNFR:
    """NFR-05: compliance_report() on 1000 trajectories must complete in < 30 seconds."""

    def test_compliance_report_1000_trajectories_under_30s(
        self, benchmark: pytest.FixtureRequest
    ) -> None:
        """NFR-05 CPU gate for compliance_report() computation time.

        Bypasses fit() (GPU-required) by directly populating _invariant_residuals
        with 1000 synthetic residuals. Tests the report computation path only.

        Args:
            benchmark: pytest-benchmark fixture.
        """
        import numpy as np
        from physlink import ActionSpace, DreamerV3Adapter, ObservationSpace, register_invariant

        obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        adapter = DreamerV3Adapter(obs, act)

        def mass_conservation(trajectory: dict) -> float:
            return abs(trajectory.get("mass_in", 0.0) - trajectory.get("mass_out", 0.0))

        register_invariant(adapter, "mass_conservation", mass_conservation, tolerance=0.01)

        rng = np.random.default_rng(42)
        adapter._invariant_residuals["mass_conservation"] = rng.random(1000).tolist()

        result = benchmark(adapter.compliance_report)
        mean_s = benchmark.stats.stats.mean
        assert mean_s < 30.0, (
            f"compliance_report() NFR-05 violation: mean {mean_s:.4f}s (limit: 30.0s)\n"
            f"  Got:      {mean_s:.4f}s mean on 1000 trajectories\n"
            f"  Expected: < 30.0s (NFR-05, CPU-only CI threshold)\n"
            f"  Fix:      optimize compliance_report() in adapters/dreamer.py"
        )
        assert result is not None
```

**Why direct `adapter._invariant_residuals` injection:** The compliance_report() computation is pure Python — it reads `_invariants` and `_invariant_residuals`, does arithmetic, and builds a `ComplianceReport`. There is no GPU dependency in this path. By injecting residuals directly, we test exactly the code path that needs the NFR guarantee, without the T4 requirement of `fit()`.

### Architecture Compliance Checklist for This Story

- `plot()` and `export()` added to `ComplianceReport` in `core/validation.py` ✅ (correct location)
- `import matplotlib.pyplot as plt` is INSIDE `plot()` body — lazy import ✅ (architecture Cross-Cutting Concern 5)
- `import json` in `export()` — standard library, no architecture constraints ✅
- `core/validation.py` still has ZERO imports from `adapters/` ✅ (AST boundary test will pass)
- `from __future__ import annotations` already present in `core/validation.py` ✅
- Google-style docstrings with Args, Raises, Example on `plot()` and `export()` ✅ (AR-11)
- `X | Y` type syntax: `dict[str, list[float]] | None` ✅
- No `Union`, `Optional`, `List` legacy typing ✅
- `_residuals_by_invariant` is private (single underscore) — not a public method ✅
- Naming: methods `plot` (snake_case) ✅, parameter `title` / `show_threshold` (full names, no abbrev) ✅
- `physlink.__all__` already has exactly 7 symbols — no `__init__.py` change needed ✅

### Previous Story Intelligence (Story 4.4)

Critical patterns established that MUST be respected:
- `ComplianceReport` is a plain class (NOT a frozen dataclass) — `list` fields are unhashable
- Defensive copying in `__init__` is mandatory for all collection fields
- `mypy --strict` on `core/`: all type annotations must be fully explicit. Use `dict[str, list[float]]` not `dict` — the `[type-arg]` rule (ANN401 equivalent) will catch missing generics
- `ruff check src/` strict: `ANN401` (no `Any` in public signatures) means the new `_residuals_by_invariant` parameter must be typed `dict[str, list[float]] | None` (not `Any`)
- `test_core_boundary.py` uses AST walking — even `TYPE_CHECKING` imports from `adapters/` in `core/` are caught. `ComplianceReport` must have ZERO imports from `adapters/`
- File List + Change Log MUST be complete before marking done
- Commit message pattern: `feat(story-4.5): ComplianceReport Plot and Export`
- Total test count before this story: 698 passed, 3 skipped

### Data Flow — What `_residuals_by_invariant` Contains

After `DreamerV3Adapter.compliance_report()` with Story 4.5 changes:
```python
adapter._invariant_residuals = {
    "mass_conservation": [0.002, 0.015, 0.001, 0.009],  # all 4 residuals
    "energy_check": [0.02, 0.01, 0.06, 0.03],           # all 4 residuals
}

# compliance_report() now builds:
report._residuals_by_invariant = {
    "mass_conservation": [0.002, 0.015, 0.001, 0.009],  # copy
    "energy_check": [0.02, 0.01, 0.06, 0.03],           # copy
}

# report.plot() uses these to build histograms — shows full distribution including non-violations
# report.export() uses _stats + _violation_list (unchanged) — violations only where residual > tolerance
```

**Why full residuals for plot, violations-only for export:** The histogram shows the distribution of ALL residuals to contextualize where violations are. The JSON export focuses on actionable data (violations + summary stats) — full residual arrays would bloat the JSON without adding compliance-specific value.

### Project Structure Notes

- `ComplianceReport.plot()` and `ComplianceReport.export()` — in `src/physlink/core/validation.py` (existing file, add methods to existing class) [Source: architecture.md#Category 3 + Structure Patterns]
- Tests for `plot()` and `export()` — in `tests/unit/core/test_validation.py` (existing file, add new test classes) [Source: architecture.md#Structure Patterns]
- Adapter integration tests — in `tests/unit/adapters/test_dreamer_cpu.py` (existing file, add `TestComplianceReportStory45`)
- NFR benchmark — in `tests/perf/test_nfr_benchmarks.py` (existing file, add `TestComplianceReportNFR`)
- No new files needed — all additions are to existing files

### References

- [Source: epics.md#Story 4.5] — Acceptance Criteria, user story statement
- [Source: epics.md#FR-07] — `ComplianceReport` full spec: `plot()`, `export()`, `< 5s` (NFR-07), deterministic (NFR-13)
- [Source: epics.md#NFR-05] — compliance_report() on 1000 trajectories < 30 seconds
- [Source: epics.md#NFR-07] — report.plot() renders inline < 5 seconds
- [Source: epics.md#NFR-13] — deterministic: same data, same result
- [Source: epics.md#AR-10] — exactly 7 symbols in physlink.__all__
- [Source: architecture.md#Category 3] — ComplianceReport in physlink.core.validation, 7-symbol __all__
- [Source: architecture.md#Cross-Cutting Concerns, point 5] — matplotlib lazy import pattern
- [Source: architecture.md#Docstring Patterns] — Google style, Args/Raises/Example mandatory
- [Source: architecture.md#Type Annotation Patterns] — X|Y syntax, from __future__ import annotations
- [Source: architecture.md#Testing Patterns] — no conftest.py in subdirs, single conftest at root
- [Source: implementation-artifacts/4-4-compliancereport-summary-and-violations.md] — `_stats`/`_violation_list` structure, mypy strict type-arg rule, defensive copy pattern, AST boundary workaround
- [Source: tests/integration/test_api_stability.py:78-83] — stale comment to remove after finalizing

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Toutes les tâches 1–10 implémentées et validées en une seule session.
- `ComplianceReport.__init__` étendu avec `_residuals_by_invariant` (backward-compatible, copie défensive).
- `ComplianceReport.plot()` : import lazy matplotlib, gestion scalar subplot (n=1), fallback "No residual data", `plt.show()` pour Colab inline.
- `ComplianceReport.export()` : JSON list par invariant avec champs complets, `json.load()` sans décodeur.
- `DreamerV3Adapter.compliance_report()` : seul le `return` modifié, passe `_residuals_by_invariant` complet.
- 23 nouveaux tests ajoutés (7 plot + 10 export + 4 adapter + 1 API stability + 1 NFR). Total : 721 passed, 3 skipped.
- `ruff check src/` : zéro warning. `mypy --strict src/physlink/core/` : zéro erreur.
- Benchmark NFR-05 : `compliance_report()` sur 1000 trajectoires ≈ 0.55ms (limite 30s) — conforme.
- Commentaire stale `# Epic 4 (Story 4.5) will update...` supprimé de `test_api_stability.py`.

### File List

- `src/physlink/core/validation.py`
- `src/physlink/adapters/dreamer.py`
- `tests/unit/core/test_validation.py`
- `tests/unit/adapters/test_dreamer_cpu.py`
- `tests/integration/test_api_stability.py`
- `tests/perf/test_nfr_benchmarks.py`
- `_bmad-output/implementation-artifacts/4-5-compliancereport-plot-and-export.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Senior Developer Review (AI)

**Reviewer:** Denis (AI Review) — 2026-05-22

**Verdict: APPROVED** — 0 critical issues. 2 medium issues fixed automatically.

**Findings fixed:**
- M1 [test_validation.py, test_dreamer_cpu.py] — `tmp_path` annotated as `pytest.MonkeyPatch` instead of `pathlib.Path`. Fixed to `Path` (consistent with established convention). Added `from pathlib import Path` import to `test_validation.py`.
- M2 [test_validation.py:TestComplianceReportPlot, test_dreamer_cpu.py:test_compliance_report_plot_runs_via_adapter] — `plt.show()` in Agg backend generates `UserWarning: FigureCanvasAgg is non-interactive`. Added `@pytest.mark.filterwarnings("ignore::UserWarning")` to suppress the known warning in headless test contexts.

**Verified:** 721 passed, 3 skipped, ruff zero warnings, mypy strict zero errors. All ACs and [x] tasks confirmed implemented.

### Change Log

- 2026-05-22: AI Review — fixed `tmp_path: pytest.MonkeyPatch` → `Path` (M1) and added `@pytest.mark.filterwarnings` for plt.show() UserWarning in Agg backend (M2). Story → done.
- 2026-05-22: Story 4.5 implémentée — `ComplianceReport.plot()` (histogramme matplotlib lazy) et `ComplianceReport.export()` (JSON complet) ajoutés à `core/validation.py`. `DreamerV3Adapter.compliance_report()` passe désormais `_residuals_by_invariant`. Gate de stabilité API étendu à l'égalité exacte de 7 symboles (AR-10). Benchmark NFR-05 ajouté. 23 nouveaux tests — 721 total, 3 skipped, zéro régression.
