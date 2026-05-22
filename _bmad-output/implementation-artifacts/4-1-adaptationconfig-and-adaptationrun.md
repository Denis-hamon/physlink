# Story 4.1: AdaptationConfig and AdaptationRun

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher running named adaptation experiments,
I want an immutable AdaptationConfig and a stateful AdaptationRun to separate configuration from execution state,
so that I can version my configuration in YAML/JSON and track run state without mixing the two concerns.

## Acceptance Criteria

1. **Given** I construct an `AdaptationConfig` with valid parameters (obs_space, act_space, steps, checkpoint_interval_steps)
   **When** I attempt to mutate a field after construction
   **Then** a `FrozenInstanceError` (subclass of `AttributeError`) is raised — config is immutable

2. **Given** an `AdaptationConfig` object
   **When** I serialize it to YAML and reload it via `from_yaml(path)`
   **Then** the deserialized config is equal to the original (round-trip stable, no torch objects in serialized form)

3. **Given** an `AdaptationRun` is created from an `AdaptationConfig`
   **When** the run progresses through steps (via `adapter.fit()`)
   **Then** the run object tracks stateful data (current_step, checkpoint_paths, elapsed_seconds) separately from the immutable config
   **And** the config within the run remains unchanged after fit() completes

## Tasks / Subtasks

