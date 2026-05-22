# Story 4.2: TrajectoryBuffer Export and Load

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher managing trajectory datasets across Colab sessions,
I want TrajectoryBuffer.export(path) and .load(path) to persist my trajectory data reliably,
so that I can save a session's collected trajectories and reload them in a future Colab session without data loss.

## Acceptance Criteria

1. **Given** a `TrajectoryBuffer` populated with trajectory data
   **When** I call `TrajectoryBuffer.export(path="./trajectories.pkl")`
   **Then** a file is written at the specified path containing all trajectory data
   **And** the export does not modify the buffer's in-memory state

2. **Given** an exported `TrajectoryBuffer` file on disk
   **When** I call `TrajectoryBuffer.load(path="./trajectories.pkl")`
   **Then** the loaded buffer contains the same trajectories as the original (round-trip fidelity)
   **And** the loaded buffer is immediately usable as input to `adapter.fit()`

3. **Given** a `TrajectoryBuffer` export/load cycle is run in a fresh Colab cell
   **When** the cell is re-run
   **Then** the same result is produced without side effects (NFR-09)

## Tasks / Subtasks

- [x] Task 1: Implement `TrajectoryBuffer` in `src/physlink/core/_types.py` (AC: #1, #2, #3)
  - [x] Add `TrajectoryBuffer` as a `@dataclass` with field `data: list[dict[str, Any]] = field(default_factory=list)`
  - [x] Add `export(self, path: str) -> None` — deferred `import pickle` inside method; writes `self.data` via `pickle.dump(self.data, f)` without mutating `self.data`
  - [x] Add `load(cls, path: str) -> TrajectoryBuffer` as `@classmethod` — deferred `import pickle`; uses `pickle.load(f)` then `cls(data=data)`
  - [x] Add `to_batch(self) -> TrajectoryBatch` convenience method — returns `TrajectoryBatch.from_list(self.data)`
  - [x] Add `__len__`, `__iter__`, `__repr__` (mirrors `TrajectoryBatch` interface for usability)
  - [x] Add Google-style docstring with Args, Returns, Raises, Example sections on class and each public method
  - [x] Note: pickle is appropriate for `TrajectoryBuffer` (researcher's own trusted data); the no-pickle rule (AR-05) specifically applies to checkpoints only

- [x] Task 2: Update `fit()` and `visualize()` in `src/physlink/adapters/dreamer.py` to accept `TrajectoryBuffer` (AC: #2)
  - [x] Import `TrajectoryBuffer` at runtime at the top of the module alongside `TrajectoryBatch` import: `from physlink.core._types import TrajectoryBatch, TrajectoryBuffer`
  - [x] Update `fit()` type annotation: `trajectories: list[dict[str, Any]] | TrajectoryBatch | TrajectoryBuffer`
  - [x] In `fit()` body: add `if isinstance(trajectories, TrajectoryBuffer): trajectories = trajectories.to_batch()` BEFORE the existing `if isinstance(trajectories, list)` check
  - [x] Update `fit()` docstring Args line for `trajectories` to mention `TrajectoryBuffer` as a third accepted type
  - [x] Update `visualize()` type annotation similarly: `trajectories: list[dict[str, Any]] | TrajectoryBatch | TrajectoryBuffer`
  - [x] Add the same `if isinstance(trajectories, TrajectoryBuffer)` conversion in `visualize()` body
  - [x] Update `visualize()` docstring Args line similarly

- [x] Task 3: Add `TrajectoryBuffer` tests in `tests/unit/core/test_types.py` (AC: #1, #2, #3)
  - [x] Add `from physlink.core._types import ..., TrajectoryBuffer` to imports
  - [x] Add `TestTrajectoryBufferConstruction` class (10 tests: construction, repr, iter, to_batch, to_batch on empty buffer)
  - [x] Add `TestTrajectoryBufferExport` class (4 tests: creates file, no mutation, non-empty, empty buffer)
  - [x] Add `TestTrajectoryBufferLoad` class (8 tests: isinstance, single, multi, numpy, length, to_batch, FileNotFoundError, empty round-trip)
  - [x] Add `TestTrajectoryBufferIdempotence` class (2 tests: re-export overwrites, re-load equals)

- [x] Task 4: Add `TrajectoryBuffer` integration test in `tests/unit/adapters/test_dreamer_cpu.py` (AC: #2)
  - [x] Add `TestFitWithTrajectoryBufferStory42` class (7 tests: fit accepts buffer, produces AdaptationRun, export/load round-trip, module-level import check, validation-before-conversion guard, visualize error path, visualize source inspection)

- [x] Task 5: Run full test suite — zero regressions (AC: all)
  - [x] `pytest tests/ -x -m "not gpu"` — 615 passed, 3 skipped, 0 failures
  - [x] `ruff check src/` — zero warnings
  - [x] `mkdocs build --strict` — docs built successfully
  - [x] File List complete AND Change Log entry added before marking done

## Dev Notes

### What Story 4.2 Does and Does NOT Do

**This story implements:**
- `TrajectoryBuffer` dataclass with `export(path)`, `load(path)`, `to_batch()` methods
- `fit()` and `visualize()` updated to accept `TrajectoryBuffer` as a third input type
- New tests in `test_types.py` and `test_dreamer_cpu.py`

**Explicitly deferred — do NOT implement:**
- `register_invariant()` / `ComplianceReport` — Stories 4.3–4.5
- `TrajectoryBuffer.from_numpy()` — Story 2.1 deferred constructor (v0.2)
- Any changes to `physlink.__init__` public exports

### `TrajectoryBuffer` Design

`TrajectoryBuffer` is a separate, mutable buffer class distinct from `TrajectoryBatch`. While `TrajectoryBatch` is the canonical input to `fit()`, `TrajectoryBuffer` is the persistence wrapper that adds `export()`/`load()` to the data lifecycle.

```python
@dataclass
class TrajectoryBuffer:
    data: list[dict[str, Any]] = field(default_factory=list)

    def export(self, path: str) -> None:
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self.data, f)

    @classmethod
    def load(cls, path: str) -> TrajectoryBuffer:
        import pickle
        with open(path, "rb") as f:
            data = pickle.load(f)  # noqa: S301
        return cls(data=data)

    def to_batch(self) -> TrajectoryBatch:
        return TrajectoryBatch.from_list(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.data)

    def __repr__(self) -> str:
        return f"TrajectoryBuffer(n={len(self.data)})"
```

**Why pickle for TrajectoryBuffer:**
- AR-05 says "No pickle" for checkpoints (safetensors format). This rule does not apply to trajectory data.
- Trajectory data is a researcher's own trusted data — no deserialization attack surface concern.
- pickle handles arbitrary Python dicts including numpy arrays transparently.
- The spec explicitly shows `./trajectories.pkl` as the path format.
- The `# noqa: S301` suppresses the bandit pickle warning (expected in a library context).

### `fit()` and `visualize()` Type Extension

The conversion order in `fit()` must be:
```python
# Before the training loop, convert to TrajectoryBatch
if isinstance(trajectories, TrajectoryBuffer):
    trajectories = trajectories.to_batch()
if isinstance(trajectories, list):
    trajectories = TrajectoryBatch.from_list(trajectories)
# Now trajectories is always TrajectoryBatch
```

**Important**: The `TrajectoryBuffer` import at the top of `dreamer.py` must be a **runtime import** (not only under `TYPE_CHECKING`), since `isinstance()` check requires the actual class at runtime.

```python
# dreamer.py top-level import (line 7 area)
from physlink.core._types import TrajectoryBatch, TrajectoryBuffer
```

The `TYPE_CHECKING` block currently has `AdaptationRun` — the `TrajectoryBuffer` import is a runtime import, so it goes with `TrajectoryBatch`, not under `TYPE_CHECKING`.

### ruff Compliance (Carry-Over)

- `ANN401` IS enabled — avoid `Any` in public signatures
- `from __future__ import annotations` is already present in `_types.py`
- Deferred imports pattern: `import pickle` inside method bodies
- `S301` (bandit pickle warning): use `# noqa: S301` on `pickle.load()` call
- `D401` (docstring imperative mood) — "Export ...", "Load ...", "Convert ..."

### Files Being Modified — Current State

**`src/physlink/core/_types.py`** (UPDATE):
- Current state: `TrajectoryBatch`, `AdaptationConfig`, `AdaptationRun`
- Add: `TrajectoryBuffer` dataclass after `TrajectoryBatch`

**`src/physlink/adapters/dreamer.py`** (UPDATE):
- Current state: imports `TrajectoryBatch` from `core._types`; `fit()` accepts `list[dict] | TrajectoryBatch`
- Change: import `TrajectoryBuffer` alongside `TrajectoryBatch`
- Change: add `TrajectoryBuffer` to `fit()` and `visualize()` type annotations and conversion branches

**`tests/unit/core/test_types.py`** (UPDATE):
- Current state: tests for `TrajectoryBatch`, `AdaptationConfig`, `AdaptationRun`
- Add: `TestTrajectoryBufferConstruction`, `TestTrajectoryBufferExport`, `TestTrajectoryBufferLoad`, `TestTrajectoryBufferIdempotence`

**`tests/unit/adapters/test_dreamer_cpu.py`** (UPDATE):
- Current state: tests for `DreamerV3Adapter` including `TestFitReturnTypeStory41`
- Add: `TestFitWithTrajectoryBufferStory42`

### Previous Story Intelligence (Story 4.1)

From Story 4.1 completion notes:
- `deferred import` pattern established in `_types.py` for `yaml` — follow same pattern for `pickle`
- `from __future__ import annotations` is ALREADY present in `_types.py`
- File List + Change Log entry MUST be complete before marking done
- `ruff check src/` must show zero warnings before marking done

### Architecture Compliance

**Module placement:**
- `TrajectoryBuffer` → `src/physlink/core/_types.py` (same module as `TrajectoryBatch`, `AdaptationConfig`, `AdaptationRun`)
- Architecture doc lists `TrajectoryBuffer I/O dans utils/io.py` as a post-v0.1 refactor option; placing in `core/_types.py` is the simpler choice for this story

**Boundary rules:**
- `physlink.core/ → physlink.core/` ✅ — `_types.py` intra-core (no change)
- `physlink.adapters/ → physlink.core/` ✅ — `dreamer.py` importing `TrajectoryBuffer` from `core._types`

**Public API surface — `TrajectoryBuffer` is NOT exported from `physlink.__init__`:**
- Architecture doc: `TrajectoryBatch`, `AdaptationConfig`, `AdaptationRun` in sub-modules (advanced use)
- `TrajectoryBuffer` follows the same pattern

### References

- [Source: epics.md#Story 4.2] — Acceptance Criteria, user story statement
- [Source: epics.md#FR-08] — `TrajectoryBuffer.export(path)` / `.load(path)`
- [Source: architecture.md#Gap Analysis] — `TrajectoryBuffer I/O dans utils/io.py` (deferred to post-v0.1, placed in _types.py for now)
- [Source: architecture.md#Category 1] — `fit()` silent conversion pattern
- [Source: implementation-artifacts/4-1-adaptationconfig-and-adaptationrun.md] — deferred import pattern, ruff rules, File List requirement

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

<!-- Debug entries will be added here as needed -->

### Completion Notes List

- `TrajectoryBuffer` implemented as `@dataclass` in `src/physlink/core/_types.py` with `export(path)`, `load(path)` (pickle-based), `to_batch()`, `__len__`, `__iter__`, `__repr__`.
- `fit()` in `dreamer.py` updated: type annotation extended to `list[dict] | TrajectoryBatch | TrajectoryBuffer`; `TrajectoryBuffer` converted via `to_batch()` before existing `list` conversion.
- `visualize()` in `dreamer.py` updated identically for type annotation and conversion.
- `TrajectoryBuffer` imported at module-level in `dreamer.py` (runtime import alongside `TrajectoryBatch`).
- 31 new tests added: 24 in `test_types.py` (`TestTrajectoryBufferConstruction` ×10, `TestTrajectoryBufferExport` ×4, `TestTrajectoryBufferLoad` ×8, `TestTrajectoryBufferIdempotence` ×2), 7 in `test_dreamer_cpu.py` (`TestFitWithTrajectoryBufferStory42` ×7). Gap-closure (+5 tests) documented in `_bmad-output/implementation-artifacts/tests/test-summary-4-2.md`.
- Full test suite: 620 passed, 3 skipped, 0 failures. ruff: zero warnings. mkdocs: build successful.

### File List

- `src/physlink/core/_types.py` — added `TrajectoryBuffer` dataclass with `export`, `load`, `to_batch`, `__len__`, `__iter__`, `__repr__`; added `Raises` to `export()` docstring (AI-review fix)
- `src/physlink/adapters/dreamer.py` — added `TrajectoryBuffer` to runtime import; extended `fit()` and `visualize()` type annotations and conversion branches
- `tests/unit/core/test_types.py` — added `TrajectoryBuffer` import; added `TestTrajectoryBufferConstruction` (10 tests), `TestTrajectoryBufferExport` (4), `TestTrajectoryBufferLoad` (8), `TestTrajectoryBufferIdempotence` (2) = 24 new tests
- `tests/unit/adapters/test_dreamer_cpu.py` — added `TestFitWithTrajectoryBufferStory42` class (7 new tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story 4.2 status updated to done
- `_bmad-output/implementation-artifacts/tests/test-summary-4-2.md` — gap-closure test summary (5 additional tests documented)
- `.gitignore` — added `__pycache__/`, `*.pyc`, `*.pyo`, `physlink_checkpoints/` (AI-review fix)

## Senior Developer Review (AI)

**Date:** 2026-05-22 | **Reviewer:** AI (claude-sonnet-4-6) | **Outcome:** APPROVED

**Acceptance Criteria:** All 3 ACs IMPLEMENTED — export/load fidelity, round-trip usability with `fit()`, idempotence (NFR-09).

**Fixes applied:**
- `src/physlink/core/_types.py` — Added `Raises: OSError` to `export()` docstring (Google-style completeness)
- `.gitignore` — Added `__pycache__/`, `*.pyc`, `*.pyo`, `physlink_checkpoints/` to prevent test artifacts from cluttering git status
- Story file — Updated test counts to reflect gap-closure reality (31 tests, not 26); added `test-summary-4-2.md` to File List

**No action items created. No critical issues found.**

## Change Log

- **2026-05-22** — Story 4.2 implemented: `TrajectoryBuffer` dataclass added to `core/_types.py` with pickle-based `export`/`load` and `to_batch()` convenience method; `fit()` and `visualize()` in `dreamer.py` extended to accept `TrajectoryBuffer` with silent conversion; 31 new tests added across 2 test files (24+7 after gap-closure); 620 tests pass, ruff clean.
- **2026-05-22** — AI review: corrected test counts in story metadata; added `export()` Raises doc; updated `.gitignore`; story status → done.
