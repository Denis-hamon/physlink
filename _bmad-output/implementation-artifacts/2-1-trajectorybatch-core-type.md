# Story 2.1: TrajectoryBatch Core Type

Status: done

## Story

As a developer,
I want a `TrajectoryBatch` type in `core/_types.py` that `fit()` accepts transparently,
so that downstream stories can use a stable, typed trajectory contract without introducing torch dependencies into `core/`.

## Acceptance Criteria

1. **Given** `from physlink.core._types import TrajectoryBatch` is executed
   **When** I inspect the class
   **Then** `TrajectoryBatch` has a `from_list(data: list[dict])` classmethod that converts silently
   **And** no torch primitives appear in the public type signature of `TrajectoryBatch`
   **And** `test_core_no_torch_import.py` passes on `core/_types.py` (AST check — no torch import)

2. **Given** `fit()` is called with a `list[dict]`
   **When** silent conversion occurs inside `fit()`
   **Then** the conversion to `TrajectoryBatch` is transparent to the caller — no user-facing type error
   **And** `fit()` also accepts a `TrajectoryBatch` directly without conversion

3. **Given** `TrajectoryBatch.from_list([])` is called with an empty list
   **When** the object is constructed
   **Then** it succeeds without error (empty batch is valid)

## Tasks / Subtasks

