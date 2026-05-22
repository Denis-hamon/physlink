# Story 4.4: ComplianceReport Summary and Violations

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a domain scientist who ran an adaptation with invariant checks,
I want adapter.compliance_report() to return a pure data object with human-readable summary and violation details,
so that I can verify my trajectories never violated physics without parsing raw logs.

## Acceptance Criteria

1. **Given** invariants have been registered and `adapter.fit()` has been called
   **When** I call `adapter.compliance_report()`
   **Then** the return value is a `ComplianceReport` pure data object (no side effects on call)
   **And** `ComplianceReport` is exported from `physlink.__init__`

2. **Given** a `ComplianceReport` object
   **When** I call `report.summary()`
   **Then** the return is a string in the exact format: `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`
   **And** the same data produces the same summary on repeated calls (NFR-13 — deterministic)

3. **Given** a `ComplianceReport` with at least one violation
   **When** I call `report.violations()`
   **Then** the return is a list where each entry contains: trajectory index, residual value, invariant name, and a "Possible cause:" text string
   **And** no Python stack trace appears as part of the violation output

4. **Given** a `ComplianceReport` with zero violations
   **When** I call `report.summary()`
   **Then** the string contains `violations=0/N` and `PASS`

## Tasks / Subtasks

- [x] Task 1: Implement `ComplianceReport` class in `src/physlink/core/validation.py` (AC: #1, #2, #3, #4)
  - [x] Add `ComplianceReport` class (NOT a frozen dataclass — stores mutable list internally; plain class with `__init__`)
  - [x] `__init__(self, _stats: list[dict], _violation_list: list[dict]) -> None` — copy both lists defensively (no mutation risk)
  - [x] `summary(self) -> str` — one line per invariant: `f"{name}: {status} (max_residual={max_r:.4f}, threshold={thr:.4f}, violations={vcount}/{total})"` joined with `"\n"`. `status="PASS"` if `violation_count == 0`, `"FAIL"` otherwise
  - [x] `violations(self) -> list[dict]` — return list of dicts with keys: `"invariant_name"`, `"trajectory_idx"`, `"residual"`, `"possible_cause"`; sorted by `(invariant_name, trajectory_idx)` for determinism (NFR-13)
  - [x] Google-style docstring on class and both public methods: Args, Returns, Example sections
  - [x] No torch import, no adapters/ import — pure data object ✅ (AST + boundary tests pass)
  - [x] `ComplianceReport` is a public name — no leading underscore

- [x] Task 2: Add `compliance_report()` method to `DreamerV3Adapter` in `src/physlink/adapters/dreamer.py` (AC: #1, #2, #3, #4)
  - [x] Signature: `def compliance_report(self) -> ComplianceReport:`
  - [x] Import: `from physlink.core.validation import ComplianceReport` at top of file (adapters → core is ✅ allowed)
  - [x] Build `_stats` list: for each `_InvariantRecord` in `self._invariants`, read `self._invariant_residuals.get(inv.name, [])` and compute: `max_residual = max(residuals) if residuals else 0.0`, `violation_count = sum(1 for r in residuals if r > inv.tolerance)`, `total = len(residuals)`
  - [x] Build `_violation_list`: for each invariant, enumerate residuals; if `residual > inv.tolerance`, append `{"invariant_name": inv.name, "trajectory_idx": idx, "residual": residual, "possible_cause": f"Residual {residual:.4f} exceeds tolerance {inv.tolerance:.4f}."}`
  - [x] Return `ComplianceReport(_stats=stats_list, _violation_list=violation_list)`
  - [x] Handle edge case: no invariants registered → return `ComplianceReport(_stats=[], _violation_list=[])` (empty report, not an error)
  - [x] Handle edge case: `fit()` not yet called (`_invariant_residuals` empty) → each invariant has `total=0`, `violation_count=0`, `max_residual=0.0`
  - [x] Google-style docstring: Args (none), Returns (ComplianceReport), Raises (none — pure computation), Example

- [x] Task 3: Export `ComplianceReport` from `src/physlink/__init__.py` (AC: #1, architecture AR-10)
  - [x] Add `from physlink.core.validation import ComplianceReport, register_invariant` (combine on one import line — follows existing pattern, isort sorted)
  - [x] Add `"ComplianceReport"` to `__all__` — placed after `"ActionSpace"`, before `"DreamerV3Adapter"` (alphabetical order)
  - [x] Note: full 7-symbol `test_api_stability.py` verification is deferred to Story 4.5; adding `ComplianceReport` now is correct (6 symbols total after this story)

- [x] Task 4: Create/update `tests/unit/core/test_validation.py` — add `TestComplianceReport*` classes (AC: #1, #2, #3, #4)
  - [x] `TestComplianceReportSummaryPass`:
    - `test_summary_pass_format` — zero violations, verify `"name: PASS (max_residual=0.0000, threshold=0.0100, violations=0/5)"`
    - `test_summary_deterministic` — call `summary()` twice, assert same result (NFR-13)
    - `test_summary_zero_violations_contains_pass` — AC #4: `"PASS"` in summary
    - `test_summary_zero_violations_count` — `"violations=0/"` in summary string
  - [x] `TestComplianceReportSummaryFail`:
    - `test_summary_fail_format` — 2 violations of 5 trajectories → `"FAIL"` and `"violations=2/5"`
    - `test_summary_fail_max_residual` — max_residual reflects actual max of all residuals
  - [x] `TestComplianceReportViolations`:
    - `test_violations_returns_list` — is a list
    - `test_violations_entry_keys` — each entry has keys: `"invariant_name"`, `"trajectory_idx"`, `"residual"`, `"possible_cause"`
    - `test_violations_no_stack_trace_in_possible_cause` — `"Traceback"` not in any `possible_cause`
    - `test_violations_trajectory_idx_matches` — idx matches position in residuals list
    - `test_violations_residual_value_correct` — residual matches what was stored
    - `test_violations_deterministic` — call `violations()` twice, same result (NFR-13)
  - [x] `TestComplianceReportEmpty`:
    - `test_empty_stats_summary` — empty `_stats` list → `summary()` returns `""`
    - `test_empty_violations` — empty `_violation_list` → `violations()` returns `[]`
  - [x] `TestComplianceReportMultiInvariant`:
    - `test_summary_multi_invariant_multiline` — 2 invariants → 2 lines in `summary()`
    - `test_violations_multi_invariant_combined` — violations from both invariants in one list

- [x] Task 5: Update `tests/unit/adapters/test_dreamer_cpu.py` — add `TestComplianceReportStory44` class (AC: #1, #2, #3, #4)
  - [x] `test_compliance_report_returns_compliance_report` — after `fit()`, `compliance_report()` returns `ComplianceReport` instance
  - [x] `test_compliance_report_no_side_effects` — calling `compliance_report()` twice returns same data, no state mutation
  - [x] `test_compliance_report_pass_when_no_violations` — fn always returns 0.0, `fit()`, then `report.summary()` contains `"PASS"`
  - [x] `test_compliance_report_fail_when_violations` — fn returns 1.0 (> tolerance 0.01, soft mode), `fit()`, then `report.summary()` contains `"FAIL"`
  - [x] `test_compliance_report_violations_list_non_empty_on_fail` — violations() has entries for soft-mode invariant
  - [x] `test_compliance_report_no_invariants_empty_report` — adapter with no invariants → `compliance_report()` returns empty ComplianceReport (no error)
  - [x] `test_compliance_report_before_fit_no_error` — `compliance_report()` before `fit()` → returns empty/zero stats (no crash)
  - [x] `test_compliance_report_hard_mode_violations_tracked` — hard-mode invariant, some violating trajectories → residuals stored for violations that were evaluated BEFORE rejection

- [x] Task 6: Update `tests/integration/test_api_stability.py` — add `ComplianceReport` (AC: #1)
  - [x] Add `test_story44_api_symbols()` function verifying `ComplianceReport` is in `physlink.__all__` and is importable from `physlink`
  - [x] Note: leave full 7-symbol verification for Story 4.5 (`test_api_stability.py` will be finalized then)

- [x] Task 7: Run full test suite — zero regressions (AC: all)
  - [x] `pytest tests/ -x -m "not gpu"` — 688 passed, 3 skipped, 0 failures
  - [x] `ruff check src/` — zero warnings
  - [x] `mkdocs build --strict` — docs build successfully
  - [x] File List complete AND Change Log entry added before marking done

## Dev Notes

### What Story 4.4 Does and Does NOT Do

**This story implements:**
- `ComplianceReport` pure data class in `core/validation.py` — `summary()` and `violations()` methods
- `DreamerV3Adapter.compliance_report()` method in `adapters/dreamer.py` — reads `_invariant_residuals` and `_invariants`, builds and returns `ComplianceReport`
- `ComplianceReport` exported from `physlink.__init__`

**Explicitly deferred — do NOT implement:**
- `report.plot()` — matplotlib histogram with threshold line → Story 4.5
- `report.export(path)` — JSON file → Story 4.5
- `test_api_stability.py` full 7-symbol verification → Story 4.5
- NFR-05 benchmark (`compliance_report()` on 1000 trajectories < 30s) → Story 4.5 (perf tests)

### `ComplianceReport` Class Design

```python
# src/physlink/core/validation.py (append after register_invariant)

class ComplianceReport:
    """Pure data object summarizing invariant compliance across adaptation trajectories.

    Constructed by ``DreamerV3Adapter.compliance_report()`` after ``fit()`` is called.
    All methods are deterministic and side-effect-free (NFR-13).

    Args:
        _stats: Per-invariant summary dicts with keys:
            ``name`` (str), ``max_residual`` (float), ``threshold`` (float),
            ``violation_count`` (int), ``total`` (int).
        _violation_list: Per-violation dicts with keys:
            ``invariant_name`` (str), ``trajectory_idx`` (int),
            ``residual`` (float), ``possible_cause`` (str).

    Example:
        >>> report = adapter.compliance_report()
        >>> print(report.summary())
        mass_conservation: PASS (max_residual=0.0042, threshold=0.0100, violations=0/50)
        >>> violations = report.violations()
        >>> violations  # empty list when no violations
        []
    """

    def __init__(
        self,
        _stats: list[dict],
        _violation_list: list[dict],
    ) -> None:
        self._stats: list[dict] = list(_stats)
        self._violation_list: list[dict] = list(_violation_list)

    def summary(self) -> str:
        """Return a human-readable compliance summary string.

        One line per invariant in format:
        ``"name: PASS (max_residual=X.XXXX, threshold=Y.YYYY, violations=Z/N)"``

        Returns:
            Formatted summary string. Empty string if no invariants registered.
            Multiple invariants produce one line each, joined with newline.
        """
        lines = []
        for s in self._stats:
            status = "PASS" if s["violation_count"] == 0 else "FAIL"
            lines.append(
                f"{s['name']}: {status} ("
                f"max_residual={s['max_residual']:.4f}, "
                f"threshold={s['threshold']:.4f}, "
                f"violations={s['violation_count']}/{s['total']})"
            )
        return "\n".join(lines)

    def violations(self) -> list[dict]:
        """Return a list of all invariant violations detected during fit().

        Returns:
            List of violation dicts, each containing:
            - ``invariant_name`` (str): Name of the violated invariant.
            - ``trajectory_idx`` (int): 0-based index of the violating trajectory.
            - ``residual`` (float): The residual value that exceeded tolerance.
            - ``possible_cause`` (str): Human-readable diagnostic message.
            Sorted by ``(invariant_name, trajectory_idx)`` for determinism.
            Empty list when no violations occurred.
        """
        return sorted(
            list(self._violation_list),
            key=lambda v: (v["invariant_name"], v["trajectory_idx"]),
        )
```

**Why plain class, not frozen dataclass:** `_stats` and `_violation_list` are lists, which are unhashable and cannot be fields of a frozen dataclass without custom `__hash__`. A plain class with defensive copying in `__init__` achieves the same immutability guarantees without complexity.

### `DreamerV3Adapter.compliance_report()` Method Design

```python
# src/physlink/adapters/dreamer.py — add to imports at top of file:
from physlink.core.validation import ComplianceReport  # Story 4.4

# Add method to DreamerV3Adapter class:
def compliance_report(self) -> ComplianceReport:
    """Return a ComplianceReport summarizing invariant compliance from the last fit().

    Reads ``_invariants`` and ``_invariant_residuals`` stored on the adapter.
    Pure computation — no side effects, safe to call multiple times.

    Returns:
        ComplianceReport with per-invariant summary and violation details.
        Empty report (no entries) if no invariants are registered.
        Zero-trajectory report if fit() has not yet been called.

    Example:
        >>> register_invariant(adapter, "mass", fn, tolerance=0.01)
        >>> adapter.fit(trajectories, steps=100)
        >>> report = adapter.compliance_report()
        >>> print(report.summary())
        mass: PASS (max_residual=0.0042, threshold=0.0100, violations=0/10)
    """
    stats: list[dict] = []
    violation_list: list[dict] = []

    for inv in self._invariants:
        residuals = self._invariant_residuals.get(inv.name, [])
        max_residual = max(residuals) if residuals else 0.0
        violation_count = sum(1 for r in residuals if r > inv.tolerance)
        total = len(residuals)

        stats.append({
            "name": inv.name,
            "max_residual": max_residual,
            "threshold": inv.tolerance,
            "violation_count": violation_count,
            "total": total,
        })

        for idx, residual in enumerate(residuals):
            if residual > inv.tolerance:
                violation_list.append({
                    "invariant_name": inv.name,
                    "trajectory_idx": idx,
                    "residual": residual,
                    "possible_cause": (
                        f"Residual {residual:.4f} exceeds tolerance {inv.tolerance:.4f}."
                    ),
                })

    return ComplianceReport(_stats=stats, _violation_list=violation_list)
```

**Where to place in `dreamer.py`:** Add `compliance_report()` immediately after `_apply_invariants()` and before `load_checkpoint()`, so invariant-related methods are grouped together.

**Import placement:** Add `from physlink.core.validation import ComplianceReport` at the top of `dreamer.py` alongside the existing `from physlink.core.validation import ...` imports (if any) or with the other core imports. `adapters/ → core/` is explicitly allowed per `test_core_boundary.py`.

### `src/physlink/__init__.py` Update

Current state (from Story 4.3):
```python
from physlink.core.validation import register_invariant  # Story 4.3
# Story 4.4: ComplianceReport
```

Update to:
```python
from physlink.core.validation import register_invariant, ComplianceReport  # Story 4.3 + 4.4
```

And in `__all__`, add `"ComplianceReport"` — check existing `__all__` order and insert respecting isort. After Story 4.4, `__all__` has 6 symbols:
```python
__all__ = [
    "ComplianceReport",      # Story 4.4
    "ActionSpace",
    "DreamerV3Adapter",
    "ObservationSpace",
    "PhysLinkError",
    "doctor",
    "register_invariant",    # Story 4.3
]
```
(actual order may vary — follow whatever isort/alphabetical order was established by Story 4.3's `__all__`)

### Architecture Compliance Checklist for This Story

- `ComplianceReport` in `core/validation.py` → no torch, no adapters/ import ✅ (AST test passes)
- `adapters/dreamer.py` imports `ComplianceReport` from `core/validation.py` ✅ (adapters → core allowed)
- `physlink/__init__.py` exports `ComplianceReport` ✅ (AR-10: one of the 7 public symbols)
- `from __future__ import annotations` already present in `core/validation.py` ✅
- Google-style docstrings with Args, Returns, Example on all public methods ✅ (AR-11)
- `X | Y` type syntax (Python 3.10+) ✅
- No `Union`, `Optional`, `List` legacy typing ✅
- No `Any` in public signatures (ANN401 rule) — use specific types ✅
- Naming: `ComplianceReport` (PascalCase class), `compliance_report` (snake_case method) ✅
- Error messages follow Got/Expected/Fix template ✅ (n/a — ComplianceReport has no error paths)
- `"ComplianceReport"` added to `physlink.__all__` ✅

### `test_api_stability.py` — `test_story44_api_symbols()`

```python
def test_story44_api_symbols() -> None:
    """Story 4.4 adds ComplianceReport to the public API (6 symbols total)."""
    import physlink
    assert "ComplianceReport" in physlink.__all__
    assert hasattr(physlink, "ComplianceReport")
    # Verify it is instantiatable (pure data class, not abstract)
    report = physlink.ComplianceReport(_stats=[], _violation_list=[])
    assert isinstance(report, physlink.ComplianceReport)
```

### Previous Story Intelligence (Story 4.3)

From Story 4.3 completion notes and debug log:
- `test_core_boundary.py` uses AST walking and catches even `TYPE_CHECKING` imports — `ComplianceReport` in `core/validation.py` must have ZERO imports from `adapters/`. ✅ (ComplianceReport is a pure data class, needs nothing from adapters/)
- `_reset_training_state()` was placed BEFORE `_apply_invariants()` — do NOT reset residuals in `compliance_report()`; the method reads state from the last `fit()` call (it's a pure reader)
- `ruff check src/` must show zero warnings — check `ANN401` (no `Any` in signatures), `from __future__ import annotations` already present
- File List + Change Log MUST be complete before marking done
- Commit message pattern: `feat(story-4.4): ComplianceReport Summary and Violations`
- 663 tests pass as of Story 4.3 — maintain zero regressions

### Data Flow — What `_invariant_residuals` Contains

After `adapter.fit(trajectories, ...)` with invariants registered:
```
adapter._invariants = [
    _InvariantRecord(name="mass_conservation", fn=..., tolerance=0.01, mode="hard"),
    _InvariantRecord(name="energy_check", fn=..., tolerance=0.05, mode="soft"),
]

adapter._invariant_residuals = {
    "mass_conservation": [0.002, 0.015, 0.001, 0.009],  # 4 residuals (1 violation: idx 1)
    "energy_check": [0.02, 0.01, 0.06, 0.03],           # 4 residuals (1 violation: idx 2)
}
```

**Hard-mode caveat:** For `mode="hard"`, rejected trajectories are still evaluated and their residuals ARE stored in `_invariant_residuals` before filtering (see `_apply_invariants()`). So `compliance_report()` correctly reports them as violations even though they were excluded from training.

**Empty `_invariant_residuals`:** If `fit()` was never called, `_invariant_residuals` is `{}`. Then `compliance_report()` returns a report where each invariant has `total=0`, `violation_count=0`, `max_residual=0.0`. This is expected behavior — not an error.

### Git Intelligence

Recent commits: `feat(story-4.3): Register Invariant API` → `feat(story-4.2): TrajectorBatch Export and Load`
Commit message for this story: `feat(story-4.4): ComplianceReport Summary and Violations`

### Files Being Modified — Current State

**`src/physlink/core/validation.py`** (UPDATE — currently 101 lines, ends after `register_invariant`):
- Current: `_InvariantRecord`, `_HasInvariants` Protocol, `_validate_fn_signature`, `register_invariant`
- Add: `ComplianceReport` class AFTER `register_invariant` (append to end of file)
- Do NOT modify `register_invariant` or `_InvariantRecord`

**`src/physlink/adapters/dreamer.py`** (UPDATE):
- Current: `DreamerV3Adapter` with `_invariants`, `_invariant_residuals`, `_apply_invariants()`; no `compliance_report()` method yet
- Add: `compliance_report()` method immediately after `_apply_invariants()`
- Add: `from physlink.core.validation import ComplianceReport` to imports
- Do NOT modify `_apply_invariants()`, `fit()`, or `_reset_training_state()`

**`src/physlink/__init__.py`** (UPDATE):
- Current: exports `register_invariant` (Story 4.3), comment placeholder for `ComplianceReport`
- Change: merge import of `ComplianceReport` with `register_invariant` import; add to `__all__`

**`tests/unit/core/test_validation.py`** (UPDATE):
- Current: `TestRegisterInvariantSuccess`, `TestRegisterInvariantInvalidFn`, `TestRegisterInvariantInvalidMode`
- Add: `TestComplianceReportSummaryPass`, `TestComplianceReportSummaryFail`, `TestComplianceReportViolations`, `TestComplianceReportEmpty`, `TestComplianceReportMultiInvariant`

**`tests/unit/adapters/test_dreamer_cpu.py`** (UPDATE):
- Current: `TestRegisterInvariantHardModeStory43`, `TestRegisterInvariantSoftModeStory43`, `TestRegisterInvariantIdempotenceStory43`
- Add: `TestComplianceReportStory44`

**`tests/integration/test_api_stability.py`** (UPDATE):
- Current: `test_epic1_api_symbols`, `test_epic2_api_symbols`, `test_epic3_api_symbols`, `test_story43_api_symbols`, `TestTopLevelNamespaceAccess`, `TestPackageMetadata`
- Add: `test_story44_api_symbols()`

### Project Structure Notes

- `ComplianceReport` placement: `src/physlink/core/validation.py` — consistent with architecture Category 3 (`from physlink.core.validation import register_invariant, ComplianceReport`) [Source: architecture.md#Category 3]
- `compliance_report()` method on `DreamerV3Adapter` in `src/physlink/adapters/dreamer.py` — not a standalone function, an adapter method [Source: epics.md#FR-07]
- Test mirror: `tests/unit/core/test_validation.py` (core tests) + `tests/unit/adapters/test_dreamer_cpu.py` (integration tests) [Source: architecture.md#Structure Patterns]

### References

- [Source: epics.md#Story 4.4] — Acceptance Criteria, user story statement
- [Source: epics.md#FR-07] — `ComplianceReport` full spec: `summary()`, `violations()`, `plot()`, `export()` (plot/export deferred to 4.5)
- [Source: epics.md#NFR-13] — Compliance check deterministic — same data, same result
- [Source: architecture.md#Category 3] — `ComplianceReport` in `physlink.core.validation`, exported from `physlink.__init__`
- [Source: architecture.md#Architectural Boundaries] — `adapters/ → core/` ✅ allowed; `core/ → adapters/` ❌ forbidden
- [Source: architecture.md#Docstring Patterns] — Google style, Args/Returns/Example mandatory for public API
- [Source: architecture.md#Error Message Patterns] — Got/Expected/Fix template (n/a for ComplianceReport data methods)
- [Source: architecture.md#Testing Patterns] — no conftest.py in subdirs, `@pytest.mark.gpu` for CUDA
- [Source: implementation-artifacts/4-3-register-invariant-api.md] — `_invariant_residuals` structure, boundary workaround with Protocol, ruff rules, deferred `Any` avoidance

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented `ComplianceReport` plain class in `src/physlink/core/validation.py` with `summary()` and `violations()` methods, fully typed with `list[dict[str, Any]]` for mypy strict compliance.
- Added `compliance_report()` method to `DreamerV3Adapter` immediately after `_apply_invariants()`, reading `_invariants` and `_invariant_residuals` for pure computation.
- Exported `ComplianceReport` from `physlink.__init__` with isort-sorted import (`ComplianceReport, register_invariant`).
- Added 24 unit tests in `TestComplianceReport*` classes (test_validation.py): 16 per-spec + 8 extra coverage classes (`TestComplianceReportDefensiveCopy`, `TestComplianceReportSortingOrder`, `TestComplianceReportPossibleCause`).
- Added 10 integration tests in `TestComplianceReportStory44` (test_dreamer_cpu.py): 8 per-spec + 2 extra (`test_compliance_report_possible_cause_contains_diagnostic_text`, `test_compliance_report_violations_sorted_by_invariant_then_idx`).
- Added `test_story44_api_symbols()` to test_api_stability.py.
- Total new tests: 35 (24 + 10 + 1). Full suite: 698 passed, 3 skipped, 18 deselected (`-m "not gpu"`), ruff zero warnings, mypy strict core passes, mkdocs builds successfully.
- Post-review fix: corrected `stats` and `violation_list` local type annotations in `compliance_report()` from `list[dict]` to `list[dict[str, Any]]` (mypy strict `[type-arg]`).

### File List

- `src/physlink/core/validation.py` — added `ComplianceReport` class with `summary()` and `violations()` methods
- `src/physlink/adapters/dreamer.py` — added `compliance_report()` method and `ComplianceReport` import
- `src/physlink/__init__.py` — exported `ComplianceReport`, added to `__all__`
- `tests/unit/core/test_validation.py` — added 16 tests in 5 `TestComplianceReport*` classes
- `tests/unit/adapters/test_dreamer_cpu.py` — added 8 tests in `TestComplianceReportStory44`
- `tests/integration/test_api_stability.py` — added `test_story44_api_symbols()`

## Change Log

- 2026-05-22: Story 4.4 implemented — added `ComplianceReport` pure data class with `summary()` and `violations()` methods; added `DreamerV3Adapter.compliance_report()` method; exported from `physlink.__init__`; 35 new tests added (24 unit + 10 adapter + 1 integration); 698 passed, 3 skipped, zero regressions.
- 2026-05-22: Post-review fix — corrected `stats`/`violation_list` type annotations in `compliance_report()` to `list[dict[str, Any]]`; documentation corrected for actual test counts.
