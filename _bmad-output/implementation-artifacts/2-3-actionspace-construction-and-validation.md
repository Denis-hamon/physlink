# Story 2.3: ActionSpace Construction and Validation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher,
I want to construct an ActionSpace with dimension count and bounds in one call,
so that my action configuration is validated at creation with dimension/bound consistency enforced before any training starts.

## Acceptance Criteria

1. **Given** I call `ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)`
   **When** the object is constructed
   **Then** it succeeds without error
   **And** the object stores `dims` (= 7), `bounds` (= the 7-element list of tuples), and any clipping metadata

2. **Given** I call `ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 3)` (bounds length mismatch)
   **When** the object is constructed
   **Then** a `ValidationError` is raised immediately (not deferred to fit())
   **And** the error message follows Got/Expected/Fix:
   ```
   ActionSpace.continuous: bounds length mismatch.
     Got:      3 bounds
     Expected: 7 bounds (matching dims)
     Fix:      provide one (min, max) tuple per dimension
   ```

3. **Given** I call `ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)` and then again in the same Colab cell
   **When** the cell is re-run
   **Then** the same object is constructed without side effects (NFR-09 — idempotent)

## Tasks / Subtasks

- [x] Task 1: Implement `ActionSpace` in `src/physlink/core/spaces.py` (AC: #1, #2, #3)
  - [x] Do NOT touch `from __future__ import annotations` — already at line 6 of the file
  - [x] Do NOT add `from physlink.core.exceptions import ValidationError` — already imported
  - [x] Update the module docstring: change "ActionSpace in Story 2.3" → "Story 2.3 implemented (ActionSpace)"
  - [x] Add `ActionSpace` class AFTER `ObservationSpace` (do not modify `ObservationSpace`)
  - [x] Define `ActionSpace` as a plain class (not a dataclass — `continuous` is the only constructor)
  - [x] Class attributes: `dims: int`, `bounds: list[tuple[float, float]]`
  - [x] Private `__init__(self, dims, bounds)` sets `self.dims` and `self.bounds` (no validation in `__init__`)
  - [x] Classmethod: `continuous(dims: int, bounds: list[tuple[float, float]]) -> ActionSpace`
  - [x] Validate `dims` type first (`isinstance(dims, bool)` must also fail — booleans are ints in Python): raise `ValidationError` with Got/Expected/Fix
  - [x] Validate `dims >= 1`: raise `ValidationError` with Got/Expected/Fix
  - [x] Validate `bounds` is a `list`: raise `ValidationError` if not
  - [x] Validate `len(bounds) == dims`: raise `ValidationError` with the exact format from AC #2
  - [x] Validate each bound is a 2-element sequence (tuple or list) where first element <= second element: raise `ValidationError` per-element if not
  - [x] Return `cls(dims=dims, bounds=bounds)`
  - [x] Add `__repr__(self) -> str`: `f"ActionSpace(dims={self.dims})"`
  - [x] Google-style docstrings on the class and `continuous()` with Args, Raises, Example sections
  - [x] **Do NOT implement `.explain()`** — deferred to Story 2.4
  - [x] **Do NOT touch `physlink/__init__.py`** — `ActionSpace` export is Story 2.6

- [x] Task 2: Add `ActionSpace` tests to `tests/unit/core/test_spaces.py` (AC: #1, #2, #3)
  - [x] The file already EXISTS with ObservationSpace tests — ADD ActionSpace classes, do NOT rewrite the file
  - [x] Add `from physlink.core.spaces import ActionSpace` to the existing imports block
  - [x] Class `TestActionSpaceContinuous`:
    - [x] `test_valid_construction_7dof`: `continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)` returns `ActionSpace` instance
    - [x] `test_stores_dims`: `continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).dims == 7`
    - [x] `test_stores_bounds`: `continuous(dims=3, bounds=[(-1.0, 1.0)] * 3).bounds == [(-1.0, 1.0)] * 3`
    - [x] `test_asymmetric_bounds`: `continuous(dims=2, bounds=[(-2.0, 2.0), (0.0, 1.0)])` succeeds
    - [x] `test_single_dim`: `continuous(dims=1, bounds=[(0.0, 1.0)])` succeeds
    - [x] `test_equal_min_max_bounds`: `continuous(dims=1, bounds=[(0.5, 0.5)])` succeeds (min == max is valid)
    - [x] `test_negative_bounds`: `continuous(dims=2, bounds=[(-5.0, -1.0), (-3.0, 0.0)])` succeeds
  - [x] Class `TestActionSpaceValidation`:
    - [x] `test_bounds_length_mismatch_raises_validation_error`: `dims=7, bounds=[(-1.0, 1.0)] * 3` → `pytest.raises(ValidationError)`
    - [x] `test_bounds_length_mismatch_message_got`: check `"3 bounds"` in error message
    - [x] `test_bounds_length_mismatch_message_expected`: check `"7 bounds"` in error message
    - [x] `test_bounds_length_mismatch_message_fix`: check `"Fix" in str(exc_info.value)`
    - [x] `test_zero_dims_raises_validation_error`: `dims=0` → `pytest.raises(ValidationError)`
    - [x] `test_negative_dims_raises_validation_error`: `dims=-1` → `pytest.raises(ValidationError)`
    - [x] `test_string_dims_raises_validation_error`: `dims="seven"` → `pytest.raises(ValidationError)` with `# type: ignore[arg-type]`
    - [x] `test_float_dims_raises_validation_error`: `dims=7.0` → `pytest.raises(ValidationError)` with `# type: ignore[arg-type]`
    - [x] `test_bool_dims_raises_validation_error`: `dims=True` → `pytest.raises(ValidationError)` (True is int subclass — must fail)
    - [x] `test_false_bool_dims_raises_validation_error`: `dims=False` → `pytest.raises(ValidationError)`
    - [x] `test_none_dims_raises_validation_error`: `dims=None` → `pytest.raises(ValidationError)` with `# type: ignore[arg-type]`
    - [x] `test_non_list_bounds_raises_validation_error`: `bounds=((-1.0, 1.0),) * 7` (tuple of tuples) → `pytest.raises(ValidationError)` with `# type: ignore[arg-type]`
    - [x] `test_inverted_bound_raises_validation_error`: `dims=1, bounds=[(1.0, -1.0)]` → `pytest.raises(ValidationError)`
    - [x] `test_inverted_bound_error_message_contains_fix`: check `"Fix"` in error message
    - [x] `test_dims_error_message_got_expected_fix`: for `dims=0`, check `"Got"`, `"Expected"`, `"Fix"` in message
    - [x] `test_string_dims_error_message_contains_type`: check `"str"` in error message for `dims="seven"`
  - [x] Class `TestActionSpaceInterface`:
    - [x] `test_repr_contains_dims`: `"dims=7"` in `repr(continuous(dims=7, bounds=[(-1.0, 1.0)] * 7))`
    - [x] `test_idempotent_construction`: two calls with identical args produce equal `dims` and `bounds` (NFR-09)
  - [x] Class `TestActionSpaceNoTorch`:
    - [x] `test_no_torch_in_continuous_signature`: `import inspect`; assert `"torch"` not in `str(inspect.signature(ActionSpace.continuous))`

## Dev Notes

### Current File State

`src/physlink/core/spaces.py` — currently contains `ObservationSpace` (Story 2.2 done) and NO `ActionSpace`:
```python
"""Observation and action space definitions.

Story 2.2 implemented (ObservationSpace). ActionSpace in Story 2.3.
"""

from __future__ import annotations

from physlink.core.exceptions import ValidationError


class ObservationSpace:
    # ... (full implementation — do not touch)
```

`tests/unit/core/test_spaces.py` — EXISTS with 28 ObservationSpace tests across 4 classes:
- `TestObservationSpaceFromProprioception` (11 tests)
- `TestObservationSpaceValidation` (12 tests)
- `TestObservationSpaceInterface` (4 tests)
- `TestObservationSpaceNoTorch` (1 test)

→ **ADD** `ActionSpace` to the import line and **APPEND** new test classes below the existing ones.

### Recommended Implementation (full code to ADD to spaces.py)

```python
class ActionSpace:
    """Continuous action space with per-dimension bounds and immediate validation.

    Constructed exclusively via the factory classmethod. Validates dims/bounds
    consistency at creation time so configuration errors surface before training.

    Args:
        dims: Number of action dimensions.
        bounds: Per-dimension (min, max) clipping bounds.

    Example:
        >>> act_space = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        >>> act_space.dims
        7
    """

    def __init__(
        self,
        dims: int,
        bounds: list[tuple[float, float]],
    ) -> None:
        self.dims = dims
        self.bounds = bounds

    @classmethod
    def continuous(
        cls,
        dims: int,
        bounds: list[tuple[float, float]],
    ) -> ActionSpace:
        """Construct a continuous ActionSpace with per-dimension bounds.

        Args:
            dims: Number of action dimensions. Must be a positive integer >= 1.
            bounds: List of (min, max) tuples, one per dimension.
                Each element must satisfy min <= max.

        Returns:
            An ActionSpace with the specified dimensions and bounds.

        Raises:
            ValidationError: If dims is not a positive integer, bounds is not a list,
                bounds length does not match dims, or any bound has min > max.

        Example:
            >>> act_space = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
            >>> act_space.dims
            7
        """
        # bool check MUST come before int check — bool is a subclass of int in Python
        if isinstance(dims, bool) or not isinstance(dims, int):
            raise ValidationError(
                f"ActionSpace.continuous: invalid dims type.\n"
                f"  Got:      dims={dims!r} (type: {type(dims).__name__})\n"
                f"  Expected: dims must be a positive integer (int)\n"
                f"  Fix:      pass an integer, e.g. dims=7 for a 7-DOF arm."
            )
        if dims < 1:
            raise ValidationError(
                f"ActionSpace.continuous: invalid dims value.\n"
                f"  Got:      dims={dims}\n"
                f"  Expected: dims >= 1 (positive integer)\n"
                f"  Fix:      pass dims >= 1, e.g. dims=7 for a 7-DOF arm."
            )
        if not isinstance(bounds, list):
            raise ValidationError(
                f"ActionSpace.continuous: invalid bounds type.\n"
                f"  Got:      bounds of type {type(bounds).__name__}\n"
                f"  Expected: list of (min, max) tuples, one per dimension\n"
                f"  Fix:      pass a list of tuples, e.g. bounds=[(-1.0, 1.0)] * {dims}"
            )
        if len(bounds) != dims:
            raise ValidationError(
                f"ActionSpace.continuous: bounds length mismatch.\n"
                f"  Got:      {len(bounds)} bounds\n"
                f"  Expected: {dims} bounds (matching dims)\n"
                f"  Fix:      provide one (min, max) tuple per dimension"
            )
        for i, bound in enumerate(bounds):
            if not (isinstance(bound, (tuple, list)) and len(bound) == 2):
                raise ValidationError(
                    f"ActionSpace.continuous: invalid bound at index {i}.\n"
                    f"  Got:      {bound!r} (type: {type(bound).__name__})\n"
                    f"  Expected: a (min, max) tuple with two numeric values\n"
                    f"  Fix:      pass a 2-tuple, e.g. (-1.0, 1.0)"
                )
            lo, hi = bound
            if lo > hi:
                raise ValidationError(
                    f"ActionSpace.continuous: inverted bound at index {i}.\n"
                    f"  Got:      bound=({lo}, {hi}) where min > max\n"
                    f"  Expected: (min, max) where min <= max\n"
                    f"  Fix:      swap the values, e.g. bound=({hi}, {lo})"
                )
        return cls(dims=dims, bounds=bounds)

    def __repr__(self) -> str:
        return f"ActionSpace(dims={self.dims})"
```

### Bool Trap — Mandatory Guard Order

Same trap as Story 2.2. Python: `isinstance(True, int) → True`.
The guard in `continuous()` **MUST** be:
```python
if isinstance(dims, bool) or not isinstance(dims, int):
    raise ValidationError(...)
```
If reversed, `True` (= 1) and `False` (= 0) silently pass the int check.

### Error Message Format — Got/Expected/Fix Template

All messages must follow the architecture convention from `architecture.md`:
```
<class>.<method>: <one-line summary>.
  Got:      <actual value with type if useful>
  Expected: <what was expected>
  Fix:      <actionable instruction>
```
Note: 2-space indent before `Got:`, `Expected:`, `Fix:`. This matches `ObservationSpace` and `ValidationError` examples in `core/exceptions.py`.

### Adding ActionSpace to Test Imports

The existing `test_spaces.py` import block is:
```python
from physlink.core.spaces import ObservationSpace
```

Change it to:
```python
from physlink.core.spaces import ActionSpace, ObservationSpace
```

Do not change any other import. `inspect` is already imported.

### Critical Constraints — Do Not Violate

- **No torch in `core/spaces.py`** — `test_core_no_torch_import.py` AST-walks `core/**/*.py`. Any `import torch` → CI failure.
- **No `core/` → `adapters/` imports** — `test_core_boundary.py` enforces this.
- **`from __future__ import annotations` already at line 6** — do NOT add again (mypy ANN204 error).
- **`ValidationError` already imported** — do NOT add a second import.
- **`ActionSpace` is NOT exported from `physlink.__init__` yet** — export is Story 2.6. Do not touch `__init__.py`.
- **Do NOT implement `.explain()`** — Story 2.4. No stub, no placeholder (pollutes public API).
- **Do NOT modify `ObservationSpace`** — it has 28 passing tests; any change risks regressions.
- **`bounds` parameter takes a `list`**, not a tuple or other sequence — enforce with `isinstance(bounds, list)`. The documented API uses `[(-1.0, 1.0)] * 7` (a list).

### Idempotency (NFR-09)

`ActionSpace.continuous()` is a pure factory — it has no global or module-level state. Calling it twice with the same arguments produces two independent objects with the same `dims` and `bounds`. This satisfies NFR-09 by construction; no special handling required.

### Testing Patterns — Consistency with Existing Tests

The existing `test_spaces.py` uses these conventions (carry over exactly):
- All test methods annotated `-> None`
- `pytest.raises(ValidationError)` for error tests
- `# type: ignore[arg-type]` on calls where the argument deliberately violates the type annotation
- Class-based grouping with `TestXxx` names
- No `@pytest.mark.gpu` needed — all `test_spaces.py` tests are CPU-only
- One `conftest.py` at `tests/conftest.py` — **never** create a conftest in `tests/unit/core/`

### Test Coverage for Bounds Length Mismatch (Primary AC)

The epics AC #2 specifies the exact error message format. Test it precisely:
```python
def test_bounds_length_mismatch_message_got(self) -> None:
    with pytest.raises(ValidationError) as exc_info:
        ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 3)
    assert "3 bounds" in str(exc_info.value)

def test_bounds_length_mismatch_message_expected(self) -> None:
    with pytest.raises(ValidationError) as exc_info:
        ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 3)
    assert "7 bounds" in str(exc_info.value)
```

### Previous Story Intelligence

**From Story 2.2 (done — ObservationSpace):**
- Pattern: bool-before-int guard is the single most dangerous Python trap — Story 2.2 confirms it works as shown above.
- ruff strict mode: annotate ALL method return types including `-> None` on `__init__`.
- mypy --strict on `core/`: no `Any` escapes, all parameters must have type annotations.
- `__iter__` and special methods need explicit return type annotations (`-> Iterator[...]`) — apply same rigor to `__repr__`.
- 2026-05-22 note: `# type: ignore[arg-type]` on test calls where the argument type deliberately violates annotation is the correct approach (not casting).

**From Story 2.1 (done — TrajectoryBatch):**
- `from __future__ import annotations` in stub files — do NOT add again.
- `dict[str, Any]` pattern if Any needed — import from `typing`.
- Test file convention: class-based grouping, explicit `-> None` on all test methods.

**Git context:**
- Last commit: `feat(story-2.2): ObservationSpace Construction and Validation` (a1aa783)
- Commit naming follows `feat(story-X.Y): <Title Case Description>` format.

### Project Structure Notes

- `ActionSpace` belongs in `src/physlink/core/spaces.py` — architecturally designated [Source: architecture.md#Project Structure & Boundaries]
- Test file `tests/unit/core/test_spaces.py` already exists — ADD to it, do NOT create a new file
- `ActionSpace` is NOT exported from `physlink.__init__` in this story — deferred to Story 2.6 along with `ObservationSpace`
- Story 2.4 adds `.explain()` to both `ObservationSpace` and `ActionSpace` — do not preempt
- `ActionSpace` is consumed by `DreamerV3Adapter` in Story 3.1 — the `dims` and `bounds` attributes must be public and stable

### References

- [Source: architecture.md#Category 2 — Exception Hierarchy] — `ValidationError` definition and Got/Expected/Fix template
- [Source: architecture.md#Implementation Patterns & Consistency Rules] — naming, annotations, docstring, and testing conventions
- [Source: architecture.md#Project Structure & Boundaries] — `src/physlink/core/spaces.py` location, tests/ mirror structure
- [Source: architecture.md#Architectural Boundaries] — no `core/` → `adapters/` import rule
- [Source: architecture.md#Category 3 — Module Public API Surface] — `ActionSpace` in `__all__` deferred to Story 2.6
- [Source: epics.md#Story 2.3] — Acceptance Criteria source (3 ACs, including exact error message format)
- [Source: epics.md#Story 2.4] — `.explain()` on this class, deferred — do not implement
- [Source: 2-2-observationspace-construction-and-validation.md#Dev Notes] — bool trap, mypy rigor, test file conventions
- [Source: tests/integration/test_core_no_torch_import.py] — AST guard covering `core/spaces.py`
- [Source: tests/integration/test_core_boundary.py] — boundary guard covering `core/spaces.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Task 1 (spaces.py): Ajout de la classe `ActionSpace` après `ObservationSpace` dans `src/physlink/core/spaces.py`. Docstring de module mis à jour. Guard bool-avant-int appliqué sur `dims`. Validation complète : type, valeur >= 1, bounds de type list, longueur bounds == dims, chaque bound est un 2-tuple avec min <= max. `__repr__` et docstrings Google-style. Aucun import ajouté, `__init__.py` non touché, `.explain()` non implémenté.
- Task 2 (test_spaces.py): Ajout de `ActionSpace` à l'import existant. Ajout de 4 classes de tests (26 tests) sans toucher aux 28 tests ObservationSpace existants. Suite initiale : 246 passed, 2 skipped. Post-QA audit : `TestActionSpaceGaps` (15 tests) ajoutée, portant le total ActionSpace à 41 tests et la suite globale à 261 passed, 2 skipped. Ruff et mypy --strict : OK.

### File List

- src/physlink/core/spaces.py
- tests/unit/core/test_spaces.py

## Senior Developer Review (AI)

**Date:** 2026-05-22  
**Reviewer:** claude-sonnet-4-6 (adversarial review)

### AC Coverage
- AC #1 (construction 7-DOF) ✅ — `spaces.py:126–196`, `test_spaces.py:142–167`
- AC #2 (bounds mismatch Got/Expected/Fix) ✅ — `spaces.py:173–179`, `test_spaces.py:174–187`
- AC #3 (idempotent re-run) ✅ — `test_spaces.py:249–253`, `test_spaces.py:312–315`

### Issues Found and Fixed
- 🟡 MEDIUM (FIXED): Change Log et Completion Notes mentionnaient 246 passed / 26 tests ; l'état réel post-QA est 261 passed / 41 tests ActionSpace (15 tests `TestActionSpaceGaps` ajoutés par audit non documentés). → Completion Notes et Change Log mis à jour.
- 🟢 LOW (FIXED): Docstring du module test ne mentionnait que `ObservationSpace`. → Mise à jour.
- 🟢 LOW (INFO): `TestActionSpaceInterface.test_idempotent_construction` ne vérifie pas `a is not b` — couvert dans `TestActionSpaceGaps.test_idempotent_construction_returns_independent_objects`. Pas d'action requise (couverture présente).

### Verdict
**APPROVED — aucune issue CRITICAL ou HIGH.** Toutes les tâches [x] sont genuinement implémentées. Bool-trap guard confirmé. Integration tests (`test_core_no_torch_import`, `test_core_boundary`) verts.

## Change Log

- 2026-05-22: Story 2.3 implémentée — ajout de la classe `ActionSpace` dans `spaces.py` avec validation complète (type dims, valeur dims >= 1, bounds list, longueur bounds == dims, min <= max par bound) et 26 nouveaux tests dans `test_spaces.py`. Suite initiale : 246 passed, 2 skipped.
- 2026-05-22: QA audit post-implémentation — `TestActionSpaceGaps` (15 tests) ajoutée, couvrant bounds mal-formés (1 ou 3 éléments, non-séquence), mismatch inverse (excess bounds), messages d'erreur bound inversé, indépendance des objets, format repr exact, scale 100-DOF, type bounds, mixed int/float. Suite finale : 261 passed, 2 skipped. Aucune régression.
- 2026-05-22: Review adversariale — MEDIUM (Change Log stale), LOW (docstring test module) corrigés. Statut → done.