- [x] Task 1: Implement `TrajectoryBatch` in `src/physlink/core/_types.py` (AC: #1, #2, #3)
  - [x] Keep the existing `from __future__ import annotations` at line 1 — do NOT add it again
  - [x] Add `import numpy as np` only if needed for type hints; otherwise numpy is not required here
  - [x] Define `TrajectoryBatch` dataclass (use `@dataclass(frozen=False)` or plain class — no torch)
  - [x] Attribute: `data: list[dict]` — the raw trajectory list
  - [x] Classmethod: `from_list(data: list[dict]) -> TrajectoryBatch` — silent conversion, no validation
  - [x] Add `__len__(self) -> int` returning `len(self.data)`
  - [x] Add `__iter__(self)` yielding from `self.data` for iteration compatibility
  - [x] Add `__repr__(self) -> str` for debug convenience: `f"TrajectoryBatch(n={len(self.data)})"`
  - [x] Public type signature: parameter types use `list[dict]`, return type `TrajectoryBatch` — no torch.Tensor
  - [x] Google-style docstring on the class and `from_list()` with Args + Example sections
  - [x] **Do NOT implement** `from_numpy()` — deferred to v0.2 (architecture decision)
  - [x] **Do NOT implement** `AdaptationConfig` or `AdaptationRun` — deferred to Story 4.1
  - [x] Leave the existing file comment referencing Story 4.1 in place

- [x] Task 2: Add `synthetic_trajectories` fixture to `tests/conftest.py` (AC: #2)
  - [x] Read existing `tests/conftest.py` first (currently has only a docstring)
  - [x] Add `import numpy as np` at top
  - [x] Add `import pytest`
  - [x] Add fixture: `@pytest.fixture` on `synthetic_trajectories() -> list[dict]`
  - [x] Body: `rng = np.random.default_rng(42)` then return `[{"obs": rng.random(7), "action": rng.random(3)} for _ in range(1000)]`
  - [x] Docstring: `"""1000 numpy-only trajectories — no GPU required."""`
  - [x] This fixture provides consistent trajectory data for Story 3.2 (fit()) and Story 4.x tests

- [x] Task 3: Create `tests/unit/core/test_types.py` (AC: #1, #2, #3)
  - [x] This file does NOT exist yet — create it
  - [x] Header imports: `from __future__ import annotations`, `import pytest`, `from physlink.core._types import TrajectoryBatch`
  - [x] Class `TestTrajectoryBatchFromList`:
    - [x] `test_from_list_returns_trajectory_batch`: assert `isinstance(TrajectoryBatch.from_list([{"obs": [1, 2, 3]}]), TrajectoryBatch)`
    - [x] `test_from_list_preserves_data`: assert `len(tb.data) == 3` after constructing from a 3-item list
    - [x] `test_from_list_empty_list_is_valid`: `TrajectoryBatch.from_list([])` must not raise
    - [x] `test_from_list_preserves_dict_keys`: round-trip — `tb.data[0]["obs"]` equals original value
  - [x] Class `TestTrajectoryBatchInterface`:
    - [x] `test_len_returns_count`: `len(TrajectoryBatch.from_list([{}, {}]))` == 2
    - [x] `test_iter_yields_dicts`: `list(tb)` == original `list[dict]`
    - [x] `test_repr_contains_n`: `"n=3"` in `repr(TrajectoryBatch.from_list([{}, {}, {}]))`
  - [x] Class `TestTrajectoryBatchNoTorch`:
    - [x] `test_no_torch_in_public_annotation`: import `inspect`, `TrajectoryBatch.from_list`; assert `"torch"` not in `str(inspect.signature(TrajectoryBatch.from_list))`
  - [x] Class `TestSyntheticTrajectoriesFixture` (uses the conftest fixture):
    - [x] `test_from_list_with_numpy_trajectories(synthetic_trajectories)`: construct `TrajectoryBatch.from_list(synthetic_trajectories)` and assert `len(tb) == 1000`
    - [x] `test_data_is_list_of_dicts(synthetic_trajectories)`: assert all `isinstance(t, dict)` for `t` in `tb.data`

## Dev Notes

### Critical Constraints

- **`from __future__ import annotations` already present** in `src/physlink/core/_types.py`. Do NOT add it again.
- **No torch anywhere in `core/_types.py`** — `test_core_no_torch_import.py` AST-walks this file on every CI run. Any `import torch` or `from torch import ...` will break CI.
- **No `core/` → `adapters/` imports** — `test_core_boundary.py` enforces this. `_types.py` must never import from `physlink.adapters`.
- **`from_numpy()` is explicitly deferred to v0.2** (Architecture — Category 1 Trajectory Data Contract). Do not add it. A `# v0.2: add from_numpy()` comment is acceptable; a stub that raises `NotImplementedError` is not (it pollutes the public API surface).
- **`AdaptationConfig` and `AdaptationRun` are Story 4.1** — the file comment in `_types.py` references this. Preserve it; do not implement these classes in this story.

### File to Modify

`src/physlink/core/_types.py` — currently contains only:
```python
"""Canonical trajectory data types for PhysLink core.

Implementation in Story 2.1 (TrajectoryBatch) and Story 4.1 (AdaptationConfig, AdaptationRun).
"""

from __future__ import annotations
```

This is the complete current state. Add `TrajectoryBatch` after the existing imports.

### Files to Create

- `tests/unit/core/test_types.py` — does not exist yet. Check `tests/unit/core/` — currently contains only `test_exceptions.py`.
- Do NOT create a `tests/unit/core/conftest.py` — the architecture mandates a single `tests/conftest.py`.

### File to Update

`tests/conftest.py` — currently contains only a docstring. Append the `synthetic_trajectories` fixture.

### Recommended Implementation

```python
# src/physlink/core/_types.py  (after existing header)

from dataclasses import dataclass, field


@dataclass
class TrajectoryBatch:
    """Canonical container for a batch of trajectory dicts.

    Backend-agnostic — no torch primitives in any public signature.
    Used as the stable input type for fit() across all adapters.

    Args:
        data: List of trajectory dicts, each with at minimum "obs" and "action" keys.

    Example:
        >>> tb = TrajectoryBatch.from_list([{"obs": [1, 2], "action": [0]}])
        >>> len(tb)
        1
    """

    data: list[dict] = field(default_factory=list)

    @classmethod
    def from_list(cls, data: list[dict]) -> TrajectoryBatch:
        """Convert a list of trajectory dicts to a TrajectoryBatch silently.

        Args:
            data: List of trajectory dicts. Empty list is valid.

        Returns:
            A TrajectoryBatch wrapping the provided data.

        Example:
            >>> tb = TrajectoryBatch.from_list([{"obs": [1, 2], "action": [0]}])
            >>> isinstance(tb, TrajectoryBatch)
            True
        """
        return cls(data=data)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __repr__(self) -> str:
        return f"TrajectoryBatch(n={len(self.data)})"
```

### `fit()` Integration Pattern (Story 3.2 reference)

Story 2.1 defines the type contract. Story 3.2 implements `fit()`. The silent conversion pattern to use in `DreamerV3Adapter.fit()` will be:

```python
# adapters/dreamer.py — Story 3.2 implementation (NOT in this story)
from physlink.core._types import TrajectoryBatch

def fit(
    self,
    trajectories: list[dict] | TrajectoryBatch,
    steps: int,
    checkpoint_interval_steps: int = 1000,
) -> AdaptationRun:
    if isinstance(trajectories, list):
        trajectories = TrajectoryBatch.from_list(trajectories)
    # ... rest of fit()
```

This pattern is provided as guidance for Story 3.2. Do NOT implement `fit()` in this story.

### Testing Architecture Reminders

- `tests/conftest.py` is the **only** conftest allowed — never create module-level conftests.
- `synthetic_trajectories` fixture uses `np.random.default_rng(42)` for deterministic data (NFR-13).
- `@pytest.mark.gpu` is NOT needed here — all `test_types.py` tests are CPU-only by design.
- `tests/unit/` mirrors `src/physlink/` exactly: `tests/unit/core/test_types.py` ↔ `src/physlink/core/_types.py`.

### Conventions Checklist

- `X | Y` union syntax (Python 3.10+) — not `Union[X, Y]`
- `from __future__ import annotations` — already present, do not duplicate
- Class name: `TrajectoryBatch` (PascalCase) ✓
- Method names: `from_list`, `__len__`, `__iter__`, `__repr__` (snake_case) ✓
- No abbreviations: `data`, not `d` or `traj_list`
- Google-style docstrings with Args + Example on public methods

### Project Structure Notes

- Alignment: `src/physlink/core/_types.py` is the architecturally designated location [Source: architecture.md#Category 1 — Trajectory Data Contract]
- `TrajectoryBatch` is NOT exported from `physlink.__init__` yet — that export finalization happens in Story 2.6 (or as a sub-task of it, to be confirmed)
- The architecture lists `TrajectoryBatch` in `__init__` exports only implicitly; its primary consumer is `DreamerV3Adapter.fit()`, accessed via `physlink.core._types`
- No conflicts with existing files — `_types.py` is currently a stub

### References

- [Source: architecture.md#Category 1 — Trajectory Data Contract] — canonical definition of `TrajectoryBatch`, `from_list()`, silent conversion
- [Source: architecture.md#Implementation Patterns & Consistency Rules] — naming, annotations, docstring, and testing conventions
- [Source: architecture.md#Project Structure & Boundaries] — `src/physlink/core/_types.py` location
- [Source: architecture.md#Architectural Boundaries] — no `core/` → `adapters/` import rule
- [Source: epics.md#Story 2.1] — Acceptance Criteria source
- [Source: tests/integration/test_core_no_torch_import.py] — AST guard that will cover `_types.py`
- [Source: tests/integration/test_core_boundary.py] — boundary guard that will cover `_types.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Correction ruff ANN204 + mypy strict : `__iter__` annoté `-> Iterator[dict[str, Any]]` ; `list[dict]` remplacé par `list[dict[str, Any]]` partout dans `_types.py`.

### Completion Notes List

- `TrajectoryBatch` dataclass implémentée dans `src/physlink/core/_types.py` : `from_list()`, `__len__`, `__iter__`, `__repr__`, Google-style docstrings.
- Aucune dépendance torch — validé par `test_core_no_torch_import.py` (AST guard) et `test_core_boundary.py`.
- Fixture `synthetic_trajectories` ajoutée à `tests/conftest.py` (1000 trajectoires numpy déterministes, seed 42).
- 21 nouveaux tests dans `tests/unit/core/test_types.py` — tous passent (5 classes de test, couvrant from_list, interface, no-torch, direct construction, edge cases, fixture shapes).
- Suite complète : 192 passed, 2 skipped, 0 failed.

### File List

- src/physlink/core/_types.py
- src/physlink/__init__.py
- tests/conftest.py
- tests/unit/core/test_types.py

## Change Log

- 2026-05-22 : Story 2.1 — Implémentation `TrajectoryBatch` core type, fixture `synthetic_trajectories`, 21 tests unitaires.
- 2026-05-22 : Review Story 2.1 — Auto-fix : annotations `-> None` + ANN001 + F401 + RUF015 sur `test_types.py` (28 violations ruff résolues) ; correction comptage tests (10→21) ; File List complété.