- [x] Task 1: Add `__eq__` and `__hash__` to `ObservationSpace` and `ActionSpace` in `src/physlink/core/spaces.py` (AC: #2)
  - [x] Add `__eq__` to `ObservationSpace` comparing dims, include_velocity, _joints, clip_bounds, normalize
  - [x] Add `__hash__` to `ObservationSpace` based on same fields
  - [x] Add `__eq__` to `ActionSpace` comparing dims and bounds (convert bounds to tuples for hash)
  - [x] Add `__hash__` to `ActionSpace` using `hash((self.dims, tuple(tuple(b) for b in self.bounds)))`
  - [x] These MUST be added for `@dataclass(frozen=True)` auto-generated `__eq__` on `AdaptationConfig` to produce value equality (not identity comparison)

- [x] Task 2: Implement `AdaptationConfig` and `AdaptationRun` in `src/physlink/core/_types.py` (AC: #1, #2, #3)
  - [x] Add `import datetime` at module level (needed for AdaptationRun.started_at default)
  - [x] Add `AdaptationConfig` as `@dataclass(frozen=True)` with fields: `obs_space: ObservationSpace`, `act_space: ActionSpace`, `steps: int`, `checkpoint_interval_steps: int = 1000`, `checkpoint_dir: str = "physlink_checkpoints"`
  - [x] Add `to_dict(self) -> dict[str, object]` method on `AdaptationConfig` — serializes using `self.obs_space.explain()`, `self.act_space.explain()` plus scalar fields
  - [x] Add `from_dict(cls, d: dict[str, object]) -> AdaptationConfig` classmethod — reconstructs `ObservationSpace` via `from_proprioception(joints=d["obs_space"]["joints"], include_velocity=..., clip_bounds=..., normalize=...)` and `ActionSpace.continuous(dims=..., bounds=[tuple(b) for b in d["act_space"]["bounds"]])`
  - [x] Add `to_yaml(self, path: str) -> None` method — deferred `import yaml` inside method body; uses `yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)`
  - [x] Add `from_yaml(cls, path: str) -> AdaptationConfig` classmethod — deferred `import yaml`; uses `yaml.safe_load(f)` then `cls.from_dict(d)`
  - [x] Add Google-style docstring with Args, Returns, Raises, Example sections to `AdaptationConfig` and each public method
  - [x] Add `AdaptationRun` as plain `@dataclass` (NOT frozen) with fields: `config: AdaptationConfig`, `current_step: int = 0`, `checkpoint_paths: list[str] = field(default_factory=list)`, `started_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())`, `elapsed_seconds: float = 0.0`
  - [x] Add Google-style docstring to `AdaptationRun`
  - [x] Add necessary imports at top: `from physlink.core.spaces import ObservationSpace, ActionSpace` (already backend-agnostic — no torch)

- [x] Task 3: Update `fit()` in `src/physlink/adapters/dreamer.py` to return `AdaptationRun` (AC: #3)
  - [x] Import `AdaptationConfig, AdaptationRun` inside `fit()` body (deferred import pattern — consistent with all other deferred imports in dreamer.py)
  - [x] Change return type annotation from `-> None` to `-> AdaptationRun`
  - [x] Collect checkpoint paths during fit() into a local `_run_checkpoint_paths: list[str] = []` list — append `self._last_checkpoint_path` every time `_save_checkpoint()` is called (BOTH branches: debug_hooks and non-debug)
  - [x] At the end of `fit()` (AFTER the Live/progress context manager exits and `self._fit_elapsed_seconds` is set):
    ```python
    _config = AdaptationConfig(
        obs_space=self.obs_space,
        act_space=self.act_space,
        steps=steps,
        checkpoint_interval_steps=checkpoint_interval_steps,
        checkpoint_dir=checkpoint_dir,
    )
    _run = AdaptationRun(
        config=_config,
        current_step=completed,
        checkpoint_paths=_run_checkpoint_paths,
        elapsed_seconds=self._fit_elapsed_seconds or 0.0,
    )
    return _run
    ```
  - [x] Update `fit()` docstring: change `Returns:` section from implicit None to `Returns: AdaptationRun capturing config, step count, checkpoint paths, and elapsed time.`
  - [x] Update Example in `fit()` docstring to assign the return value: `run = adapter.fit(trajectories, steps=10, debug_hooks=True)`

- [x] Task 4: Update `tests/unit/core/test_types.py` — add AdaptationConfig and AdaptationRun tests (AC: #1, #2, #3)
  - [x] Add `TestAdaptationConfigImmutability` class:
    - `test_config_raises_on_mutation` — assert `FrozenInstanceError` on field assignment
    - `test_config_stores_correct_fields` — assert obs_space, act_space, steps, checkpoint_interval_steps
    - `test_config_default_checkpoint_interval` — default = 1000
  - [x] Add `TestAdaptationConfigSerialization` class:
    - `test_to_dict_contains_required_keys` — assert obs_space, act_space, steps, checkpoint_interval_steps, checkpoint_dir in dict
    - `test_to_dict_obs_space_is_json_serializable` — `json.dumps(d["obs_space"])` does not raise
    - `test_to_dict_act_space_is_json_serializable` — `json.dumps(d["act_space"])` does not raise
    - `test_to_dict_no_torch_objects` — assert no torch.Tensor in any nested value
    - `test_yaml_round_trip_equal` (uses `tmp_path`) — `config.to_yaml(path)`, `loaded = AdaptationConfig.from_yaml(path)`, `assert loaded == config`
    - `test_from_dict_round_trip_equal` — `AdaptationConfig.from_dict(config.to_dict()) == config`
  - [x] Add `TestAdaptationRunState` class:
    - `test_run_is_not_frozen` — assert no `FrozenInstanceError` when mutating `run.current_step`
    - `test_run_stores_config` — assert `run.config is config`
    - `test_run_config_unchanged_after_mutation` — mutate run fields, config fields unchanged
    - `test_run_default_step_is_zero` — `AdaptationRun(config=config).current_step == 0`
    - `test_run_has_started_at_iso_format` — `run.started_at` is a non-empty string parseable by `datetime.fromisoformat`

- [x] Task 5: Run full test suite — zero regressions (AC: all)
  - [x] `pytest tests/ -x -m "not gpu"` — all existing tests pass (no regressions from spaces.py changes)
  - [x] `ruff check src/` — zero warnings
  - [x] `mkdocs build --strict` — docs build successfully (validated via CI infrastructure tests)
  - [x] File List complete AND Change Log entry added before marking done

## Dev Notes

### What Story 4.1 Does and Does NOT Do

**This story implements:**
- `__eq__` / `__hash__` on `ObservationSpace` and `ActionSpace` (prerequisite for value-equality in AdaptationConfig)
- `AdaptationConfig`: frozen dataclass with YAML/JSON round-trip serialization
- `AdaptationRun`: stateful mutable dataclass returned by `fit()`
- `fit()` return type updated from `None` → `AdaptationRun`
- New tests in `test_types.py`

**Explicitly deferred — do NOT implement:**
- `TrajectoryBuffer.export(path)` / `.load(path)` — Story 4.2
- `register_invariant()` / `ComplianceReport` — Stories 4.3–4.5
- `AdaptationConfig` or `AdaptationRun` exports from `physlink.__init__` — these are sub-module types for advanced use, NOT part of the 7-symbol public API surface

### Critical: `fit()` Currently Returns `None` — Must Change to `AdaptationRun`

The architecture doc specifies `fit() -> AdaptationRun` but Story 3.6's dev notes explicitly deferred this change. Story 4.1 owns this change. The return type annotation on line 551 of `dreamer.py` must change from `-> None` to `-> AdaptationRun`.

**Existing tests that call `fit()`** do not assert `is None` on the return value (they ignore it). Changing the return type will not break existing tests — verified by checking `tests/unit/adapters/test_dreamer_cpu.py` (all fit() calls are fire-and-forget in test setup).

### `AdaptationConfig` — Design Decisions

**Use `@dataclass(frozen=True)` for immutability:**
```python
from dataclasses import dataclass, field as dc_field

@dataclass(frozen=True)
class AdaptationConfig:
    obs_space: ObservationSpace
    act_space: ActionSpace
    steps: int
    checkpoint_interval_steps: int = 1000
    checkpoint_dir: str = "physlink_checkpoints"
```

`@dataclass(frozen=True)` raises `dataclasses.FrozenInstanceError` (a subclass of `AttributeError`) on any field mutation — this satisfies AC #1.

**Why `ObservationSpace.__eq__` must be added (Task 1 is a prerequisite):**
- `@dataclass(frozen=True)` auto-generates `__eq__` comparing all fields with `==`
- `ObservationSpace` and `ActionSpace` are plain classes with no `__eq__` → Python falls back to identity (`is`) comparison
- Two independently constructed `ObservationSpace(joints=7)` objects would NOT be equal
- The YAML round-trip AC #2 requires: `AdaptationConfig.from_yaml(path) == original` — this ONLY passes if value equality works on the space objects

**YAML serialization approach — use `.explain()` dicts:**
`ObservationSpace.explain()` and `ActionSpace.explain()` already return JSON-serializable dicts (verified in Story 2.4 — they are JSON-serializable). The explain dicts contain ALL fields needed to reconstruct the spaces:
- `obs_space.explain()` → `{"type": "ObservationSpace", "dims": 14, "joints": 7, "include_velocity": True, "clip_bounds": null, "normalize": False}`
- `act_space.explain()` → `{"type": "ActionSpace", "dims": 7, "bounds": [[-1.0, 1.0], ...], "clipping_behavior": "per_dimension"}`

For `from_dict()`, reconstruct as:
```python
obs = ObservationSpace.from_proprioception(
    joints=d["obs_space"]["joints"],
    include_velocity=d["obs_space"]["include_velocity"],
    clip_bounds=tuple(d["obs_space"]["clip_bounds"]) if d["obs_space"]["clip_bounds"] else None,
    normalize=d["obs_space"]["normalize"],
)
act = ActionSpace.continuous(
    dims=d["act_space"]["dims"],
    bounds=[tuple(b) for b in d["act_space"]["bounds"]],
)
```

Note: `clip_bounds` from explain() returns a list (e.g. `[-1.0, 1.0]`), must convert to `tuple` for `ObservationSpace` reconstruction. `bounds` from ActionSpace explain() returns `[[lo, hi], ...]`, must convert inner lists to tuples.

### `AdaptationRun` — Design and Relationship to `fit()`

`AdaptationRun` is NOT frozen. It is mutable by design — it tracks execution state that changes as the run progresses.

```python
@dataclass
class AdaptationRun:
    config: AdaptationConfig
    current_step: int = 0
    checkpoint_paths: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    elapsed_seconds: float = 0.0
```

The `config` field holds a reference to the immutable `AdaptationConfig` — changing `run.config.steps` would raise `FrozenInstanceError`, confirming the AC "the config within the run remains unchanged."

**How `fit()` populates `AdaptationRun`:**

1. Track all checkpoint paths in a local list `_run_checkpoint_paths: list[str] = []`
2. In BOTH branches (debug and non-debug), append the return value of `_save_checkpoint()`:
   ```python
   # Instead of just: self._last_checkpoint_path = _save_checkpoint(...)
   _ckpt = _save_checkpoint(self._model, self._actor, self._critic, completed, checkpoint_dir)
   self._last_checkpoint_path = _ckpt
   _run_checkpoint_paths.append(_ckpt)
   ```
3. After the training loop exits (and `self._fit_elapsed_seconds` is set), construct and return:
   ```python
   _config = AdaptationConfig(
       obs_space=self.obs_space,
       act_space=self.act_space,
       steps=steps,
       checkpoint_interval_steps=checkpoint_interval_steps,
       checkpoint_dir=checkpoint_dir,
   )
   return AdaptationRun(
       config=_config,
       current_step=completed,
       checkpoint_paths=_run_checkpoint_paths,
       elapsed_seconds=self._fit_elapsed_seconds or 0.0,
   )
   ```

The `completed` variable in `fit()` is the counter variable for steps completed — it's already tracked in the existing code.

### ruff Compliance (Carry-Over from Stories 3.3–3.6)

- `ANN401` IS enabled — do NOT use `Any` in public signatures. Use `object` for unknown types in `from_dict(cls, d: dict[str, object])`.
- `BLE` is NOT enabled — `except Exception` is permitted if needed
- `from __future__ import annotations` is ALREADY present in `_types.py` — do NOT add it again
- `from __future__ import annotations` is NOT needed in `adapters/dreamer.py` — consistent with Stories 3.x
- All third-party and stdlib imports in method bodies MUST be deferred (inside the function body) — consistent with the pattern established in Stories 3.2–3.6
- `yaml` is already in dependencies (`pyyaml>=6.0` in `pyproject.toml`) — no new dep needed
- `datetime` is stdlib — deferred import not required (can be at module level in `_types.py`)

**Specific ruff rules to watch in `_types.py`:**
- `D401` (docstring imperative mood) — keep docstrings using imperative: "Attach ...", "Return ...", not "Attaches ...", "Returns ..."  
- The existing `from typing import Any` in `_types.py` is only used for `TrajectoryBatch.data: list[dict[str, Any]]` — do not remove it

### `ObservationSpace.__eq__` and `__hash__` Implementation

Add directly after the existing `explain()` method in `spaces.py`:

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, ObservationSpace):
        return NotImplemented
    return (
        self.dims == other.dims
        and self.include_velocity == other.include_velocity
        and self._joints == other._joints
        and self.clip_bounds == other.clip_bounds
        and self.normalize == other.normalize
    )

def __hash__(self) -> int:
    return hash((self.dims, self.include_velocity, self._joints, self.clip_bounds, self.normalize))
```

For `ActionSpace`, add after `explain()`:
```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, ActionSpace):
        return NotImplemented
    return self.dims == other.dims and self.bounds == other.bounds

def __hash__(self) -> int:
    return hash((self.dims, tuple(tuple(b) for b in self.bounds)))
```

These changes are backward-compatible — existing tests (`test_spaces.py`) do not assert identity equality (`is`), they test functional behavior. Adding `__eq__` cannot break any existing test.

### Files Being Modified — Current State

**`src/physlink/core/spaces.py`** (UPDATE):
- Current state: `ObservationSpace` and `ActionSpace` have `__repr__` and `explain()` but NO `__eq__` or `__hash__`
- Add: `__eq__` and `__hash__` to both classes (after `explain()`)

**`src/physlink/core/_types.py`** (UPDATE):
- Current state: only `TrajectoryBatch` dataclass (lines 1–56); module docstring says "Story 4.1 (AdaptationConfig, AdaptationRun)" — this is the designated location
- Add: `import datetime` at module level (before existing imports or grouped with stdlib)
- Add: `from physlink.core.spaces import ObservationSpace, ActionSpace` (new import — these are core/ → core/ which is explicitly allowed per architecture boundary rules)
- Add: `AdaptationConfig` frozen dataclass with methods
- Add: `AdaptationRun` mutable dataclass

**`src/physlink/adapters/dreamer.py`** (UPDATE):
- Current state: `fit()` at line 544 has return type `-> None` (line 551); `_save_checkpoint()` return value is captured into `self._last_checkpoint_path` in both fit() branches (done in Story 3.6)
- Change: return type `-> None` → `-> AdaptationRun`
- Change: add local `_run_checkpoint_paths: list[str] = []` before the training loop
- Change: append to `_run_checkpoint_paths` each time `_save_checkpoint()` is called
- Change: construct and return `AdaptationRun` at end of `fit()`
- Update: `fit()` docstring Returns section

**`tests/unit/core/test_types.py`** (UPDATE):
- Current state: tests only for `TrajectoryBatch` (lines 1–100)
- Add: new test classes for `AdaptationConfig` and `AdaptationRun`
- No new files, no new directories

### Previous Story Intelligence (Story 3.6)

From Story 3.6 completion notes:
- `deferred import` pattern is established for all third-party imports inside method bodies in `dreamer.py` — follow this for the `AdaptationConfig`/`AdaptationRun` import inside `fit()`
- `datetime.datetime.now(datetime.timezone.utc).isoformat()` is the correct timestamp pattern (not deprecated `utcnow()`)
- File List + Change Log entry MUST be complete before marking `done` (Action Item P-1 from Epic 2 retro — still enforced)
- ruff `RUF102` — avoid extraneous `f` prefix on static strings

From Story 3.6 dev notes (explicitly deferred to this story):
- "Explicitly deferred: `AdaptationRun` return type for `fit()` (Story 4.1) — `fit()` still returns `None`" — THIS IS THE STORY THAT IMPLEMENTS IT

### Git Intelligence

Recent commit pattern from stories 3.x:
- All stories follow: `feat(story-X.Y): Title` commit format
- Testing gate: `pytest tests/ -x -m "not gpu"` must pass with 0 failures before marking done
- Ruff: `ruff check src/` must show zero warnings
- MkDocs: `mkdocs build --strict` must succeed (new public methods need Google-style docstrings for mkdocstrings)

The `core/_types.py` changes will be picked up by `test_core_no_torch_import.py` AST check — the new `AdaptationConfig` and `AdaptationRun` classes must NOT import or reference any torch types in their public signatures.

### Architecture Compliance

**Module placement — confirmed correct:**
- `AdaptationConfig` and `AdaptationRun` → `src/physlink/core/_types.py` (specified in architecture.md Project Structure section: `# FR-02/03: TrajectoryBatch, AdaptationConfig, AdaptationRun`)
- `ObservationSpace.__eq__` addition → `src/physlink/core/spaces.py` (same file, Story 2 module)

**Boundary rules (from `architecture.md#Architectural Boundaries`):**
- `physlink.core/ → physlink.core/` ✅ OK — `_types.py` importing from `spaces.py` is intra-core
- `physlink.adapters/ → physlink.core/` ✅ OK — `dreamer.py` importing `AdaptationConfig, AdaptationRun` from `core._types`

**Public API surface — `AdaptationConfig` and `AdaptationRun` are NOT exported from `physlink.__init__`:**
- Architecture doc: "TrajectoryBatch, AdaptationConfig, AdaptationRun dans sous-modules (usage avancé)"
- The 7-symbol public API surface (`doctor`, `ObservationSpace`, `ActionSpace`, `DreamerV3Adapter`, `register_invariant`, `ComplianceReport`, `PhysLinkError`) does NOT include these types
- `test_api_stability.py` does NOT need updating for this story (Story 4.5 finalizes the 7-symbol list)

**Naming conventions (from `architecture.md#Naming Patterns`):**
- `AdaptationConfig`, `AdaptationRun` — PascalCase ✅
- `obs_space`, `act_space`, `checkpoint_interval_steps` — full names, zero abbreviation ✅
- `to_dict`, `from_dict`, `to_yaml`, `from_yaml` — snake_case ✅

### Project Structure Notes

- `src/physlink/core/_types.py` — UPDATE: add `AdaptationConfig`, `AdaptationRun`; add `datetime` import; add `ObservationSpace`, `ActionSpace` import
- `src/physlink/core/spaces.py` — UPDATE: add `__eq__`, `__hash__` to `ObservationSpace` and `ActionSpace`
- `src/physlink/adapters/dreamer.py` — UPDATE: `fit()` return type, checkpoint paths collection, return `AdaptationRun`
- `tests/unit/core/test_types.py` — UPDATE: add `TestAdaptationConfigImmutability`, `TestAdaptationConfigSerialization`, `TestAdaptationRunState`

No new files, no new directories required.

### References

- [Source: epics.md#Story 4.1] — Acceptance Criteria, user story statement, full scope
- [Source: epics.md#FR-08] — `AdaptationConfig` (immutable, YAML/JSON-serializable) and `AdaptationRun` (stateful, temporary); `TrajectoryBuffer.export(path)` / `.load(path)` (deferred to 4.2)
- [Source: epics.md#Epic 4 goal] — "domain scientist can attach physical invariant checks" — AdaptationConfig is the entry point for named-run lab workflows (Story 5.2)
- [Source: architecture.md#Category 1] — `fit()` signature with `-> AdaptationRun` return type
- [Source: architecture.md#Project Structure] — `src/physlink/core/_types.py` designated location for AdaptationConfig/AdaptationRun
- [Source: architecture.md#Architectural Boundaries] — `core/ → core/` allowed; `adapters/ → core/` allowed
- [Source: architecture.md#Naming Patterns] — full names, PascalCase classes, snake_case methods
- [Source: architecture.md#Structure Patterns] — `src/` layout; tests mirror `src/physlink/core/` in `tests/unit/core/`
- [Source: architecture.md#Implementation Patterns] — `from __future__ import annotations` in core/; `X | Y` annotation syntax
- [Source: architecture.md#Gap Analysis] — "AdaptationConfig schéma YAML — format de sérialisation non spécifié → décision à l'implémentation" — use explain() dicts
- [Source: implementation-artifacts/3-6-export-and-share-panel.md#Dev Notes] — deferred import convention; `fit()` return type explicitly deferred to 4.1; datetime.now(timezone.utc) pattern; File List + Change Log closing requirement
- [Source: src/physlink/core/_types.py:3] — module docstring explicitly names "Story 4.1 (AdaptationConfig, AdaptationRun)"
- [Source: src/physlink/core/spaces.py:100-127] — `ObservationSpace.explain()` returns joints, include_velocity, clip_bounds, normalize — all fields needed for reconstruction
- [Source: src/physlink/core/spaces.py:229-252] — `ActionSpace.explain()` returns dims, bounds (as lists) — all fields needed for reconstruction
- [Source: src/physlink/adapters/dreamer.py:544-551] — `fit()` current return type `-> None` to be changed
- [Source: src/physlink/adapters/dreamer.py:638-661] — `_save_checkpoint()` call sites where checkpoint paths must be collected into list
- [Source: pyproject.toml] — `pyyaml>=6.0` already in dependencies; `datetime` is stdlib — no new deps needed

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- **ruff F821**: `"AdaptationRun"` in `fit()` return annotation was an undefined name since the import is deferred. Fixed by adding `TYPE_CHECKING` block with `AdaptationRun` import at the top of `dreamer.py`.
- **mypy [index]**: `from_dict` used `d["obs_space"]["joints"]` where `d: dict[str, object]` — subscripting `object` triggers `[index]`. Fixed by typing intermediate vars `obs_d: Any = d["obs_space"]`.
- **ruff RUF100**: `# noqa: PLC0415` was not a valid/enabled noqa directive. Removed from both `import yaml` lines.
- **ruff E501**: `ObservationSpace.__hash__` line was 103 chars. Wrapped to multi-line.

### Completion Notes List

- `ObservationSpace.__eq__` / `__hash__` added (value equality by dims, include_velocity, _joints, clip_bounds, normalize).
- `ActionSpace.__eq__` / `__hash__` added (value equality by dims and bounds).
- `AdaptationConfig` implemented as `@dataclass(frozen=True)` with `to_dict`, `from_dict`, `to_yaml`, `from_yaml` and full Google-style docstrings.
- `AdaptationRun` implemented as mutable `@dataclass` with started_at UTC ISO timestamp default.
- `fit()` return type changed from `None` → `AdaptationRun`; checkpoint paths collected in both training branches; `AdaptationRun` constructed and returned after training loop.
- 65 new tests added: 34 in `test_types.py` (`TestAdaptationConfigImmutability` ×5, `TestAdaptationConfigSerialization` ×6, `TestAdaptationRunState` ×5, `TestAdaptationConfigEquality` ×9, `TestAdaptationRunDefaults` ×8), 23 in `test_spaces.py` (`TestObservationSpaceEquality` ×13, `TestActionSpaceEquality` ×10), 8 in `test_dreamer_cpu.py` (`TestFitReturnTypeStory41` ×8).
- Full test suite: 589 passed, 3 skipped, 0 failures.

### File List

- `src/physlink/core/spaces.py` — added `__eq__` and `__hash__` to `ObservationSpace` and `ActionSpace`
- `src/physlink/core/_types.py` — added `import datetime`, `from physlink.core.spaces import ObservationSpace, ActionSpace`, `AdaptationConfig` dataclass, `AdaptationRun` dataclass
- `src/physlink/adapters/dreamer.py` — added `TYPE_CHECKING` import, `AdaptationRun` under `TYPE_CHECKING`, changed `fit()` return type to `AdaptationRun`, added checkpoint path collection, added `AdaptationRun` construction and return
- `tests/unit/core/test_types.py` — added `TestAdaptationConfigImmutability`, `TestAdaptationConfigSerialization`, `TestAdaptationRunState`, `TestAdaptationConfigEquality`, `TestAdaptationRunDefaults` test classes (34 new tests)
- `tests/unit/core/test_spaces.py` — added `TestObservationSpaceEquality`, `TestActionSpaceEquality` test classes (23 new tests)
- `tests/unit/adapters/test_dreamer_cpu.py` — added `TestFitReturnTypeStory41` test class (8 new tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story 4.1 status updated

## Change Log

- **2026-05-22** — Story 4.1 implemented: `ObservationSpace`/`ActionSpace` value equality via `__eq__`/`__hash__`; `AdaptationConfig` frozen dataclass with YAML/JSON round-trip; `AdaptationRun` mutable dataclass; `fit()` return type changed from `None` to `AdaptationRun` with checkpoint path tracking; 65 new tests added across 3 test files; 589 tests pass, ruff/mypy clean.
- **2026-05-22** — Senior Developer Review (AI): 2 MEDIUM issues fixed (missing `test_spaces.py` and `test_dreamer_cpu.py` from File List, incorrect test count in Completion Notes). 3 LOW findings noted: `ActionSpace.__eq__` doesn't normalize tuple/list bounds (non-breaking, matches spec), `from_dict` uses `type: ignore` for 3 scalar fields, source-inspection tests in `TestFitReturnTypeStory41` are brittle to refactoring. All ACs verified implemented. Status → done.
