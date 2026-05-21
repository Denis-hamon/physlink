# Story 2.2: ObservationSpace Construction and Validation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want to construct an ObservationSpace with joint count and velocity flag in one line,
so that my observation configuration is validated immediately at creation time — not silently at training time.

## Acceptance Criteria

1. **Given** I call `ObservationSpace.from_proprioception(joints=7, include_velocity=True)`
   **When** the object is constructed
   **Then** it succeeds without error
   **And** it stores: `dims` (= 14 for 7 joints + velocity), `include_velocity` (True), `_joints` (7), and `clip_bounds` / `normalize` (both default to None/False)

2. **Given** I call `ObservationSpace.from_proprioception(joints=0)` (invalid — zero joints)
   **When** the object is constructed
   **Then** a `ValidationError` is raised immediately (not deferred to fit())
   **And** the error message follows the Got/Expected/Fix template:
   ```
   Got:      joints=0
     Expected: joints >= 1 (positive integer)
     Fix:      pass joints >= 1, e.g. joints=7 for a 7-DOF arm.
   ```

3. **Given** I call `ObservationSpace.from_proprioception(joints="seven")` (wrong type)
   **When** the object is constructed
   **Then** a `ValidationError` is raised immediately
   **And** the error message shows Got/Expected/Fix with the actual type received:
   ```
   Got:      joints='seven' (type: str)
     Expected: joints must be a positive integer (int)
     Fix:      pass an integer, e.g. joints=7 for a 7-DOF arm.
   ```

## Tasks / Subtasks

