# Story 4.3: register_invariant() API

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a domain scientist (CFD, mechanics, climate),
I want to attach a physical invariant check to my adapter using a plain Python callable,
so that I can encode my domain knowledge without learning any PhysLink abstractions or subclassing anything.

## Acceptance Criteria

1. **Given** I define a plain Python function `def mass_conservation(trajectory: dict) -> float: ...`
   **When** I call `register_invariant(adapter, name="mass_conservation", fn=mass_conservation, tolerance=0.01, mode="hard")`
   **Then** the invariant is attached to the adapter without error
   **And** no subclassing, decorators, or inheritance is required

2. **Given** `mode="hard"` is set
   **When** `adapter.fit()` processes a trajectory where `fn(trajectory) > tolerance`
   **Then** that trajectory is rejected from the training batch
   **And** a diagnostic message is logged (not a raw stack trace)

3. **Given** `mode="soft"` is set
   **When** `adapter.fit()` processes a trajectory where `fn(trajectory) > tolerance`
   **Then** the trajectory is included but its residual penalizes the loss function

4. **Given** I pass a function with the wrong signature (e.g., `def check_pressure(pressure, volume) -> bool`)
   **When** `register_invariant()` is called
   **Then** a `ValidationError` is raised immediately (not deferred to fit())
   **And** the error message shows the function name and parameters in human-readable form: `Got: check_pressure(pressure, volume) -> bool`
   **And** the message shows: `Expected: fn(trajectory: dict) -> float`, Fix: a correction instruction (UX-DR-12)

5. **Given** I call `register_invariant(..., mode="medium")` (invalid mode value)
   **When** `register_invariant()` is called
   **Then** a `ConfigurationError` is raised immediately
   **And** the error message follows Got/Expected/Fix: Got `"medium"`, Expected one of `["hard", "soft"]`, Fix: use `mode="hard"` to reject violations or `mode="soft"` to penalize them

## Tasks / Subtasks

