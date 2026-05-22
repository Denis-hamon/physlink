# Story 3.1: DreamerV3Adapter Construction

Status: done

## Story

As a researcher,
I want to instantiate DreamerV3Adapter with my configured ObservationSpace and ActionSpace,
so that the adapter validates compatibility between my spaces and the DreamerV3 model before any training begins.

## Acceptance Criteria

1. **Given** valid `ObservationSpace` and `ActionSpace` objects from Epic 2
   **When** I call `DreamerV3Adapter(obs_space, act_space)`
   **Then** the adapter is constructed without error
   **And** no training or model loading occurs at construction time (construction is cheap)

2. **Given** an `ObservationSpace` with incompatible dimensions for DreamerV3 (`obs_space.dims < 4`)
   **When** I call `DreamerV3Adapter(obs_space, act_space)`
   **Then** a `ConfigurationError` is raised immediately
   **And** the error message follows Got/Expected/Fix with the incompatible dimension values

3. **Given** `DreamerV3Adapter` is imported
   **When** I inspect `physlink.__init__`
   **Then** `DreamerV3Adapter` is one of the 7 exported symbols (no direct adapter submodule import needed)

## Tasks / Subtasks

- [x] Task 1: Implement `BaseAdapter` abstract class in `src/physlink/core/adapter.py` (AC: #1)
  - [x] Add `from __future__ import annotations` (AR-11, required in all core/ files)
  - [x] Import `ABC`, `abstractmethod` from `abc`; import `ObservationSpace`, `ActionSpace` from `physlink.core.spaces`; import `TrajectoryBatch` from `physlink.core._types`
  - [x] Define `BaseAdapter(ABC)` with `__init__(self, obs_space: ObservationSpace, act_space: ActionSpace) -> None` storing both spaces as instance attributes
  - [x] Define abstract stubs: `fit()`, `visualize()`, `export()`, `explain()` — see exact signatures in Dev Notes
  - [x] Google-style docstrings with Args/Raises/Example on class and all methods
  - [x] Verify NO torch/jax imports (AST check in `test_core_no_torch_import.py` runs on `core/**/*.py`)

- [x] Task 2: Implement `DreamerV3Adapter` in `src/physlink/adapters/dreamer.py` (AC: #1, #2)
  - [x] Import `BaseAdapter` from `physlink.core.adapter`; import `ConfigurationError` from `physlink.core.exceptions`
  - [x] Define `MIN_OBS_DIMS: int = 4` module-level constant (DreamerV3 minimum — see architecture doc example)
  - [x] Define `MIN_ACT_DIMS: int = 1` module-level constant
  - [x] Constructor validates `obs_space.dims >= MIN_OBS_DIMS` → `ConfigurationError` with Got/Expected/Fix if not
  - [x] Constructor validates `act_space.dims >= MIN_ACT_DIMS` → `ConfigurationError` with Got/Expected/Fix if not
  - [x] Call `super().__init__(obs_space, act_space)` after validation passes
  - [x] Implement `explain() -> dict[str, Any]` returning `{"type": "DreamerV3Adapter", "obs_space": self.obs_space.explain(), "act_space": self.act_space.explain()}`
  - [x] Implement `fit()`, `visualize()`, `export()` as stubs raising `NotImplementedError` with "Implemented in Story 3.2/3.5/3.6" message
  - [x] No torch import at module level — construction does not require torch; `fit()` stub raises `NotImplementedError` so defer torch import to Story 3.2
  - [x] Public method signatures use backend-agnostic types only — no `torch.Tensor` in any signature (AST check on adapter public signatures)
  - [x] Google-style docstrings on class and all public methods; `__repr__` with explicit `-> str` return type (mypy --strict requirement)

- [x] Task 3: Update `src/physlink/__init__.py` — export `DreamerV3Adapter` (AC: #3)
  - [x] Add `from physlink.adapters.dreamer import DreamerV3Adapter`
  - [x] Update `__all__` to 5 symbols (isort-sorted): `["ActionSpace", "DreamerV3Adapter", "ObservationSpace", "PhysLinkError", "doctor"]`
  - [x] Remove the `# Story 3.1: DreamerV3Adapter` placeholder comment
  - [x] Keep the `# Story 4.3/4.4: register_invariant, ComplianceReport` placeholder comment

- [x] Task 4: Update `tests/integration/test_api_stability.py` (AC: #3)
  - [x] **CRITICAL:** Change `test_epic2_api_symbols` from `assert expected == actual` to `assert expected.issubset(actual)` — the current `==` will fail once `DreamerV3Adapter` is added to `__all__`
  - [x] Add `test_epic3_api_symbols()` checking 5 symbols with `issubset` (not `==` — Epic 4 will add more)
  - [x] Update the deprecation protocol comment: remove "Epic 3 (Story 3.1) will add…" note, add "Epic 4 (Story 4.5) will update to the full 7-symbol set" instead
  - [x] Add DreamerV3Adapter entries to `TestTopLevelNamespaceAccess` class (hasattr, callable, identity with adapters module)
  - [x] See exact target state in Dev Notes

- [x] Task 5: Create `tests/unit/adapters/test_dreamer_cpu.py` (AC: #1, #2)
  - [x] Test happy path: `DreamerV3Adapter(obs_space, act_space)` succeeds with valid 7-DOF spaces
  - [x] Test `ConfigurationError` raised for `obs_space.dims < 4` (e.g., joints=1 without velocity)
  - [x] Test `ConfigurationError` raised for `act_space.dims < 1` (edge case)
  - [x] Test error message follows Got/Expected/Fix format (assert substring in message)
  - [x] Test construction is idempotent (NFR-09: re-running cell builds fresh adapter without side effects)
  - [x] Test `explain()` returns a dict with keys `"type"`, `"obs_space"`, `"act_space"`
  - [x] Test `explain()` return value is JSON-serializable (no torch objects)
  - [x] Test that importing `DreamerV3Adapter` does NOT import torch (verifies no module-level torch import)
  - [x] Test `fit()`, `visualize()`, `export()` raise `NotImplementedError` (stubs correctly defer to later stories)
  - [x] Test `__repr__` returns string containing class name, obs_dims, and act_dims (`TestDreamerV3AdapterRepr`)
  - [x] Tests do NOT use `@pytest.mark.gpu` — all CPU-only at construction stage

- [x] Task 6: Run full test suite — zero regressions (AC: all)
  - [x] `pytest tests/ -x` — all pass (432 passed, 3 skipped — no regression from Epic 2 baseline)
  - [x] `mypy --strict src/physlink/core/` — no new errors (adapter.py is in core/, must pass)
  - [x] `ruff check src/` — clean
  - [x] `mkdocs build --strict` — docs still build (new DreamerV3Adapter in `__init__.py` will appear in API reference)
  - [x] **Closing checklist:** File List complete AND Change Log reflects actual state before marking done (Epic 2 Action Item P-1)

## Dev Notes

### Scope Boundary — What Story 3.1 Does and Does NOT Do

**This story implements:** construction and space validation only.

**Explicitly deferred — do NOT implement in this story:**
- `fit()` (Story 3.2) — no training loop, no torch tensors, no progress bar
- debug hooks (Story 3.3)
- safetensors checkpoint save/load (Story 3.4)
- `visualize()` / triptych GIF (Story 3.5)
- `export()` / share panel (Story 3.6)

Implement `fit()`, `visualize()`, `export()` as stubs with `raise NotImplementedError(...)`. This is the correct pattern — do NOT pre-implement anything belonging to later stories.

### Files Being Modified — Current State

**`src/physlink/core/adapter.py`** (UPDATE — currently a 2-line stub):
```python
"""Abstract base adapter interface for PhysLink.
Concrete implementations in Story 3.1 (DreamerV3Adapter).
"""
from __future__ import annotations
```
Story 3.1 turns this into a real abstract base class.

**`src/physlink/adapters/dreamer.py`** (UPDATE — currently a 3-line stub):
```python
"""DreamerV3 adapter for PhysLink.
Implementation in Story 3.1 (DreamerV3Adapter).
"""
```
Story 3.1 fills this with the real `DreamerV3Adapter` implementation.

**`src/physlink/__init__.py`** (UPDATE — currently 4 symbols):
```python
__all__ = ["ActionSpace", "ObservationSpace", "PhysLinkError", "doctor",
           # Story 3.1: DreamerV3Adapter
           # Story 4.3/4.4: register_invariant, ComplianceReport
          ]
```
Story 3.1 adds `DreamerV3Adapter` to reach 5 symbols.

**`tests/integration/test_api_stability.py`** (UPDATE — Epic 2 test uses `==`):
Currently `test_epic2_api_symbols` asserts exact set equality (`== {4 symbols}`).
Adding a 5th symbol BREAKS this test. Change `==` to `.issubset()` first.

### `src/physlink/core/adapter.py` — Exact Target State

```python
"""Abstract base adapter interface for PhysLink."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from physlink.core._types import TrajectoryBatch
from physlink.core.spaces import ActionSpace, ObservationSpace


class BaseAdapter(ABC):
    """Abstract base class for all PhysLink adapters.

    Concrete subclasses implement fit(), visualize(), and export() for
    specific ML backends. Construction validates space compatibility only —
    no model loading or backend imports at init time.

    Args:
        obs_space: Validated ObservationSpace from Epic 2.
        act_space: Validated ActionSpace from Epic 2.

    Example:
        >>> # Do not instantiate BaseAdapter directly — use DreamerV3Adapter
        >>> from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
        >>> obs = ObservationSpace.from_proprioception(joints=7)
        >>> act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        >>> adapter = DreamerV3Adapter(obs, act)
    """

    def __init__(self, obs_space: ObservationSpace, act_space: ActionSpace) -> None:
        self.obs_space = obs_space
        self.act_space = act_space

    @abstractmethod
    def fit(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
        steps: int,
        checkpoint_interval_steps: int = 1000,
    ) -> None:
        """Run the adaptation loop. Implemented in Story 3.2."""

    @abstractmethod
    def visualize(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
    ) -> None:
        """Produce triptych GIF. Implemented in Story 3.5."""

    @abstractmethod
    def export(self, path: str) -> None:
        """Export artifact bundle. Implemented in Story 3.6."""

    @abstractmethod
    def explain(self) -> dict[str, Any]:
        """Return metadata dict describing adapter configuration."""
```

> **Why `fit()` return type is `None` here:** `AdaptationRun` (the proper return type from architecture doc) is Story 4.1. Using `None` keeps the abstract signature valid now; Story 4.1 will update the type annotation once `AdaptationRun` exists.

### `src/physlink/adapters/dreamer.py` — Exact Target State

```python
"""DreamerV3 adapter for PhysLink."""

from typing import Any

from physlink.core._types import TrajectoryBatch
from physlink.core.adapter import BaseAdapter
from physlink.core.exceptions import ConfigurationError
from physlink.core.spaces import ActionSpace, ObservationSpace

MIN_OBS_DIMS: int = 4   # DreamerV3 requires >= 4 observation dimensions
MIN_ACT_DIMS: int = 1   # at least 1 action dimension required


class DreamerV3Adapter(BaseAdapter):
    """DreamerV3 adapter for physical simulation reinforcement learning.

    Validates space compatibility at construction time. Training, visualization,
    and export are deferred to fit() / visualize() / export() respectively.
    No model weights are loaded and no GPU is required at construction.

    Args:
        obs_space: Observation space with dims >= 4.
        act_space: Action space with dims >= 1.

    Raises:
        ConfigurationError: If obs_space.dims < 4 or act_space.dims < 1.

    Example:
        >>> from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
        >>> obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        >>> act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        >>> adapter = DreamerV3Adapter(obs, act)
        >>> adapter.obs_space.dims
        14
    """

    def __init__(self, obs_space: ObservationSpace, act_space: ActionSpace) -> None:
        if obs_space.dims < MIN_OBS_DIMS:
            raise ConfigurationError(
                f"DreamerV3Adapter: incompatible obs_space.\n"
                f"  Got:      obs_space.dims={obs_space.dims}\n"
                f"  Expected: obs_space.dims >= {MIN_OBS_DIMS} (DreamerV3 minimum)\n"
                f"  Fix:      construct ObservationSpace with joints >= {MIN_OBS_DIMS}, "
                f"or use include_velocity=True to double the dimension count."
            )
        if act_space.dims < MIN_ACT_DIMS:
            raise ConfigurationError(
                f"DreamerV3Adapter: incompatible act_space.\n"
                f"  Got:      act_space.dims={act_space.dims}\n"
                f"  Expected: act_space.dims >= {MIN_ACT_DIMS}\n"
                f"  Fix:      construct ActionSpace with dims >= 1."
            )
        super().__init__(obs_space, act_space)

    def explain(self) -> dict[str, Any]:
        """Return a metadata dict describing this adapter's space configuration.

        Returns:
            A JSON-serializable dict with keys: type, obs_space, act_space.

        Example:
            >>> adapter = DreamerV3Adapter(obs, act)
            >>> info = adapter.explain()
            >>> info["type"]
            'DreamerV3Adapter'
        """
        return {
            "type": "DreamerV3Adapter",
            "obs_space": self.obs_space.explain(),
            "act_space": self.act_space.explain(),
        }

    def fit(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
        steps: int,
        checkpoint_interval_steps: int = 1000,
    ) -> None:
        """Run the DreamerV3 adaptation loop. Implemented in Story 3.2.

        Args:
            trajectories: Trajectory dataset (list of dicts or TrajectoryBatch).
            steps: Total adaptation steps to run.
            checkpoint_interval_steps: Steps between checkpoint saves.

        Raises:
            NotImplementedError: Always — implemented in Story 3.2.
        """
        raise NotImplementedError("fit() is implemented in Story 3.2.")

    def visualize(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
    ) -> None:
        """Produce triptych GIF. Implemented in Story 3.5.

        Args:
            trajectories: Trajectory dataset to visualize.

        Raises:
            NotImplementedError: Always — implemented in Story 3.5.
        """
        raise NotImplementedError("visualize() is implemented in Story 3.5.")

    def export(self, path: str) -> None:
        """Export artifact bundle. Implemented in Story 3.6.

        Args:
            path: Directory path for the exported artifacts.

        Raises:
            NotImplementedError: Always — implemented in Story 3.6.
        """
        raise NotImplementedError("export() is implemented in Story 3.6.")

    def __repr__(self) -> str:
        return (
            f"DreamerV3Adapter("
            f"obs_dims={self.obs_space.dims}, "
            f"act_dims={self.act_space.dims})"
        )
```

> **No torch import:** Construction is pure Python validation. `fit()` is a stub that raises `NotImplementedError`. Defer `import torch` to Story 3.2 where actual training is implemented. This ensures `import physlink` succeeds without PyTorch installed (same requirement as `doctor()`).

### `src/physlink/__init__.py` — Exact Target State

```python
"""PhysLink — backend-agnostic adapter library for physical simulation ML."""

__version__ = "0.1.0"

from physlink.adapters.dreamer import DreamerV3Adapter  # Story 3.1
from physlink.core.exceptions import PhysLinkError
from physlink.core.spaces import ActionSpace, ObservationSpace  # Story 2.6
from physlink.utils.diagnostics import doctor

__all__ = [
    "ActionSpace",
    "DreamerV3Adapter",     # Story 3.1
    "ObservationSpace",
    "PhysLinkError",
    "doctor",
    # Story 4.3/4.4: register_invariant, ComplianceReport
]
```

**CRITICAL: `__all__` must remain isort-sorted.** `TestPackageMetadata.test_all_is_sorted()` asserts `physlink.__all__ == sorted(physlink.__all__)`. The 5-symbol alphabetical order is: `ActionSpace`, `DreamerV3Adapter`, `ObservationSpace`, `PhysLinkError`, `doctor`.

### `tests/integration/test_api_stability.py` — Required Changes

**Change 1: Fix `test_epic2_api_symbols` (CRITICAL — this test breaks immediately when DreamerV3Adapter is added):**

```python
# BEFORE (current — fails with 5 symbols):
assert expected == actual, ...

# AFTER (change to issubset):
assert expected.issubset(actual), (
    f"Epic 2 API surface regression.\n"
    f"  Missing: {expected - actual}\n"
    f"  Got:     {sorted(actual)}\n"
    f"  Fix:     restore missing symbols to physlink.__all__"
)
```

**Change 2: Add `test_epic3_api_symbols()` after the existing Epic 2 test:**

```python
def test_epic3_api_symbols() -> None:
    """Story 3.1: DreamerV3Adapter added to public API."""
    import physlink
    from physlink import DreamerV3Adapter  # noqa: F401 — import test

    expected = {"doctor", "ObservationSpace", "ActionSpace", "PhysLinkError", "DreamerV3Adapter"}
    actual = set(physlink.__all__)
    assert expected.issubset(actual), (
        f"Epic 3 API surface mismatch.\n"
        f"  Missing: {expected - actual}\n"
        f"  Got:     {sorted(actual)}\n"
        f"  Fix:     add missing symbols to physlink.__all__ in src/physlink/__init__.py"
    )
```

> **Why `issubset` instead of `==` for Epic 3?** Epic 4 (Story 4.5) will add `register_invariant` and `ComplianceReport`. Using `issubset` here prevents the Epic 3 test from breaking at that time.

**Change 3: Update deprecation protocol comment:**

```python
# DEPRECATION PROTOCOL (NFR-11):
# ...existing text...
# Epic 4 (Story 4.5) will update to assert the full 7-symbol set.
```

**Change 4: Add to `TestTopLevelNamespaceAccess`:**

```python
def test_dreamer_v3_adapter_accessible_via_physlink(self) -> None:
    import physlink
    assert hasattr(physlink, "DreamerV3Adapter")

def test_dreamer_v3_adapter_is_callable(self) -> None:
    import physlink
    assert callable(physlink.DreamerV3Adapter)

def test_dreamer_v3_adapter_same_object_as_adapters_module(self) -> None:
    from physlink import DreamerV3Adapter
    from physlink.adapters.dreamer import DreamerV3Adapter as AdaptersDreamer
    assert DreamerV3Adapter is AdaptersDreamer
```

### `tests/unit/adapters/test_dreamer_cpu.py` — Implementation Pattern

Follow the established class-based pattern from Epic 2 tests. Key test classes to create:
- `TestDreamerV3AdapterConstruction` — happy path and error cases
- `TestDreamerV3AdapterExplain` — explain() output contract
- `TestDreamerV3AdapterStubs` — fit/visualize/export raise NotImplementedError
- `TestDreamerV3AdapterIdempotence` — NFR-09 cell re-run safety

Each test must annotate `-> None` (mypy --strict). Use the `synthetic_trajectories` fixture from `tests/conftest.py` if needed, but construction tests don't require trajectory data.

**No `@pytest.mark.gpu`** — all tests are CPU-only at construction stage. Mark GPU tests only when implementing `fit()` in Story 3.2.

### Architecture Compliance Checklist

- `core/adapter.py` has NO torch/jax imports → `test_core_no_torch_import.py` passes
- `adapters/dreamer.py` has NO torch import at module level → import succeeds without PyTorch
- `adapters/` imports from `core/` → allowed (boundary is core/ → adapters/, not the reverse)
- `core/adapter.py` imports from `core/spaces.py` and `core/_types.py` → intra-core, allowed
- `DreamerV3Adapter` public signatures use only `ObservationSpace`, `ActionSpace`, `list[dict]`, `TrajectoryBatch` → no backend primitives
- Error messages follow Got/Expected/Fix template → `ConfigurationError` message structure
- `__all__` isort-sorted → `test_all_is_sorted()` passes
- `from __future__ import annotations` in `adapter.py` (core/) → AR-11
- Google-style docstrings on all public methods → `test_docstring_completeness.py` AST check will cover `core/adapter.py` automatically

### Docstring Pitfalls (from Epic 2 retrospective)

- **mkdocs_autorefs trap:** Do NOT write docstring Examples using `result["key"][integer]` subscript (e.g., `info["obs_space"][0]`). Use `info["type"]` (string key) or `len(info["obs_space"])` instead.
- **mypy --strict ANN204:** Every special method (`__init__`, `__repr__`, `__len__`, `__iter__`) requires explicit return type annotation. `__init__` → `-> None`, `__repr__` → `-> str`.

### Pre-condition Note — `YOUR-ORG` Blocker

Epic 2 retrospective flags `YOUR-ORG` in `README.md`, `mkdocs.yml`, `ci.yml`, `publish.yml`, and `notebooks/quickstart.ipynb` as a CRITICAL unresolved debt item (D-1) that is two epics overdue. Story 3.1 does not depend on it, but Story 3.6 (Export and Share Panel — Colab URL behavior) will need a real git remote. This is noted here for awareness; it does not block Story 3.1 delivery.

### Project Structure Notes

- `src/physlink/core/adapter.py` — UPDATE (currently stub, becomes real ABC)
- `src/physlink/adapters/dreamer.py` — UPDATE (currently stub, becomes full implementation)
- `src/physlink/__init__.py` — UPDATE (4 → 5 symbols)
- `tests/integration/test_api_stability.py` — UPDATE (epic2 test + epic3 test)
- `tests/unit/adapters/test_dreamer_cpu.py` — NEW

No new directories needed. `tests/unit/adapters/` already exists (verified).

### References

- [Source: epics.md#Story 3.1] — Acceptance Criteria and scope
- [Source: architecture.md#Category 2] — Exception hierarchy and Got/Expected/Fix pattern; ConfigurationError example with `obs_dims >= 4`
- [Source: architecture.md#Category 3] — `from physlink.adapters.dreamer import DreamerV3Adapter` import pattern; 7-symbol target
- [Source: architecture.md#Structure Patterns] — `src/physlink/adapters/dreamer.py` file location; `tests/unit/adapters/test_dreamer_cpu.py` test location
- [Source: architecture.md#Type Annotation Patterns] — `X | Y` syntax, `from __future__ import annotations`, no `torch.Tensor` in public signatures
- [Source: architecture.md#Testing Patterns] — `@pytest.mark.gpu` rule; `tests/conftest.py` single conftest rule
- [Source: implementation-artifacts/2-6-google-style-docstrings.md#Dev Notes] — `test_api_stability.py` exact `==` vs `issubset` note; Story 3.1 comment to activate
- [Source: epic-2-retro-2026-05-22.md#Challenges] — mkdocs_autorefs integer-subscript trap; mypy ANN204 special methods rule; File List + Change Log closing checklist requirement (Action Item P-1)
- [Source: epic-2-retro-2026-05-22.md#Key Insights] — `test_docstring_completeness.py` AST auto-extensibility; YOUR-ORG critical debt

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blocking issues encountered. Implementation matched the exact target state specified in Dev Notes.

### Completion Notes List

- Task 1: `BaseAdapter` ABC implemented in `src/physlink/core/adapter.py` with all abstract methods (`fit`, `visualize`, `export`, `explain`), Google-style docstrings, `from __future__ import annotations`, no torch/jax imports. mypy --strict passes on core/.
- Task 2: `DreamerV3Adapter` implemented in `src/physlink/adapters/dreamer.py`. Validates `obs_space.dims >= 4` and `act_space.dims >= 1` with Got/Expected/Fix `ConfigurationError` messages. `fit()`, `visualize()`, `export()` are stubs raising `NotImplementedError`. No torch at module level. `__repr__` annotated `-> str`.
- Task 3: `src/physlink/__init__.py` updated from 4 to 5 symbols. `DreamerV3Adapter` added, `__all__` remains isort-sorted (`ActionSpace`, `DreamerV3Adapter`, `ObservationSpace`, `PhysLinkError`, `doctor`). `test_all_is_sorted()` passes.
- Task 4: `test_api_stability.py` updated — `test_epic2_api_symbols` now uses `.issubset()`, `test_epic3_api_symbols()` added with issubset check for 5 symbols, deprecation comment updated, 3 new `TestTopLevelNamespaceAccess` methods for `DreamerV3Adapter`.
- Task 5: `tests/unit/adapters/test_dreamer_cpu.py` created with 5 test classes (Construction, Idempotence, Explain, Stubs, Repr, ImportNoBytorchDependency) covering all ACs — 32 CPU-only tests, no `@pytest.mark.gpu`.
- Task 6: 432 passed, 3 skipped — zero regressions. mypy --strict clean on core/ and adapters/. ruff clean. mkdocs --strict build succeeds.

### File List

- `src/physlink/core/adapter.py` — updated (stub → real `BaseAdapter` ABC)
- `src/physlink/adapters/dreamer.py` — updated (stub → full `DreamerV3Adapter` implementation)
- `src/physlink/__init__.py` — updated (4 → 5 public symbols, `DreamerV3Adapter` added)
- `tests/integration/test_api_stability.py` — updated (`test_epic2_api_symbols` issubset fix, `test_epic3_api_symbols` added, 3 namespace access tests added)
- `tests/unit/adapters/test_dreamer_cpu.py` — new (32 CPU-only tests for Story 3.1 ACs)
- `docs/api/index.md` — updated (added direct-import note; renamed Space Configuration section)

## Senior Developer Review (AI)

**Reviewer:** AI (claude-sonnet-4-6) — 2026-05-22  
**Outcome:** Approved — 0 CRITICAL, 0 HIGH issues. 2 MEDIUM + 1 LOW fixed automatically.

**Fixes applied:**
- [M-1] Added `docs/api/index.md` to File List (was modified by dev agent but omitted from record)
- [M-2] Corrected test count: 25 → 32 unit tests; 422 passed/2 skipped → 432 passed/3 skipped (dev agent undercounted)
- [L-1] Added `TestDreamerV3AdapterRepr` to Task 5 checklist (5th test class was missing from spec)

**Verified:** All ACs implemented. mypy --strict clean on core/ and adapters/dreamer.py. ruff clean. mkdocs --strict builds. 432 tests pass, 0 regressions.

## Change Log

- 2026-05-22: Story 3.1 implemented — `BaseAdapter` ABC and `DreamerV3Adapter` constructed; `DreamerV3Adapter` exported as 5th public symbol; API stability tests updated for Epic 3; 32 new unit tests added; 432 tests pass.
- 2026-05-22: Code review complete — 2 MEDIUM + 1 LOW issues auto-fixed (File List completed, test counts corrected, Task 5 spec updated). Status → done.