- [x] Task 1: Implement `ObservationSpace` in `src/physlink/core/spaces.py` (AC: #1, #2, #3)
  - [x] Keep `from __future__ import annotations` at line 6 — do NOT add it again
  - [x] Add `import inspect` only if needed for signature formatting; it is NOT needed here
  - [x] Add `from physlink.core.exceptions import ValidationError` import
  - [x] Define `ObservationSpace` as a plain class (not a dataclass — `from_proprioception` is the only constructor)
  - [x] Class attributes: `dims: int`, `include_velocity: bool`, `_joints: int`, `clip_bounds: tuple[float, float] | None`, `normalize: bool`
  - [x] Classmethod: `from_proprioception(joints: int, include_velocity: bool = False, clip_bounds: tuple[float, float] | None = None, normalize: bool = False) -> ObservationSpace`
  - [x] Validate `joints` type first (`isinstance(joints, bool)` must also fail — booleans are ints in Python): raise `ValidationError` with Got/Expected/Fix
  - [x] Validate `joints >= 1`: raise `ValidationError` with Got/Expected/Fix
  - [x] Compute `dims = joints * 2 if include_velocity else joints`
  - [x] Return instance with all attributes set
  - [x] Add `__repr__(self) -> str`: `f"ObservationSpace(dims={self.dims}, velocity={self.include_velocity})"`
  - [x] Google-style docstrings on the class and `from_proprioception()` with Args, Raises, Example sections
  - [x] **Do NOT implement `.explain()`** — deferred to Story 2.4
  - [x] **Do NOT implement `ActionSpace`** — deferred to Story 2.3
  - [x] Leave the existing file comment referencing Stories 2.2 and 2.3 in place (update it after adding the class)

- [x] Task 2: Create `tests/unit/core/test_spaces.py` (AC: #1, #2, #3)
  - [x] This file does NOT exist yet — check `tests/unit/core/` (currently: `test_exceptions.py`, `test_types.py`)
  - [x] Header imports: `from __future__ import annotations`, `import pytest`, `from physlink.core.spaces import ObservationSpace`, `from physlink.core.exceptions import ValidationError`
  - [x] Class `TestObservationSpaceFromProprioception`:
    - [x] `test_valid_construction_7dof`: `from_proprioception(joints=7, include_velocity=False)` returns `ObservationSpace` instance
    - [x] `test_valid_construction_with_velocity`: `from_proprioception(joints=7, include_velocity=True)` returns instance with `dims == 14`
    - [x] `test_dims_without_velocity_equals_joints`: `from_proprioception(joints=3).dims == 3`
    - [x] `test_dims_with_velocity_doubles`: `from_proprioception(joints=5, include_velocity=True).dims == 10`
    - [x] `test_stores_joints_attribute`: `from_proprioception(joints=7)._joints == 7`
    - [x] `test_stores_velocity_flag`: `from_proprioception(joints=7, include_velocity=True).include_velocity is True`
    - [x] `test_default_include_velocity_is_false`: `from_proprioception(joints=7).include_velocity is False`
    - [x] `test_clip_bounds_default_none`: `from_proprioception(joints=7).clip_bounds is None`
    - [x] `test_clip_bounds_stored`: `from_proprioception(joints=7, clip_bounds=(-1.0, 1.0)).clip_bounds == (-1.0, 1.0)`
    - [x] `test_normalize_default_false`: `from_proprioception(joints=7).normalize is False`
  - [x] Class `TestObservationSpaceValidation`:
    - [x] `test_zero_joints_raises_validation_error`: `pytest.raises(ValidationError)` for `from_proprioception(joints=0)`
    - [x] `test_negative_joints_raises_validation_error`: `pytest.raises(ValidationError)` for `from_proprioception(joints=-1)`
    - [x] `test_string_joints_raises_validation_error`: `pytest.raises(ValidationError)` for `from_proprioception(joints="seven")`
    - [x] `test_float_joints_raises_validation_error`: `pytest.raises(ValidationError)` for `from_proprioception(joints=7.0)`
    - [x] `test_bool_joints_raises_validation_error`: `pytest.raises(ValidationError)` for `from_proprioception(joints=True)` — True is a bool subclass of int; treat as invalid
    - [x] `test_none_joints_raises_validation_error`: `pytest.raises(ValidationError)` for `from_proprioception(joints=None)`
    - [x] `test_zero_joints_error_message_got_expected_fix`: check `"Got" in str(exc_info.value)` and `"Expected" in str(exc_info.value)` and `"Fix" in str(exc_info.value)`
    - [x] `test_string_joints_error_message_contains_type`: check `"str"` in the error message
  - [x] Class `TestObservationSpaceInterface`:
    - [x] `test_repr_contains_dims`: `"dims=7"` in `repr(from_proprioception(joints=7))`
    - [x] `test_repr_contains_velocity`: `"velocity=False"` in `repr(from_proprioception(joints=7))`
    - [x] `test_idempotent_construction`: constructing same args twice gives equal `dims` values (NFR-09)
  - [x] Class `TestObservationSpaceNoTorch`:
    - [x] `test_no_torch_in_from_proprioception_signature`: `import inspect`; assert `"torch"` not in `str(inspect.signature(ObservationSpace.from_proprioception))`

## Dev Notes

### File State

`src/physlink/core/spaces.py` — currently contains only:
```python
"""Observation and action space definitions.

Implementation in Story 2.2 (ObservationSpace) and Story 2.3 (ActionSpace).
"""

from __future__ import annotations
```

Add `ObservationSpace` after the existing imports. Leave the module docstring intact (update it to say "Story 2.2 implemented").

`tests/unit/core/` — currently contains: `test_exceptions.py`, `test_types.py`. Create `test_spaces.py` here.

### Critical Constraints

- **No torch in `core/spaces.py`** — `test_core_no_torch_import.py` AST-walks `core/**/*.py` on every CI run. Any `import torch` breaks CI immediately.
- **No `core/` → `adapters/` imports** — `test_core_boundary.py` enforces this. `spaces.py` must never import from `physlink.adapters`.
- **`from __future__ import annotations` already present** in `spaces.py`. Do NOT add it again.
- **`bool` is a subclass of `int` in Python** — `isinstance(True, int)` returns `True`. You MUST check `isinstance(joints, bool)` BEFORE `isinstance(joints, int)` to correctly reject booleans.
- **Do NOT implement `.explain()`** — Story 2.4. Do not add a stub or placeholder method; it pollutes the public API surface.
- **Do NOT implement `ActionSpace`** — Story 2.3. The file comment references it — preserve that context.
- **`ObservationSpace` is NOT exported from `physlink.__init__` yet** — that export is part of Story 2.6. Do not touch `__init__.py`.

### ValidationError Import Pattern

```python
from physlink.core.exceptions import ValidationError
```

Use the existing `ValidationError` from `core/exceptions.py` (Story 1.2). Do NOT invent a new exception class.

### Recommended Implementation

```python
# src/physlink/core/spaces.py  (after existing header + from __future__ import annotations)

from physlink.core.exceptions import ValidationError


class ObservationSpace:
    """Proprioceptive observation space with immediate dimension validation.

    Constructed exclusively via the factory classmethod. Validates inputs
    at creation time so configuration errors surface before any training.

    Args:
        dims: Total observation dimension count (joints or joints*2 with velocity).
        include_velocity: Whether joint velocities are included in observations.
        _joints: Raw joint count passed to from_proprioception.
        clip_bounds: Optional (min, max) clipping range applied to observations.
        normalize: Whether observations are normalized to [0, 1] before passing to the model.

    Example:
        >>> obs_space = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        >>> obs_space.dims
        14
    """

    def __init__(
        self,
        dims: int,
        include_velocity: bool,
        _joints: int,
        clip_bounds: tuple[float, float] | None,
        normalize: bool,
    ) -> None:
        self.dims = dims
        self.include_velocity = include_velocity
        self._joints = _joints
        self.clip_bounds = clip_bounds
        self.normalize = normalize

    @classmethod
    def from_proprioception(
        cls,
        joints: int,
        include_velocity: bool = False,
        clip_bounds: tuple[float, float] | None = None,
        normalize: bool = False,
    ) -> ObservationSpace:
        """Construct an ObservationSpace for proprioceptive (joint-based) observations.

        Args:
            joints: Number of robot joints. Must be a positive integer >= 1.
            include_velocity: If True, each joint contributes position + velocity
                to the observation, doubling the dimension count.
            clip_bounds: Optional (min, max) clipping range for raw observations.
                None means no clipping applied.
            normalize: If True, observations will be normalized before passing
                to the model. Default False.

        Returns:
            An ObservationSpace with dims = joints (or joints * 2 if include_velocity).

        Raises:
            ValidationError: If joints is not a positive integer (wrong type or value <= 0).

        Example:
            >>> obs_space = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
            >>> obs_space.dims
            14
        """
        # bool check MUST come before int check — bool is a subclass of int in Python
        if isinstance(joints, bool) or not isinstance(joints, int):
            raise ValidationError(
                f"ObservationSpace.from_proprioception: invalid joints type.\n"
                f"  Got:      joints={joints!r} (type: {type(joints).__name__})\n"
                f"  Expected: joints must be a positive integer (int)\n"
                f"  Fix:      pass an integer, e.g. joints=7 for a 7-DOF arm."
            )
        if joints < 1:
            raise ValidationError(
                f"ObservationSpace.from_proprioception: invalid joints value.\n"
                f"  Got:      joints={joints}\n"
                f"  Expected: joints >= 1 (positive integer)\n"
                f"  Fix:      pass joints >= 1, e.g. joints=7 for a 7-DOF arm."
            )
        dims = joints * 2 if include_velocity else joints
        return cls(
            dims=dims,
            include_velocity=include_velocity,
            _joints=joints,
            clip_bounds=clip_bounds,
            normalize=normalize,
        )

    def __repr__(self) -> str:
        return f"ObservationSpace(dims={self.dims}, velocity={self.include_velocity})"
```

### bool Trap — Critical

Python has a well-known `bool`-is-a-subclass-of-`int` trap:
```python
isinstance(True, int)   # → True  ← TRAP: bool passes int check
isinstance(False, int)  # → True  ← TRAP
```
The guard in `from_proprioception` MUST be ordered as shown above:
```python
if isinstance(joints, bool) or not isinstance(joints, int):
    raise ValidationError(...)
```
If you reverse the order or use only `not isinstance(joints, int)`, `True` (= 1) and `False` (= 0) silently pass or silently fail with the wrong error message.

### Dimension Contract

| `joints` | `include_velocity` | `dims` |
|----------|-------------------|--------|
| 7        | False (default)   | 7      |
| 7        | True              | 14     |
| 3        | True              | 6      |
| 1        | False             | 1      |

This contract is consumed by `DreamerV3Adapter` (Story 3.1) for compatibility checks.

### Error Message Format

Messages MUST follow the Got/Expected/Fix template from architecture.md. The template is:
```
<class>.<method>: <one-line summary>.
  Got:      <actual value with type if useful>
  Expected: <what was expected>
  Fix:      <actionable instruction>
```
Note: indented with 2 spaces before `Got:`, `Expected:`, `Fix:`. This matches the existing `ValidationError` example docstring in `core/exceptions.py`.

### Testing Architecture Reminders

- `tests/conftest.py` is the **only** conftest allowed — never create `tests/unit/core/conftest.py`.
- `synthetic_trajectories` fixture (from Story 2.1) is available but not needed for these unit tests.
- No `@pytest.mark.gpu` needed — all `test_spaces.py` tests are CPU-only (no torch).
- `tests/unit/core/test_spaces.py` mirrors `src/physlink/core/spaces.py` per architecture layout rules.

### Previous Story Intelligence (Story 2.1)

From Story 2.1 implementation (done), key patterns established:
- `from __future__ import annotations` already present in stub files — do NOT add again
- `ruff` strict mode: annotate ALL method return types including `-> None` on `__init__`
- `mypy --strict` on `core/`: all parameters must have type annotations, no `Any` escapes
- `dict[str, Any]` pattern used in `_types.py` — carry over to `test_spaces.py` if Any is needed (import from `typing`)
- 2026-05-22 correction: `__iter__` required annotation `-> Iterator[...]` to satisfy mypy ANN204 — apply same rigor here
- Test file convention: class-based grouping (`TestXxx`), explicit return types `-> None` on all test methods

### Conventions Checklist

- `X | Y` union syntax (Python 3.10+) — not `Union[X, Y]` or `Optional[X]`
- `from __future__ import annotations` — already present, do NOT duplicate
- Class name: `ObservationSpace` (PascalCase) ✓
- Method names: `from_proprioception`, `__repr__` (snake_case) ✓
- Parameter names: `joints`, `include_velocity`, `clip_bounds`, `normalize` — no abbreviations
- Google-style docstrings with Args, Raises, Example on public methods
- All test methods annotated `-> None`

### Project Structure Notes

- Alignment: `src/physlink/core/spaces.py` is the architecturally designated location [Source: architecture.md#Project Structure & Boundaries]
- `ObservationSpace` is NOT exported from `physlink.__init__` in this story — export finalization is Story 2.6
- No conflicts with existing files — `spaces.py` is currently a stub
- `tests/unit/core/test_spaces.py` mirrors `src/physlink/core/spaces.py` per architecture rules

### References

- [Source: architecture.md#Category 2 — Exception Hierarchy] — `ValidationError` definition and Got/Expected/Fix template
- [Source: architecture.md#Implementation Patterns & Consistency Rules] — naming, annotations, docstring, and testing conventions
- [Source: architecture.md#Project Structure & Boundaries] — `src/physlink/core/spaces.py` location, tests/ mirror structure
- [Source: architecture.md#Architectural Boundaries] — no `core/` → `adapters/` import rule
- [Source: architecture.md#Category 3 — Module Public API Surface] — `ObservationSpace` in `__all__` deferred to Story 2.6
- [Source: epics.md#Story 2.2] — Acceptance Criteria source
- [Source: epics.md#Story 2.3] — `ActionSpace` in same file, deferred — do not touch
- [Source: epics.md#Story 2.4] — `.explain()` on this class, deferred — do not implement
- [Source: tests/integration/test_core_no_torch_import.py] — AST guard covering `core/spaces.py`
- [Source: tests/integration/test_core_boundary.py] — boundary guard covering `core/spaces.py`
- [Source: 2-1-trajectorybatch-core-type.md#Dev Agent Record] — `bool` trap pattern and annotation rigor

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

(none — implementation was straightforward)

### Completion Notes List

- Implemented `ObservationSpace` as a plain class with factory classmethod `from_proprioception` in `src/physlink/core/spaces.py`.
- Applied bool-before-int guard (`isinstance(joints, bool) or not isinstance(joints, int)`) to correctly reject `True`/`False` as invalid inputs.
- All ValidationError messages follow the Got/Expected/Fix template from architecture.md.
- Created `tests/unit/core/test_spaces.py` with 28 tests across 4 test classes (22 specified + 6 additional coverage tests); all pass.
- Ruff and mypy --strict (src/physlink/core/) pass with no issues.
- Full regression suite: 220 passed, 2 skipped — no regressions.
- `.explain()` and `ActionSpace` deliberately not implemented (deferred to Stories 2.4 and 2.3).
- `ObservationSpace` not exported from `physlink.__init__` (deferred to Story 2.6).

### File List

- `src/physlink/core/spaces.py` (modified — ObservationSpace implemented)
- `tests/unit/core/test_spaces.py` (created — 22 unit tests)

## Change Log

- 2026-05-22: Story 2.2 implemented — added `ObservationSpace` class to `src/physlink/core/spaces.py` with factory classmethod `from_proprioception`, immediate validation (type + range), Got/Expected/Fix error messages, and `__repr__`. Created `tests/unit/core/test_spaces.py` with 28 unit tests covering AC #1, #2, #3 and all edge cases. All quality checks pass (ruff, mypy --strict, full regression suite).
- 2026-05-22: Code review (AI) — removed spurious `# type: ignore[arg-type]` on bool test cases (True/False are valid int subtypes for mypy; runtime rejection is handled by the explicit isinstance guard). Updated completion notes to reflect actual test count (28) and regression count (220). Status → done.
