# Story 2.4: Space .explain() Introspection

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher debugging normalization or clipping behavior,
I want to call `.explain()` on any Space object and receive a structured metadata dict,
so that I can verify my configuration without reading source code or guessing at defaults.

## Acceptance Criteria

1. **Given** an `ObservationSpace` constructed with `from_proprioception(joints=7, include_velocity=True)`
   **When** I call `obs_space.explain()`
   **Then** the return value is a `dict` (not a string, not None)
   **And** the dict contains keys describing: dimension count, velocity inclusion, normalization details, clipping bounds (or None if not set)

2. **Given** an `ActionSpace` constructed with `continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)`
   **When** I call `act_space.explain()`
   **Then** the return value is a `dict` with keys describing: dims, bounds per dimension, clipping behavior
   **And** the dict is JSON-serializable (no torch tensors or non-serializable objects)

## Tasks / Subtasks

- [x] Task 1: Add `.explain()` to `ObservationSpace` in `src/physlink/core/spaces.py` (AC: #1)
  - [x] Add `from typing import Any` to the import block (currently only `from physlink.core.exceptions import ValidationError` is imported — `Any` is needed for the `dict[str, Any]` return type)
  - [x] Add `.explain(self) -> dict[str, Any]` method to `ObservationSpace` AFTER `__repr__`
  - [x] Return a dict with these exact keys:
    - `"type": "ObservationSpace"` (str)
    - `"dims": self.dims` (int)
    - `"joints": self._joints` (int — raw joint count before velocity doubling)
    - `"include_velocity": self.include_velocity` (bool)
    - `"clip_bounds": list(self.clip_bounds) if self.clip_bounds is not None else None` — convert tuple to list for JSON serializability
    - `"normalize": self.normalize` (bool)
  - [x] Add Google-style docstring with Returns and Example sections
  - [x] Do NOT add `ExplainableMixin` or `core/_mixins.py` — architecture notes it as post-v0.1; implement directly on the class

- [x] Task 2: Add `.explain()` to `ActionSpace` in `src/physlink/core/spaces.py` (AC: #2)
  - [x] Add `.explain(self) -> dict[str, Any]` method to `ActionSpace` AFTER `__repr__`
  - [x] Return a dict with these exact keys:
    - `"type": "ActionSpace"` (str)
    - `"dims": self.dims` (int)
    - `"bounds": [list(b) for b in self.bounds]` — convert list[tuple] to list[list] for JSON serializability
    - `"clipping_behavior": "per_dimension"` (str — documents that clipping is applied independently per axis)
  - [x] Add Google-style docstring with Returns and Example sections
  - [x] **Do NOT touch `physlink/__init__.py`** — `ActionSpace` export is Story 2.6

- [x] Task 3: Add `.explain()` tests to `tests/unit/core/test_spaces.py` (AC: #1, #2)
  - [x] The file EXISTS with 261 passing tests — ADD new test classes, do NOT rewrite the file
  - [x] Add `import json` to the existing imports block (needed for JSON-serializable assertions)
  - [x] Class `TestObservationSpaceExplain` (ADD after existing classes):
    - [x] `test_explain_returns_dict`: `from_proprioception(joints=7, include_velocity=True).explain()` returns a `dict`
    - [x] `test_explain_contains_dims_key`: `"dims"` in result
    - [x] `test_explain_dims_value_with_velocity`: `joints=7, include_velocity=True` → `result["dims"] == 14`
    - [x] `test_explain_dims_value_without_velocity`: `joints=7, include_velocity=False` → `result["dims"] == 7`
    - [x] `test_explain_contains_joints_key`: `"joints"` in result
    - [x] `test_explain_joints_raw_value`: `joints=7` → `result["joints"] == 7` (regardless of include_velocity)
    - [x] `test_explain_contains_include_velocity`: `"include_velocity"` in result and value matches constructor arg
    - [x] `test_explain_clip_bounds_none_when_not_set`: `from_proprioception(joints=7)` → `result["clip_bounds"] is None`
    - [x] `test_explain_clip_bounds_when_set`: `from_proprioception(joints=7, clip_bounds=(-1.0, 1.0))` → `result["clip_bounds"] == [-1.0, 1.0]` (list, not tuple)
    - [x] `test_explain_normalize_false_default`: `result["normalize"] == False`
    - [x] `test_explain_normalize_true_when_set`: `from_proprioception(joints=7, normalize=True)` → `result["normalize"] == True`
    - [x] `test_explain_json_serializable`: `json.dumps(result)` does not raise (all values are JSON-safe)
    - [x] `test_explain_not_string`: `isinstance(result, dict)` and `not isinstance(result, str)`
  - [x] Class `TestActionSpaceExplain` (ADD after `TestObservationSpaceExplain`):
    - [x] `test_explain_returns_dict`: `continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()` returns a `dict`
    - [x] `test_explain_contains_dims_key`: `"dims"` in result
    - [x] `test_explain_dims_value`: `result["dims"] == 7`
    - [x] `test_explain_contains_bounds_key`: `"bounds"` in result
    - [x] `test_explain_bounds_length`: `len(result["bounds"]) == 7`
    - [x] `test_explain_bounds_values`: `result["bounds"][0] == [-1.0, 1.0]` (list, not tuple)
    - [x] `test_explain_bounds_are_lists_not_tuples`: all items in `result["bounds"]` are `list`, not `tuple` (critical for JSON)
    - [x] `test_explain_json_serializable`: `json.dumps(result)` does not raise
    - [x] `test_explain_not_none`: result is not None
    - [x] `test_explain_asymmetric_bounds`: `continuous(dims=2, bounds=[(-2.0, 2.0), (0.0, 1.0)]).explain()["bounds"]` == `[[-2.0, 2.0], [0.0, 1.0]]`

## Dev Notes

### Current File State

`src/physlink/core/spaces.py` — contains both `ObservationSpace` (Story 2.2) and `ActionSpace` (Story 2.3). Neither has `.explain()` yet.

Story 2.3 explicitly deferred `.explain()` with: *"Do NOT implement .explain() — deferred to Story 2.4. No stub, no placeholder."*

Current `ObservationSpace` attributes (set in `__init__`):
```python
self.dims          # int: joint_count * 2 if include_velocity else joint_count
self.include_velocity  # bool
self._joints       # int: raw joint count passed to from_proprioception
self.clip_bounds   # tuple[float, float] | None
self.normalize     # bool
```

Current `ActionSpace` attributes (set in `__init__`):
```python
self.dims    # int
self.bounds  # list[tuple[float, float]]
```

### Import to Add

The file currently has:
```python
from __future__ import annotations
from physlink.core.exceptions import ValidationError
```

**Add `from typing import Any` after the existing imports** — required for the `dict[str, Any]` return type annotation that mypy --strict accepts.

Result:
```python
from __future__ import annotations

from typing import Any

from physlink.core.exceptions import ValidationError
```

### Recommended explain() Implementation

**ObservationSpace.explain()** — add after `__repr__`:
```python
def explain(self) -> dict[str, Any]:
    """Return a metadata dict describing this observation space configuration.

    Returns:
        A JSON-serializable dict with keys:
            type: Class name ("ObservationSpace").
            dims: Total observation dimension count.
            joints: Raw joint count passed to from_proprioception.
            include_velocity: Whether joint velocities are included.
            clip_bounds: [min, max] list if set, else None.
            normalize: Whether normalization is applied.

    Example:
        >>> obs_space = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        >>> info = obs_space.explain()
        >>> info["dims"]
        14
        >>> info["include_velocity"]
        True
    """
    return {
        "type": "ObservationSpace",
        "dims": self.dims,
        "joints": self._joints,
        "include_velocity": self.include_velocity,
        "clip_bounds": list(self.clip_bounds) if self.clip_bounds is not None else None,
        "normalize": self.normalize,
    }
```

**ActionSpace.explain()** — add after `__repr__`:
```python
def explain(self) -> dict[str, Any]:
    """Return a metadata dict describing this action space configuration.

    Returns:
        A JSON-serializable dict with keys:
            type: Class name ("ActionSpace").
            dims: Number of action dimensions.
            bounds: Per-dimension [[min, max], ...] clipping bounds as lists.
            clipping_behavior: Description of how clipping is applied.

    Example:
        >>> act_space = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        >>> info = act_space.explain()
        >>> info["dims"]
        7
        >>> info["bounds"][0]
        [-1.0, 1.0]
    """
    return {
        "type": "ActionSpace",
        "dims": self.dims,
        "bounds": [list(b) for b in self.bounds],
        "clipping_behavior": "per_dimension",
    }
```

### JSON Serializability — Critical Detail

`clip_bounds` is stored as `tuple[float, float] | None`. **A Python tuple is JSON-serializable via `json.dumps`** (converted to a JSON array), but the test AC says the dict must be JSON-serializable. The conversion to `list` is still correct to ensure the output is a predictable list type, not a tuple (which would round-trip differently).

`bounds` in ActionSpace is `list[tuple[float, float]]`. Convert with `[list(b) for b in self.bounds]` so each bound is a `list[float]` not a `tuple` — tests will assert `isinstance(item, list)`.

### Bool Trap — NOT Applicable Here

The bool-before-int guard (from Stories 2.2/2.3) is NOT needed in `.explain()` — these methods read existing `self` attributes that were already validated at construction time. No new validation is needed.

### Architecture Note: ExplainableMixin

Architecture.md identifies `.explain()` as a cross-cutting concern and mentions `core/_mixins.py` as a future home for `ExplainableMixin`. This is explicitly listed in the Gap Analysis as "déférés, non bloquants" (deferred, non-blocking). **Do NOT create `core/_mixins.py` in this story.** Add `.explain()` directly to each class. The mixin refactor is a future story.

This also means:
- No new files to create
- No changes to `physlink/__init__.py` (export is Story 2.6)
- No changes to `physlink/core/__init__.py`

### Adding Tests — Import Block

The existing `test_spaces.py` import block is:
```python
import inspect

import pytest

from physlink.core.exceptions import ValidationError
from physlink.core.spaces import ActionSpace, ObservationSpace
```

Add `import json` to the import block (alphabetically before `import inspect` or after — ruff will reorder):
```python
import inspect
import json

import pytest

from physlink.core.exceptions import ValidationError
from physlink.core.spaces import ActionSpace, ObservationSpace
```

### Critical Constraints — Do Not Violate

- **No torch in `core/spaces.py`** — `test_core_no_torch_import.py` AST-walks `core/**/*.py`. Any `import torch` → CI failure.
- **No `core/` → `adapters/` imports** — `test_core_boundary.py` enforces this.
- **`from __future__ import annotations` already at line 1** — do NOT add again.
- **`ValidationError` already imported** — do NOT add a second import.
- **`.explain()` is NOT a new public API at the `physlink` namespace level** — it is a method on `ObservationSpace`/`ActionSpace`. No `physlink/__init__.py` change needed.
- **Do NOT create `core/_mixins.py`** in this story — architecture defers the mixin.
- **Do NOT modify `ObservationSpace.__init__` or `ActionSpace.__init__`** — they have 261 passing tests; any changes risk regressions.
- **Do NOT implement `.explain()` on `DreamerV3Adapter`** — that is Epic 3 scope (Story 3.1).

### Idempotency (NFR-09)

`.explain()` has no side effects and reads only `self` attributes. Calling it twice on the same object returns two equal dicts. No special handling needed.

### Previous Story Intelligence

**From Story 2.3 (done — ActionSpace):**
- `from __future__ import annotations` is at line 1 — do NOT add again. The failing case in prior stories was adding it a second time, causing mypy ANN204.
- `from typing import Any` is a safe new import — used for heterogeneous dict value types.
- ruff strict mode: annotate ALL method return types including `-> None` on `__init__`, `-> dict[str, Any]` on `.explain()`.
- mypy --strict on `core/`: no untyped parameters, all return types annotated.
- Test file convention: class-based, explicit `-> None` on all test methods.
- `# type: ignore[arg-type]` on test calls with deliberate type violations — but `.explain()` has no type-violating test calls.
- Post-QA gap tests were added in 2.3 (`TestActionSpaceGaps`). Anticipate adding similar thoroughness here.

**From Story 2.2 (done — ObservationSpace):**
- `self._joints` is the underscore-prefixed raw joint count. It is a private attribute but it is intentionally exposed in `.explain()` output (the whole point is introspection). Use `self._joints` directly in the dict value.

**Git context:**
- Last commit: `feat(story-2.3): ActionSpace Construction and Validation` (4bd7772)
- Commit naming follows `feat(story-X.Y): <Title Case Description>` format.

### Project Structure Notes

- `.explain()` belongs in `src/physlink/core/spaces.py` — same file as both classes [Source: architecture.md#Project Structure & Boundaries]
- Test file `tests/unit/core/test_spaces.py` already exists — ADD test classes, do NOT create a new file
- Architecture test comment in project structure: `test_spaces.py # ObservationSpace, ActionSpace, explain()` — this method was always part of Story 2.4's scope [Source: architecture.md#Complete Project Directory Structure]
- `ExplainableMixin` deferred to a future refactor, not this story [Source: architecture.md#Gap Analysis Results]

### References

- [Source: architecture.md#Cross-Cutting Concerns] — `.explain()` is an explainability mixin concern, all core objects implement it
- [Source: architecture.md#Gap Analysis Results] — `ExplainableMixin → core/_mixins.py` deferred as non-blocking
- [Source: architecture.md#Implementation Patterns & Consistency Rules] — `dict[str, Any]` pattern, `from __future__ import annotations` rule, Google docstrings
- [Source: architecture.md#Testing Patterns] — single conftest.py, class-based tests, explicit `-> None`
- [Source: epics.md#Story 2.4] — Acceptance Criteria source (2 ACs, JSON-serializable requirement)
- [Source: epics.md#FR-02] — Universal Space API — `.explain()` returning a metadata dict
- [Source: 2-3-actionspace-construction-and-validation.md#Dev Notes] — Current spaces.py state, test file conventions, import patterns
- [Source: 2-3-actionspace-construction-and-validation.md#Tasks] — "Do NOT implement .explain() — deferred to Story 2.4"
- [Source: tests/integration/test_core_no_torch_import.py] — AST guard covering `core/spaces.py`
- [Source: tests/integration/test_core_boundary.py] — boundary guard covering `core/spaces.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blockers encountered. Implementation followed story spec exactly.

### Completion Notes List

- Added `from typing import Any` import to `src/physlink/core/spaces.py` (between `from __future__ import annotations` and `from physlink.core.exceptions import ValidationError`)
- Implemented `ObservationSpace.explain()` after `__repr__` — returns 6-key JSON-serializable dict; `clip_bounds` tuple converted to list
- Implemented `ActionSpace.explain()` after `__repr__` — returns 4-key JSON-serializable dict; bounds list[tuple] converted to list[list]
- Added `import json` to `tests/unit/core/test_spaces.py` imports
- Added `TestObservationSpaceExplain` (13 tests), `TestActionSpaceExplain` (10 tests), `TestObservationSpaceExplainGaps` (9 tests), `TestActionSpaceExplainGaps` (8 tests) to test file — 40 new tests total
- All 301 tests pass (2 skipped — pre-existing), 0 regressions; ruff and mypy --strict both clean
- Removed stale story-reference comments from `spaces.py` module docstring (AI review fix)

### File List

- `src/physlink/core/spaces.py` (modified — added `from typing import Any`, `ObservationSpace.explain()`, `ActionSpace.explain()`)
- `tests/unit/core/test_spaces.py` (modified — added `import json`, `TestObservationSpaceExplain`, `TestActionSpaceExplain`)

### Change Log

- feat(story-2.4): `.explain()` introspection on ObservationSpace and ActionSpace — 23 new tests, 284 total passing (2026-05-22)