- [x] Task 1: Implement `register_invariant()` in `src/physlink/core/validation.py` (AC: #1, #4, #5)
  - [x] Add `_InvariantRecord` dataclass: `name: str`, `fn: Callable[[dict], float]`, `tolerance: float`, `mode: Literal["hard", "soft"]`
  - [x] Add `_validate_fn_signature(fn, name)` helper using `inspect.signature` — raises `ValidationError` if not exactly 1 positional parameter; error uses `inspect.signature(fn)` for Got, shows `fn(trajectory: dict) -> float` for Expected
  - [x] Implement `register_invariant(adapter, name, fn, tolerance, mode="soft")` — validate mode in `["hard", "soft"]` (raises `ConfigurationError` on invalid), validate fn signature, append `_InvariantRecord` to `adapter._invariants`
  - [x] Google-style docstring: Args (all 5 params), Raises (`ValidationError`, `ConfigurationError`), Example (mass_conservation pattern)
  - [x] `from __future__ import annotations` at top

- [x] Task 2: Update `DreamerV3Adapter.__init__()` in `src/physlink/adapters/dreamer.py` (AC: #1, #2, #3)
  - [x] Add `self._invariants: list = []` to `__init__` instance attributes
  - [x] Add `self._invariant_residuals: dict[str, list[float]] = {}` — keyed by invariant name, stores residual per trajectory; reset on each `fit()` call (for Story 4.4 ComplianceReport)

- [x] Task 3: Update `fit()` in `src/physlink/adapters/dreamer.py` to apply invariants (AC: #2, #3)
  - [x] After `TrajectoryBuffer`/`list` conversion to `TrajectoryBatch`, before building tensors: call `_apply_invariants(self, trajectories)` → returns filtered `TrajectoryBatch` + stores residuals
  - [x] Implement `_apply_invariants()` as a method on `DreamerV3Adapter`:
    - For each invariant in `self._invariants`, iterate `trajectories.data` with index
    - Call `invariant.fn(traj)` for each trajectory, catching exceptions (log warning, treat as residual=0.0)
    - Accumulate residuals in `self._invariant_residuals[name]`
    - `mode="hard"`: exclude trajectories where any hard-mode invariant residual > tolerance; print `[physlink] Invariant '{name}' rejected trajectory {idx}: residual={r:.4f} > tolerance={tol}`
    - `mode="soft"`: compute `self._soft_penalty: float = sum of (residual - tolerance) for violations` across soft invariants; add `soft_penalty_weight * soft_penalty` to loss in `_training_step` (or post-step via a stored scalar)
  - [x] Reset `self._invariant_residuals = {}` and `self._soft_penalty = 0.0` at start of `fit()` (idempotence — NFR-09)
  - [x] Hard mode: if ALL trajectories are rejected, raise `ValidationError` with Got/Expected/Fix (prevents empty tensor crash)
  - [x] Soft penalty implementation: store mean soft residual surplus as `self._soft_penalty_per_step: float` before the training loop; in `_training_step`, add `self._soft_penalty_per_step` to `total_loss` (scalar addition is sufficient — avoids tensor graph complexity)

- [x] Task 4: Export `register_invariant` from `src/physlink/__init__.py` (AC: #1, architecture AR-10)
  - [x] Add `from physlink.core.validation import register_invariant` import
  - [x] Add `"register_invariant"` to `__all__` (note: `ComplianceReport` deferred to Story 4.4)
  - [x] `test_api_stability.py` currently verifies 4 symbols — Story 4.5 finalizes all 7; adding `register_invariant` now is correct (5 symbols total after this story)

- [x] Task 5: Create `tests/unit/core/test_validation.py` (AC: #1, #4, #5)
  - [x] `TestRegisterInvariantSuccess` — valid fn 1 param, attaches to adapter, no error, `adapter._invariants` has 1 entry
  - [x] `TestRegisterInvariantMultiple` — 2 invariants attached, both in `adapter._invariants`
  - [x] `TestRegisterInvariantInvalidFnTwoParams` — fn with 2 params → `ValidationError`; error contains fn name and signature
  - [x] `TestRegisterInvariantInvalidFnZeroParams` — fn with 0 params → `ValidationError`
  - [x] `TestRegisterInvariantInvalidMode` — mode="medium" → `ConfigurationError`; Got/Expected/Fix in message
  - [x] `TestRegisterInvariantInvalidModeCase` — mode="HARD" → `ConfigurationError` (case-sensitive)
  - [x] `TestRegisterInvariantInvalidModeEmpty` — mode="" → `ConfigurationError`
  - [x] `TestRegisterInvariantErrorNotDeferredToFit` — validation fires immediately at register time, not at fit() time
  - [x] `TestRegisterInvariantNegativeTolerance` — negative tolerance → `ConfigurationError` (defensively: tolerance must be >= 0)

- [x] Task 6: Add integration tests in `tests/unit/adapters/test_dreamer_cpu.py` (AC: #2, #3)
  - [x] `TestRegisterInvariantHardModeStory43` class:
    - `test_hard_mode_rejects_violating_trajectory` — all-violating hard invariant → model trains on 0 trajectories should raise `ValidationError`
    - `test_hard_mode_keeps_passing_trajectory` — fn always returns 0.0, fit() completes normally
    - `test_hard_mode_partial_rejection` — fn returns high residual for subset, fit() still runs on remaining
    - `test_hard_mode_logs_diagnostic` — check print output contains invariant name and "rejected" (use capsys)
    - `test_hard_mode_residuals_stored` — `adapter._invariant_residuals["name"]` has correct length after fit()
  - [x] `TestRegisterInvariantSoftModeStory43` class:
    - `test_soft_mode_does_not_filter` — fn returns > tolerance for all trajectories, fit() still trains on all
    - `test_soft_mode_residuals_stored` — residuals are stored per trajectory
    - `test_soft_mode_zero_residual_no_penalty` — fn always returns 0.0, `_soft_penalty_per_step` == 0.0
  - [x] `TestRegisterInvariantIdempotenceStory43`:
    - `test_fit_twice_resets_residuals` — call fit() twice; second call residuals don't accumulate from first (NFR-09)

- [x] Task 7: Update `tests/integration/test_api_stability.py` to include `register_invariant`
  - [x] Add `"register_invariant"` to the expected symbols list (or verify it's present in `physlink.__all__`)

- [x] Task 8: Run full test suite — zero regressions (AC: all)
  - [x] `pytest tests/ -x -m "not gpu"` — 0 failures
  - [x] `ruff check src/` — zero warnings
  - [x] `mkdocs build --strict` — docs built successfully
  - [x] File List complete AND Change Log entry added before marking done

## Dev Notes

### What Story 4.3 Does and Does NOT Do

**This story implements:**
- `register_invariant()` function in `core/validation.py` — validates fn signature and mode, attaches `_InvariantRecord` to adapter
- `DreamerV3Adapter` gains `_invariants` list and `_invariant_residuals` dict (reset at each `fit()`)
- `fit()` applies hard-mode filtering and soft-mode loss penalty before/during training
- Violation data stored on adapter (`_invariant_residuals`) for Story 4.4 `ComplianceReport`
- `register_invariant` exported from `physlink.__init__`

**Explicitly deferred — do NOT implement:**
- `ComplianceReport` data object — Story 4.4
- `adapter.compliance_report()` method — Story 4.4
- `report.summary()`, `report.violations()` — Story 4.4
- `report.plot()`, `report.export()` — Story 4.5
- `ComplianceReport` export in `physlink.__init__` — Story 4.4
- `test_api_stability.py` 7-symbol verification — Story 4.5

### `_InvariantRecord` and Storage Design

```python
# src/physlink/core/validation.py
from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from physlink.adapters.dreamer import DreamerV3Adapter

from physlink.core.exceptions import ConfigurationError, ValidationError


@dataclass
class _InvariantRecord:
    name: str
    fn: Callable[[dict], float]
    tolerance: float
    mode: Literal["hard", "soft"]


def _validate_fn_signature(fn: Callable, name: str) -> None:
    sig = inspect.signature(fn)
    params = [
        p for p in sig.parameters.values()
        if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
    ]
    if len(params) != 1:
        raise ValidationError(
            f"register_invariant: invalid fn signature for '{name}'.\n"
            f"  Got:      {fn.__name__}{sig}\n"
            f"  Expected: fn(trajectory: dict) -> float\n"
            f"  Fix:      define your function with a single dict argument, "
            f"e.g. def {name}(trajectory: dict) -> float: ..."
        )


def register_invariant(
    adapter: DreamerV3Adapter,
    name: str,
    fn: Callable[[dict], float],
    tolerance: float,
    mode: Literal["hard", "soft"] = "soft",
) -> None:
    ...
```

**Boundary compliance:**
- `core/validation.py` → `core/exceptions.py` ✅ (intra-core import)
- `core/validation.py` → `adapters/dreamer.py` — **only under `TYPE_CHECKING`** to avoid the boundary violation (`physlink.core/ → physlink.adapters/` is FORBIDDEN per `test_core_boundary.py`). Use `TYPE_CHECKING` import for the `DreamerV3Adapter` type hint; `register_invariant` receives `adapter` and does `adapter._invariants.append(...)` at runtime without importing the class. This is the correct pattern.

**Runtime type check in `register_invariant`:** Don't do `isinstance(adapter, DreamerV3Adapter)` — it would require a runtime import which violates the boundary. Accept any adapter duck-type that has `_invariants`.

### `DreamerV3Adapter` Changes

Add to `__init__` (after `self._last_checkpoint_path`):
```python
self._invariants: list = []            # stores _InvariantRecord objects
self._invariant_residuals: dict[str, list[float]] = {}  # keyed by name
self._soft_penalty_per_step: float = 0.0  # pre-computed for soft mode
```

In `_reset_training_state()` — extend to also reset invariant state:
```python
def _reset_training_state(self) -> None:
    self._loss_history = []
    self._baseline_loss = None
    self._invariant_residuals = {}     # reset for idempotence (NFR-09)
    self._soft_penalty_per_step = 0.0
```

### `_apply_invariants()` Method Design

```python
def _apply_invariants(
    self,
    trajectories: TrajectoryBatch,
) -> TrajectoryBatch:
    """Apply registered invariants: filter hard-mode violations, compute soft penalty."""
    if not self._invariants:
        return trajectories

    data = trajectories.data
    # Initialize residual storage
    for inv in self._invariants:
        self._invariant_residuals[inv.name] = []

    hard_mask: list[bool] = [True] * len(data)

    for inv in self._invariants:
        for idx, traj in enumerate(data):
            try:
                residual = float(inv.fn(traj))
            except Exception as exc:
                print(
                    f"[physlink] Invariant '{inv.name}' failed on trajectory {idx}: "
                    f"{type(exc).__name__} — treating residual as 0.0"
                )
                residual = 0.0
            self._invariant_residuals[inv.name].append(residual)

            if inv.mode == "hard" and residual > inv.tolerance:
                hard_mask[idx] = False
                print(
                    f"[physlink] Invariant '{inv.name}' rejected trajectory {idx}: "
                    f"residual={residual:.4f} > tolerance={inv.tolerance}"
                )

    # Apply hard filtering
    filtered = [d for d, keep in zip(data, hard_mask) if keep]
    if not filtered:
        from physlink.core.exceptions import ValidationError
        raise ValidationError(
            f"register_invariant (hard mode): all {len(data)} trajectories rejected.\n"
            f"  Got:      0 trajectories remaining after hard-mode invariant filtering\n"
            f"  Expected: at least 1 trajectory passing all hard-mode invariants\n"
            f"  Fix:      lower tolerance, fix the invariant function, "
            f"or switch to mode='soft'."
        )

    # Compute soft penalty: mean surplus residual across ALL trajectories for soft invariants
    soft_surplus = 0.0
    soft_count = 0
    for inv in self._invariants:
        if inv.mode == "soft":
            for r in self._invariant_residuals[inv.name]:
                if r > inv.tolerance:
                    soft_surplus += r - inv.tolerance
                    soft_count += 1
    self._soft_penalty_per_step = soft_surplus / max(len(data), 1)

    return TrajectoryBatch(data=filtered)
```

### `fit()` Integration Point

Call `_apply_invariants` AFTER trajectory conversion to `TrajectoryBatch` but BEFORE tensor pre-processing:
```python
# In fit(), after:
if isinstance(trajectories, TrajectoryBuffer):
    trajectories = trajectories.to_batch()
if isinstance(trajectories, list):
    trajectories = TrajectoryBatch.from_list(trajectories)

# ADD:
trajectories = self._apply_invariants(trajectories)

# Then continue with:
raw_data = trajectories.data
obs_all = torch.tensor(...)
```

### `_training_step()` Soft Penalty

In `_training_step()`, the `total_loss` line becomes:
```python
total_loss = wm_loss + actor_loss + critic_loss + self._soft_penalty_per_step
```

`self._soft_penalty_per_step` is a Python float (not a tensor), which is valid: PyTorch adds it as a scalar offset to the tensor. This is the simplest correct approach — no tensor graph complexity.

### Error Message Patterns (Architecture Compliance)

**fn signature error (AC#4):**
```python
raise ValidationError(
    f"register_invariant: invalid fn signature for '{name}'.\n"
    f"  Got:      {fn.__name__}{sig}\n"
    f"  Expected: fn(trajectory: dict) -> float\n"
    f"  Fix:      define your function with a single dict argument, "
    f"e.g. def {name}(trajectory: dict) -> float: ..."
)
```

**invalid mode error (AC#5):**
```python
raise ConfigurationError(
    f"register_invariant: invalid mode for '{name}'.\n"
    f"  Got:      mode={mode!r}\n"
    f"  Expected: one of {['hard', 'soft']}\n"
    f"  Fix:      use mode='hard' to reject violations or mode='soft' to penalize them."
)
```

### Architecture Compliance Checklist

- `from __future__ import annotations` in `core/validation.py` ✅ (required for forward refs in core/)
- `DreamerV3Adapter` in `validation.py` under `TYPE_CHECKING` only — no runtime import of adapters from core/ ✅ (preserves `test_core_boundary.py` invariant)
- `_InvariantRecord` is a private type (leading underscore) — not exported from `physlink.__init__` ✅
- `register_invariant` → `physlink.__init__` export ✅ (AR-10: `register_invariant` is one of the 7 public symbols)
- `inspect` stdlib module — deferred import inside `_validate_fn_signature()` to keep module-level imports lean ✅
- Google-style docstring on `register_invariant()`: Args (5), Raises (2), Example ✅
- `X | Y` syntax for type annotations ✅ (no `Union`, `Optional`, `List`)
- `Literal["hard", "soft"]` for mode param type ✅
- `ANN401` avoidance — no `Any` in public signatures ✅ (`fn: Callable[[dict], float]` is specific)
- All error messages follow Got/Expected/Fix template ✅

### Test File: `tests/unit/core/test_validation.py` Structure

```python
"""Tests for physlink.core.validation — register_invariant."""
from __future__ import annotations

import pytest
from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
from physlink.core.validation import register_invariant
from physlink.core.exceptions import ConfigurationError, ValidationError


def _make_adapter():
    obs = ObservationSpace.from_proprioception(joints=7, include_velocity=False)
    act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
    return DreamerV3Adapter(obs, act)


def _fn_valid(trajectory: dict) -> float:
    return 0.0


class TestRegisterInvariantSuccess:
    def test_attach_valid_fn(self):
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        assert len(adapter._invariants) == 1

    def test_attach_sets_name(self):
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        assert adapter._invariants[0].name == "mass"

    def test_attach_sets_mode_default_soft(self):
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        assert adapter._invariants[0].mode == "soft"

    def test_attach_hard_mode(self):
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="hard")
        assert adapter._invariants[0].mode == "hard"

    def test_attach_multiple_invariants(self):
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        register_invariant(adapter, "energy", _fn_valid, tolerance=0.05, mode="hard")
        assert len(adapter._invariants) == 2

    def test_no_subclassing_required(self):
        # plain fn, no decoration
        adapter = _make_adapter()
        def raw_fn(t: dict) -> float:
            return abs(t.get("x", 0.0))
        register_invariant(adapter, "pos", raw_fn, tolerance=1.0)
        assert len(adapter._invariants) == 1


class TestRegisterInvariantInvalidFn:
    def test_two_params_raises(self):
        adapter = _make_adapter()
        def bad(pressure, volume): return 0.0
        with pytest.raises(ValidationError) as exc_info:
            register_invariant(adapter, "bad", bad, tolerance=0.01)
        assert "bad" in str(exc_info.value)
        assert "fn(trajectory: dict) -> float" in str(exc_info.value)

    def test_zero_params_raises(self):
        adapter = _make_adapter()
        def no_params(): return 0.0
        with pytest.raises(ValidationError):
            register_invariant(adapter, "no_params", no_params, tolerance=0.01)

    def test_error_message_contains_fn_name(self):
        adapter = _make_adapter()
        def check_pressure(p, v): return 0.0
        with pytest.raises(ValidationError) as exc_info:
            register_invariant(adapter, "check_pressure", check_pressure, tolerance=0.01)
        assert "check_pressure" in str(exc_info.value)
        assert "Got:" in str(exc_info.value)
        assert "Fix:" in str(exc_info.value)

    def test_error_raised_immediately_not_at_fit(self):
        adapter = _make_adapter()
        def bad(a, b): return 0.0
        with pytest.raises(ValidationError):
            register_invariant(adapter, "bad", bad, tolerance=0.01)
        # Adapter has no invariants attached
        assert len(adapter._invariants) == 0


class TestRegisterInvariantInvalidMode:
    def test_medium_raises(self):
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError) as exc_info:
            register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="medium")
        assert "medium" in str(exc_info.value)
        assert "hard" in str(exc_info.value)
        assert "soft" in str(exc_info.value)

    def test_uppercase_hard_raises(self):
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError):
            register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="HARD")

    def test_empty_mode_raises(self):
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError):
            register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="")

    def test_got_expected_fix_in_message(self):
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError) as exc_info:
            register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="medium")
        msg = str(exc_info.value)
        assert "Got:" in msg
        assert "Expected:" in msg
        assert "Fix:" in msg
```

### Previous Story Intelligence (Story 4.2)

From Story 4.2 completion notes:
- `from __future__ import annotations` is ALREADY present in `_types.py` — follow same for `validation.py`
- File List + Change Log MUST be complete before marking done
- `ruff check src/` must show zero warnings before marking done
- `ANN401` IS enabled — avoid `Any` in public signatures; `Callable[[dict], float]` is preferred
- `inspect` module should be imported inside the helper function (deferred import pattern) to reduce module-level imports
- `# noqa: ` comments pattern established — use when needed for ruff exceptions

From Story 4.1 completion notes:
- `from __future__ import annotations` pattern for core modules
- deferred imports inside method bodies for optional dependencies

### Git Intelligence

Recent commits follow this pattern:
- `feat(story-4.2): TrajectorBatch Export and Load`
- `feat(story-4.1): AdaptationConfig and AdaptationRun`

Commit message for this story should be: `feat(story-4.3): register_invariant() API`

### Files Being Modified — Current State

**`src/physlink/core/validation.py`** (UPDATE — currently a 6-line stub):
- Current state: `"""Invariant registration..."""` docstring + `from __future__ import annotations` only
- Add: `_InvariantRecord`, `_validate_fn_signature`, `register_invariant`

**`src/physlink/adapters/dreamer.py`** (UPDATE):
- Current state: `DreamerV3Adapter.__init__` has `_model`, `_actor`, `_critic`, `_loss_history`, `_baseline_loss`, `_fit_elapsed_seconds`, `_triptych_path`, `_last_checkpoint_path`
- Add: `_invariants`, `_invariant_residuals`, `_soft_penalty_per_step` in `__init__`
- `_reset_training_state()`: extend to reset `_invariant_residuals`, `_soft_penalty_per_step`
- Add `_apply_invariants()` method
- `fit()`: call `self._apply_invariants(trajectories)` after trajectory conversion
- `_training_step()`: add `self._soft_penalty_per_step` to `total_loss`

**`src/physlink/__init__.py`** (UPDATE):
- Current state: exports `DreamerV3Adapter`, `PhysLinkError`, `ActionSpace`, `ObservationSpace`, `doctor`; comment placeholder for `register_invariant`
- Add: `from physlink.core.validation import register_invariant`; add `"register_invariant"` to `__all__`

**`tests/unit/core/test_validation.py`** (NEW):
- Create with `TestRegisterInvariantSuccess`, `TestRegisterInvariantInvalidFn`, `TestRegisterInvariantInvalidMode`

**`tests/unit/adapters/test_dreamer_cpu.py`** (UPDATE):
- Add `TestRegisterInvariantHardModeStory43`, `TestRegisterInvariantSoftModeStory43`, `TestRegisterInvariantIdempotenceStory43`

### References

- [Source: epics.md#Story 4.3] — Acceptance Criteria, user story statement
- [Source: epics.md#FR-06] — `register_invariant()` full spec
- [Source: epics.md#UX-DR-12] — Error messages for wrong fn signature
- [Source: architecture.md#Category 3] — `register_invariant` in `physlink.core.validation`, top-level export
- [Source: architecture.md#Docstring Patterns] — `register_invariant` docstring example
- [Source: architecture.md#Error Message Patterns] — Got/Expected/Fix template
- [Source: architecture.md#Architectural Boundaries] — `core/ → adapters/` FORBIDDEN; use TYPE_CHECKING
- [Source: implementation-artifacts/4-2-trajectorybuffer-export-and-load.md] — deferred imports, ruff rules, File List requirement

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Boundary test (`test_core_boundary.py`) uses AST walking and catches even `TYPE_CHECKING` imports. Switched from `DreamerV3Adapter` type annotation to a `_HasInvariants` Protocol (defined in `core/validation.py`) + `BaseAdapter` removed in favor of the Protocol. No cross-layer import needed.
- `_reset_training_state()` was called AFTER `_apply_invariants()` in the original code structure, causing residuals to be wiped. Moved `_reset_training_state()` to before trajectory conversion so residuals are correctly preserved post-`_apply_invariants()`.

### Completion Notes List

- Implemented `_InvariantRecord` dataclass, `_validate_fn_signature()` helper, and `register_invariant()` function in `core/validation.py`
- Used `_HasInvariants` Protocol (not `DreamerV3Adapter` import) to satisfy the core→adapters boundary test (AST-based)
- Added `_invariants`, `_invariant_residuals`, `_soft_penalty_per_step` to `DreamerV3Adapter.__init__()`
- Extended `_reset_training_state()` to reset invariant state; moved call to start of `fit()` for correct idempotence
- Added `_apply_invariants()` method: hard-mode filtering with diagnostic prints, soft-mode penalty accumulation
- Added `self._soft_penalty_per_step` to `total_loss` in `_training_step()`
- Exported `register_invariant` from `physlink.__init__`; `__all__` remains isort-sorted
- Created 25 unit tests in `tests/unit/core/test_validation.py`
- Added 12 integration tests in `tests/unit/adapters/test_dreamer_cpu.py` (Story 4.3 classes)
- Added `test_story43_api_symbols()` to `tests/integration/test_api_stability.py`
- All 663 tests pass; ruff clean; mkdocs builds

### File List

- `src/physlink/core/validation.py` — implemented from stub
- `src/physlink/adapters/dreamer.py` — added `_invariants`, `_invariant_residuals`, `_soft_penalty_per_step`; added `_apply_invariants()`; updated `_reset_training_state()`, `fit()`, `_training_step()`
- `src/physlink/__init__.py` — added `register_invariant` export
- `tests/unit/core/test_validation.py` — new file, 26 tests
- `tests/unit/adapters/test_dreamer_cpu.py` — added 3 test classes (10 tests)
- `tests/integration/test_api_stability.py` — added `test_story43_api_symbols()`

## Change Log

- 2026-05-22: Story 4.3 — Implement `register_invariant()` API with hard/soft mode invariant filtering during `fit()`, full validation (signature, mode, tolerance), exports, and tests (663 tests passing)
- 2026-05-22: Story 4.3 Review — Fixed docstring (`tolerance < 0` → `ConfigurationError` not `ValidationError`); replaced deprecated `torch.cuda.amp.autocast/GradScaler` with `torch.amp.*` APIs; corrected test count annotations (25 unit / 12 integration)
