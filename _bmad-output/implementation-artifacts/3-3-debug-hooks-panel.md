# Story 3.3: Debug Hooks Panel

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher investigating prediction quality issues,
I want to toggle a debug hooks panel alongside the progress bar,
so that I can see pipeline stage statuses without interrupting the adaptation loop.

## Acceptance Criteria

1. **Given** I call `adapter.fit(trajectories, steps=10000, checkpoint_interval_steps=1000, debug_hooks=True)`
   **When** the adaptation starts
   **Then** the debug hooks panel is shown alongside the progress bar
   **And** it shows pipeline stage statuses for at minimum: data loading, world model update, actor update, critic update
   **And** each stage shows OK or a diagnostic status (not raw stack traces)
   **And** the main progress bar (step count, ETA, health, throughput) continues to stream alongside the panel

2. **Given** `adapter.fit()` is called without `debug_hooks=True` (default is `False`)
   **When** the adaptation runs
   **Then** no debug panel is shown (opt-in, not default)
   **And** the progress bar is unaffected by the absence of hooks

## Tasks / Subtasks

- [x] Task 1: Add `_STAGE_NAMES` constant and `_DebugPanel` class to `src/physlink/adapters/dreamer.py` (AC: #1)
  - [x] Add `_STAGE_NAMES: tuple[str, ...] = ("data_loading", "world_model_update", "actor_update", "critic_update")` as module-level constant
  - [x] Add `_DebugPanel` class with `stages: dict[str, str]` initialized to `"waiting..."` for all stage names
  - [x] Add `update_all(statuses: dict[str, str]) -> None` method
  - [x] Add `__rich__(self) -> Any` method — builds and returns a fresh `rich.table.Table` from current `self.stages` (deferred `from rich.table import Table` inside the method)
  - [x] `__rich__()` renders "OK" as `[bold green]OK[/bold green]`, "waiting..." as `[dim]waiting...[/dim]`, any other value as `[bold red]{value}[/bold red]`
  - [x] `__rich__()` annotated with `# noqa: ANN401` (same pattern as other private methods)

- [x] Task 2: Add `_build_debug_layout(steps, panel)` context manager to `src/physlink/adapters/dreamer.py` (AC: #1)
  - [x] Place after `_build_progress_bar()` in the module
  - [x] Signature: `def _build_debug_layout(steps: int, panel: _DebugPanel) -> Generator[tuple[Any, Any], None, None]:`
  - [x] Use `rich.live.Live(Group(progress, panel), refresh_per_second=4)` as the outer context — NOT `with Progress(...) as progress:` (which would create nested Live displays)
  - [x] `progress` is instantiated as `Progress(SpinnerColumn(), TextColumn(...), BarColumn(), MofNCompleteColumn(), TextColumn("•"), TimeRemainingColumn(), TextColumn("•"), _StepsPerSecColumn(), TextColumn("•"), _HealthColumn())` WITHOUT using it as a context manager
  - [x] `task_id = progress.add_task("[cyan]DreamerV3 adaptation", total=steps, health="OK")`
  - [x] Inner classes `_StepsPerSecColumn` and `_HealthColumn` are the same as in `_build_progress_bar()` — duplicate here (deferred import pattern, same as Story 3.2)
  - [x] All `rich` imports deferred inside the function body (same convention as `_build_progress_bar`)
  - [x] Yields `(progress, task_id)` — same tuple shape as `_build_progress_bar`

- [x] Task 3: Update `fit()` signature and body in `src/physlink/adapters/dreamer.py` (AC: #1, #2)
  - [x] Add `debug_hooks: bool = False` parameter after `checkpoint_interval_steps` in `fit()` signature
  - [x] Update Google-style docstring: add `debug_hooks` to Args section
  - [x] Update docstring Example to show `adapter.fit(trajectories, steps=10, debug_hooks=True)`
  - [x] In `fit()` body, after the optimizer/scaler setup, split into if/else on `debug_hooks`:
    - **debug path**: `debug_panel = _DebugPanel(); with _build_debug_layout(steps, debug_panel) as (progress, task_id):`
    - **non-debug path**: existing `with _build_progress_bar(steps) as (progress, task_id):` — unchanged
  - [x] Debug loop body: initialize `stage_statuses = {name: "OK" for name in _STAGE_NAMES}`, wrap `_training_step` in `try/except Exception as exc:` — on exception, set `world_model_update`, `actor_update`, `critic_update` to `type(exc).__name__`, call `debug_panel.update_all(stage_statuses)`, re-raise
  - [x] Debug loop body: on success, call `debug_panel.update_all(stage_statuses)` then `progress.update(task_id, advance=1, health=self._compute_health(loss.item()))`
  - [x] Non-debug loop body: unchanged from Story 3.2 (no stage tracking)
  - [x] `debug_hooks` does NOT require bool-before-int guard — it is already `bool`
  - [x] No new `ValidationError` raised for `debug_hooks` — it is a bool with no invalid range

- [x] Task 4: Update `tests/unit/adapters/test_dreamer_cpu.py` — add `TestFitDebugHooks` class (AC: #2)
  - [x] Add after `TestResetTrainingState` (end of file)
  - [x] `test_fit_debug_hooks_false_is_default`: fit with `steps=0` raises ValidationError — verifies `debug_hooks` default doesn't interfere with validation
  - [x] `test_fit_debug_hooks_true_still_validates_steps`: fit with `steps=0, debug_hooks=True` raises ValidationError — validation fires before `debug_hooks` branch is reached
  - [x] `test_debug_panel_initializes_with_waiting_status`: `_DebugPanel()` → all `panel.stages.values()` are `"waiting..."`
  - [x] `test_debug_panel_update_all_sets_stage_statuses`: call `update_all({"data_loading": "OK"})` → `panel.stages["data_loading"] == "OK"`
  - [x] `test_debug_panel_partial_update_leaves_other_stages`: after partial `update_all`, unchanged stages still show `"waiting..."`
  - [x] `test_debug_panel_has_all_four_stage_names`: `set(panel.stages.keys()) == set(_STAGE_NAMES)`
  - [x] These tests do NOT require GPU — they test pure-Python `_DebugPanel` state and validation logic
  - [x] No `@pytest.mark.gpu` on any test in this class

- [x] Task 5: Update `tests/unit/adapters/test_dreamer_gpu.py` — add `TestFitDebugHooks` class (AC: #1)
  - [x] All tests in this class: `@pytest.mark.gpu`
  - [x] `test_fit_with_debug_hooks_true_completes`: `adapter.fit(synthetic_trajectories, steps=50, debug_hooks=True)` — smoke test, completes without error
  - [x] `test_fit_with_debug_hooks_false_completes`: `adapter.fit(synthetic_trajectories, steps=50, debug_hooks=False)` — explicitly tests the default path
  - [x] `test_fit_debug_hooks_true_idempotent`: two sequential calls with `debug_hooks=True` both complete (NFR-09)
  - [x] `test_fit_debug_hooks_does_not_affect_health_tracking`: after `fit(steps=20, debug_hooks=True)`, `adapter._baseline_loss is not None` (baseline established after ≥10 steps)

- [x] Task 6: Run full test suite — zero regressions (AC: all)
  - [x] `pytest tests/ -x -m "not gpu"` — all CPU tests pass (474 passed, 3 skipped)
  - [x] `ruff check src/` — zero warnings
  - [x] `mkdocs build --strict` — docs build successfully
  - [x] File List complete AND Change Log reflects actual state before marking done

## Dev Notes

### What Story 3.3 Does and Does NOT Do

**This story implements:**
- `debug_hooks: bool = False` parameter on `fit()`
- `_DebugPanel` private class (module-level, `dreamer.py`)
- `_build_debug_layout()` private context manager (module-level, `dreamer.py`)
- `_STAGE_NAMES` module-level constant

**Explicitly deferred — do NOT implement:**
- Checkpoint writing (Story 3.4)
- `visualize()` / triptych GIF (Story 3.5)
- `export()` / share panel (Story 3.6)
- `AdaptationRun` return type (Story 4.1) — `fit()` still returns `None`

### Critical Architecture: Two Separate Display Paths

Story 3.2 uses `with Progress(...) as progress:` which creates an internal `rich.live.Live` instance. For the debug path, we need a `rich.live.Live` that combines `progress` AND the `_DebugPanel` in a `Group`. These two mechanisms are incompatible — you CANNOT use `Progress` as a context manager inside another `Live` context.

**Non-debug path (unchanged):**
```python
with _build_progress_bar(steps) as (progress, task_id):
    # existing loop — no change
```

**Debug path (new):**
```python
debug_panel = _DebugPanel()
with _build_debug_layout(steps, debug_panel) as (progress, task_id):
    for _ in range(steps):
        stage_statuses = {name: "OK" for name in _STAGE_NAMES}
        optimizer.zero_grad(set_to_none=True)
        try:
            loss = self._training_step(tensor_batch, device)
        except Exception as exc:
            for name in ("world_model_update", "actor_update", "critic_update"):
                stage_statuses[name] = type(exc).__name__
            debug_panel.update_all(stage_statuses)
            raise
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(all_params, max_norm=100.0)
        scaler.step(optimizer)
        scaler.update()
        debug_panel.update_all(stage_statuses)
        progress.update(task_id, advance=1, health=self._compute_health(loss.item()))
```

### `_DebugPanel.__rich__()` — How Rich Live Updates Work

Rich's `Live` display calls `__rich__()` on each renderable on every refresh cycle (4× per second). By implementing `__rich__()` to build a fresh `Table` from `self.stages` each call, updating `self.stages` causes the next refresh to show new values automatically.

```python
class _DebugPanel:
    def __init__(self) -> None:
        self.stages: dict[str, str] = {name: "waiting..." for name in _STAGE_NAMES}

    def update_all(self, statuses: dict[str, str]) -> None:
        self.stages.update(statuses)

    def __rich__(self) -> Any:  # noqa: ANN401
        from rich.table import Table

        table = Table(
            title="[dim]Debug Hooks Panel[/dim]",
            show_header=True,
            box=None,
            padding=(0, 1),
        )
        table.add_column("Stage", style="dim", no_wrap=True)
        table.add_column("Status", no_wrap=True)
        for name, status in self.stages.items():
            label = name.replace("_", " ")
            if status == "OK":
                cell = "[bold green]OK[/bold green]"
            elif status == "waiting...":
                cell = "[dim]waiting...[/dim]"
            else:
                cell = f"[bold red]{status}[/bold red]"
            table.add_row(label, cell)
        return table
```

### `_build_debug_layout()` — Key Difference from `_build_progress_bar()`

`_build_progress_bar()` uses `with Progress(...) as progress:` which creates an internal `Live`.

`_build_debug_layout()` uses `Live(Group(progress, panel), ...)` as the outer context and instantiates `Progress(...)` WITHOUT the context manager:

```python
@contextlib.contextmanager
def _build_debug_layout(
    steps: int,
    panel: _DebugPanel,
) -> Generator[tuple[Any, Any], None, None]:
    from rich.console import Group
    from rich.live import Live
    from rich.progress import (
        BarColumn, MofNCompleteColumn, Progress, ProgressColumn,
        SpinnerColumn, TextColumn, TimeRemainingColumn,
    )
    from rich.text import Text

    class _StepsPerSecColumn(ProgressColumn):
        def render(self, task: Any) -> Text:  # noqa: ANN401
            if task.speed is None:
                return Text("? step/s", style="dim")
            return Text(f"{task.speed:.1f} step/s", style="cyan")

    class _HealthColumn(ProgressColumn):
        def render(self, task: Any) -> Text:  # noqa: ANN401
            health = task.fields.get("health", "OK")
            style = "bold green" if health == "OK" else "bold red"
            return Text(health, style=style)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        TextColumn("•"),
        _StepsPerSecColumn(),
        TextColumn("•"),
        _HealthColumn(),
    )
    task_id = progress.add_task(
        "[cyan]DreamerV3 adaptation",
        total=steps,
        health="OK",
    )

    with Live(Group(progress, panel), refresh_per_second=4):
        yield progress, task_id
```

### Updated `fit()` Docstring — Args Section

Add `debug_hooks` to the docstring Args section:

```
Args:
    trajectories: Trajectory dataset. list[dict] is silently converted
        to TrajectoryBatch. Each dict must contain at minimum "obs" and
        "action" keys with numpy-compatible values.
    steps: Total gradient steps to run. Must be > 0.
    checkpoint_interval_steps: Interval between checkpoint saves.
        Checkpoint writing is deferred to Story 3.4; this parameter is
        accepted to ensure forward-compatible API. Must be > 0.
    debug_hooks: When True, displays a debug panel alongside the progress
        bar showing pipeline stage statuses (data_loading, world_model_update,
        actor_update, critic_update). Each stage shows OK or a diagnostic
        status. Defaults to False (opt-in, not default).
```

### ruff Compliance Notes

The `ruff` config enables: `select = ["E", "F", "W", "I", "N", "UP", "ANN", "RUF"]`.  
`BLE` (blind exception) is NOT enabled — `except Exception as exc:` is permitted without `# noqa`.  
`ANN401` is enabled — add `# noqa: ANN401` on `__rich__(self) -> Any` (returning `Any` from a private method using deferred rich type).  
The `_build_debug_layout` generator return type annotation `Generator[tuple[Any, Any], None, None]` requires `from collections.abc import Generator` (already imported at module level from Story 3.2).

### Stage Tracking: data_loading Is Always OK

In the current implementation, `data_loading` will always show "OK" because `tensor_batch` is pre-processed before the training loop (in `fit()` body before the `with _build_debug_layout` block). The `try/except` in the loop only wraps `_training_step`. This is architecturally correct — data loading failure would surface as an exception before the loop even starts.

For diagnostic accuracy: only `world_model_update`, `actor_update`, and `critic_update` can show error statuses from `_training_step` exceptions. `data_loading` is always set to "OK" in `stage_statuses` initialization and only updates if explicitly overridden.

### Files Being Modified — Current State

**`src/physlink/adapters/dreamer.py`** (UPDATE):
- Current `fit()` signature: `fit(self, trajectories, steps, checkpoint_interval_steps=1000) -> None`
- Story 3.3 adds: `debug_hooks: bool = False` as 4th parameter
- `_build_progress_bar()` remains unchanged (non-debug path)
- Add `_STAGE_NAMES`, `_DebugPanel`, `_build_debug_layout()` as new module-level symbols

**`tests/unit/adapters/test_dreamer_cpu.py`** (UPDATE):
- Currently ends after `TestResetTrainingState`
- Add `TestFitDebugHooks` class at the end

**`tests/unit/adapters/test_dreamer_gpu.py`** (UPDATE):
- Currently ends after `TestFitVRAMBudget`
- Add `@pytest.mark.gpu class TestFitDebugHooks` class at the end

### Anti-Pattern Prevention

- **DO NOT** use `with Progress(...) as progress:` inside `_build_debug_layout()` — this creates nested `Live` displays and will either fail or corrupt the terminal
- **DO NOT** try to update `Table.rows` in-place — `rich.Table` rows are immutable once added; use `__rich__()` to build a fresh `Table` on each render
- **DO NOT** add validation for `debug_hooks` — it is a `bool` with no invalid range; no `ValidationError` needed
- **DO NOT** add `bool-before-int` guard for `debug_hooks` — it is already `bool`, not `int`
- **DO NOT** add module-level `from rich.live import Live` — maintain deferred import convention (all rich imports stay inside function bodies)

### Previous Story Carry-Overs

From Epic 2 retrospective (still outstanding):
- `YOUR-ORG` placeholder in README.md, mkdocs.yml, ci.yml, publish.yml — Story 3.3 does NOT block on this
- Story 3.6 (Colab URL behavior) depends on it — keep deferred

From Story 3.2 completion notes:
- `ruff` clean requires `# noqa: ANN401` on private methods returning `Any`
- `ANN204` not required for `adapters/` (pyproject.toml overrides)
- File List + Change Log must be complete before marking `done` (Action Item P-1 from Epic 2 retro)
- `from __future__ import annotations` is NOT required in `adapters/dreamer.py`

### Project Structure Notes

- `src/physlink/adapters/dreamer.py` — UPDATE (add `_STAGE_NAMES`, `_DebugPanel`, `_build_debug_layout`, update `fit()`)
- `tests/unit/adapters/test_dreamer_cpu.py` — UPDATE (add `TestFitDebugHooks` at end)
- `tests/unit/adapters/test_dreamer_gpu.py` — UPDATE (add `@pytest.mark.gpu class TestFitDebugHooks` at end)

No new directories needed. No new dependencies — `rich>=13.0` is already in `pyproject.toml` and `from rich.live import Live` + `from rich.console import Group` are both available in rich 13+.

### References

- [Source: epics.md#Story 3.3] — Acceptance Criteria and scope
- [Source: epics.md#FR-03] — DreamerV3 Adapter: `debug_hooks` panel toggleable alongside progress bar
- [Source: epics.md#UX-DR-04] — Progress bar: step count, ETA, prediction health (OK/ANOMALY), throughput; debug hooks panel toggleable alongside
- [Source: architecture.md#Category 1] — `fit()` signature contract: `list[dict] | TrajectoryBatch`, `steps: int`, `checkpoint_interval_steps: int`
- [Source: architecture.md#Category 2] — ValidationError with Got/Expected/Fix template; bool-before-int guard (for steps/checkpoint_interval only, NOT for debug_hooks)
- [Source: architecture.md#Structure Patterns] — `src/physlink/adapters/dreamer.py` location; `tests/unit/adapters/` location; `@pytest.mark.gpu` rule
- [Source: architecture.md#Testing Patterns] — `tests/conftest.py` single fixture; `@pytest.mark.gpu` for all CUDA tests
- [Source: pyproject.toml] — `rich>=13.0` in dependencies (no new dep); `BLE` rule NOT enabled; `ANN` rule IS enabled
- [Source: implementation-artifacts/3-2-adaptation-loop-with-progress-bar.md#Dev Notes] — deferred torch import convention; `_build_progress_bar()` deferred rich import pattern; Story 3.2 explicitly deferred `debug_hooks=True`; ruff `# noqa: ANN401` pattern; File List + Change Log closing checklist (P-1)
- [Source: implementation-artifacts/3-1-dreamerv3adapter-construction.md#Dev Notes] — `from __future__ import annotations` NOT required in `adapters/dreamer.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blockers encountered. Implementation followed Dev Notes architecture exactly.

### Completion Notes List

- Implemented `_STAGE_NAMES` tuple and `_DebugPanel` class at module level in `dreamer.py`. `_DebugPanel.__rich__()` builds a fresh `rich.Table` on each call (Rich Live refresh pattern).
- Implemented `_build_debug_layout()` using `Live(Group(progress, panel))` as outer context — avoids nested Live displays that would occur with `with Progress(...) as progress:`.
- Updated `fit()` with `debug_hooks: bool = False` parameter; if/else branching preserves the non-debug path unchanged.
- Debug loop wraps `_training_step` in `try/except Exception` to capture stage errors without blind exception suppression (`BLE` not enabled in ruff).
- `data_loading` always shows "OK" by design — tensor pre-processing happens before the loop.
- Added 25 new CPU tests across `TestFitDebugHooks` (+3 gap fills by test-automator), `TestStageNames` (7 tests), `TestDebugPanelRendering` (9 tests), plus 6 originally specified in story — and 4 GPU tests.
- All 474 CPU tests pass (474 passed, 3 skipped), ruff clean, mkdocs builds successfully.

### File List

- src/physlink/adapters/dreamer.py
- tests/unit/adapters/test_dreamer_cpu.py
- tests/unit/adapters/test_dreamer_gpu.py

## Senior Developer Review (AI)

**Reviewer:** Denis Hamon (AI) — 2026-05-22

**Verdict:** APPROVED — No critical or blocking issues found.

**AC Validation:**
- AC #1: `debug_hooks=True` → `_DebugPanel` + `_build_debug_layout()` displayed alongside progress bar; `type(exc).__name__` used for error status (not raw stack traces). IMPLEMENTED ✅
- AC #2: `debug_hooks=False` (default) → non-debug path unchanged; no panel shown. IMPLEMENTED ✅

**Issues Found and Fixed Automatically:**

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| MEDIUM | Task 6 claimed "455 passed" but actual count after test-automator gap-filling is 474 | Updated to "474 passed, 3 skipped" |
| MEDIUM | Completion Notes said "6 CPU tests" but test-automator added 19 more (TestStageNames ×7, TestDebugPanelRendering ×9, TestFitDebugHooks +3) | Updated to "25 new CPU tests" |
| MEDIUM | Story Status stuck at "review"; sprint-status not synced | Updated story to "done"; sprint-status synced |

**Remaining notes (LOW, no fix required):**
- `table.columns[1]._cells` in `TestDebugPanelRendering` accesses Rich's internal Column attribute — fragile if Rich changes internals, but tests pass at rich≥13 and no public API alternative exists.
- `test_fit_debug_hooks_false_is_default` tests non-interference, not the actual default value — weakly named but functionally correct per story spec.

**Code Quality:** No security issues, no performance concerns, no missing error handling. ruff clean ✅. Implementation matches Dev Notes architecture exactly.

## Change Log

- 2026-05-22: Story 3.3 implemented — added `_STAGE_NAMES`, `_DebugPanel`, `_build_debug_layout()` to `dreamer.py`; updated `fit()` with `debug_hooks: bool = False` parameter and dual display path; added `TestFitDebugHooks` to CPU and GPU test suites.
- 2026-05-22: Review complete (AI) — corrected test count to 474 passed, updated Completion Notes, synced story and sprint status to "done".
