# Story 3.6: Export and Share Panel

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a researcher who validated their adaptation with a triptych,
I want to call adapter.export(path) and get a complete artifact bundle with a shareable Colab URL,
so that I can send my results to collaborators or archive them reproducibly.

## Acceptance Criteria

1. **Given** a `DreamerV3Adapter` after `fit()` and `visualize()` have been called
   **When** I call `adapter.export(path="./physlink_export/")`
   **Then** the directory at `path` is created if it does not exist
   **And** the directory contains: a GIF file, a YAML config file, a summary text file
   **And** the YAML config is valid YAML containing: space config (obs/act dimensions and bounds), checkpoint path

2. **Given** `adapter.export()` completes
   **When** I inspect the YAML file
   **Then** it is parseable by PyYAML without errors
   **And** it contains at minimum: `obs_space`, `act_space`, and `checkpoint_path` keys
   **And** `obs_space` and `act_space` values are JSON-serializable dicts (not raw Python objects)

3. **Given** the export is complete in a Colab environment
   **When** I trigger the share panel (called automatically at the end of `export()`)
   **Then** the current notebook URL is copied to the clipboard (UX-DR-06)
   **And** a confirmation message is printed showing the URL was copied

4. **Given** the share panel is triggered outside a Colab environment (e.g., local Jupyter or script)
   **When** it executes
   **Then** a message is printed stating the URL cannot be copied automatically outside Colab
   **And** no exception is raised (silent graceful degradation)

5. **Given** `adapter.export()` is called before `visualize()` has been run (`self._triptych_path is None`)
   **When** it executes
   **Then** an `AdapterError` is raised with Got/Expected/Fix message

6. **Given** `adapter.export()` is called and `self._last_checkpoint_path is None` (no checkpoint was saved during fit)
   **When** the YAML is written
   **Then** `checkpoint_path: null` is written (no exception — absence of a checkpoint is valid)

## Tasks / Subtasks

- [x] Task 1: Add `_last_checkpoint_path` instance variable and capture checkpoint paths in `fit()` in `src/physlink/adapters/dreamer.py` (AC: #1, #6)
  - [x] Add `self._last_checkpoint_path: str | None = None` in `__init__()` after the `self._triptych_path` line (line ~280)
  - [x] In `fit()` debug-hooks branch (line ~639): change `_save_checkpoint(...)` to `self._last_checkpoint_path = _save_checkpoint(...)`
  - [x] In `fit()` non-debug branch (line ~658): same capture: `self._last_checkpoint_path = _save_checkpoint(...)`
  - [x] Do NOT reset `_last_checkpoint_path` in `_reset_training_state()` — it must persist across calls so `export()` always has the most recent checkpoint path

- [x] Task 2: Implement `export()` method in `src/physlink/adapters/dreamer.py` (AC: #1, #2, #3, #4, #5, #6)
  - [x] Replace the `raise NotImplementedError(...)` body (line 794) with full implementation
  - [x] New return type: `-> dict[str, str]` (returns artifact paths dict for testability)
  - [x] First: check `if self._triptych_path is None:` → raise `AdapterError` with Got/Expected/Fix
  - [x] All imports DEFERRED inside the method body: `import os`, `import shutil`, `import yaml`
  - [x] Create output directory: `os.makedirs(path, exist_ok=True)` (idempotent — NFR-09)
  - [x] Copy GIF: `gif_dest = os.path.join(path, "triptych.gif")`, `shutil.copy2(self._triptych_path, gif_dest)`
  - [x] Build YAML config dict with `obs_space`, `act_space`, `checkpoint_path`
  - [x] Write YAML: `yaml.dump(config, f, default_flow_style=False, allow_unicode=True)`
  - [x] Write summary: human-readable text block with adapter type, dims, elapsed, paths, timestamp
  - [x] Print export confirmation and individual artifact paths
  - [x] Call `_share_panel(path)` (the share helper defined in Task 3)
  - [x] Return `{"gif": gif_dest, "config": yaml_path, "summary": summary_path}`
  - [x] Update method docstring: Args (path), Returns (dict[str, str] — artifact paths), Raises (AdapterError), Example

- [x] Task 3: Implement `_share_panel()` module-level helper in `src/physlink/adapters/dreamer.py` (AC: #3, #4)
  - [x] Add the helper as a module-level private function (after `_check_checkpoint_metadata`, before the `DreamerV3Adapter` class definition)
  - [x] Signature: `def _share_panel(export_path: str) -> None:`
  - [x] Colab detection: try `import google.colab` — if it imports, we're in Colab
  - [x] Inside Colab path: use `IPython.display.Javascript` to copy to clipboard
  - [x] Outside Colab path (ImportError): print graceful message
  - [x] All imports deferred inside the function (no module-level `import google.colab`)
  - [x] Add Google-style docstring with Args and Example sections
  - [x] Wrap entire function body in a broad try/except to prevent share panel errors from bubbling into `export()`

- [x] Task 4: Update `tests/unit/adapters/test_dreamer_cpu.py` — replace stub tests and add export tests (AC: all)
  - [x] Update existing stub tests: `test_export_raises_adapter_error_without_visualize` — assert `AdapterError`
  - [x] Update existing stub tests: `test_export_error_message_contains_got_expected_fix` — assert Got/Expected/Fix
  - [x] New fixture `_adapter_with_triptych` with stub GIF bytes
  - [x] New test class `TestDreamerV3AdapterExport` with 10 CPU tests (all pass)

- [x] Task 5: Run full test suite — zero regressions (AC: all)
  - [x] `pytest tests/ -x -m "not gpu"` — 518 passed, 3 skipped, 18 deselected
  - [x] `ruff check src/` — zero warnings
  - [x] `mkdocs build --strict` — docs build successfully
  - [x] File List complete AND Change Log entry added before marking done

## Dev Notes

### What Story 3.6 Does and Does NOT Do

**This story implements:**
- `self._last_checkpoint_path` instance variable to capture the last checkpoint path from `fit()`
- Full `DreamerV3Adapter.export(path)` implementation: directory creation, GIF copy, YAML config, summary text
- `_share_panel()` module-level helper: Colab clipboard copy or graceful non-Colab message
- Return value `dict[str, str]` with artifact paths (for test assertability)
- Updated tests: stub tests rewritten to test actual `AdapterError` behavior

**Explicitly deferred — do NOT implement:**
- `AdaptationRun` return type for `fit()` (Story 4.1) — `fit()` still returns `None`
- `TrajectoryBuffer` (Story 4.2)
- `register_invariant()` / `compliance_report()` — out of scope entirely (Epic 4)

### Critical: `_save_checkpoint` Return Value is Currently Discarded

In the current `fit()` implementation, `_save_checkpoint()` is called but its return value is discarded in BOTH branches:

```python
# Line ~639 (debug-hooks branch):
_save_checkpoint(
    self._model, self._actor, self._critic,
    completed, checkpoint_dir,
)

# Line ~658 (non-debug branch):
_save_checkpoint(
    self._model, self._actor, self._critic,
    completed, checkpoint_dir,
)
```

**Fix:** Capture the return value:
```python
self._last_checkpoint_path = _save_checkpoint(
    self._model, self._actor, self._critic,
    completed, checkpoint_dir,
)
```

This is a minimal change that has zero behavioral impact on existing tests.

### Colab Detection and Share Panel

The canonical Colab detection pattern:
```python
try:
    import google.colab  # noqa: F401
    _in_colab = True
except ImportError:
    _in_colab = False
```

For the share panel, the clipboard copy uses IPython's `display(Javascript(...))` pattern. This is the same pattern used by `tqdm` and other Colab-aware libraries. It does NOT require the `pyperclip` package (which requires OS-level clipboard access and does not work in Colab).

**Full `_share_panel()` implementation:**
```python
def _share_panel(export_path: str) -> None:
    """Trigger the Colab share panel: copy notebook URL to clipboard.

    In Google Colab, copies the current notebook URL to the clipboard via
    Javascript. Outside Colab, prints a graceful fallback message.

    Args:
        export_path: Absolute path to the export directory. Shown in fallback
            message so collaborators know where to find the artifacts.

    Example:
        >>> _share_panel("./physlink_export")
        [physlink] Share panel: URL copy only available in Google Colab.
        ...
    """
    try:
        import google.colab  # noqa: F401
        in_colab = True
    except ImportError:
        in_colab = False

    try:
        if in_colab:
            from IPython.display import Javascript, display
            display(Javascript(
                "navigator.clipboard.writeText(window.location.href)"
                ".then(() => console.log('[physlink] Notebook URL copied.'));"
            ))
            print("[physlink] Share panel: notebook URL copied to clipboard.")
            print(f"[physlink] Export path for collaborators: {export_path}")
        else:
            print(
                "[physlink] Share panel: URL copy is only available in Google Colab.\n"
                f"           To share your results, send the export directory: {export_path}"
            )
    except Exception as exc:  # noqa: BLE001
        print(f"[physlink] Share panel unavailable: {type(exc).__name__}")
```

### Export Method — Full Expected Docstring

```python
def export(self, path: str) -> dict[str, str]:
    """Export a complete artifact bundle to the specified directory.

    Copies the triptych GIF, writes a YAML configuration file, and writes
    a human-readable summary. Calls the share panel to copy the Colab
    notebook URL to the clipboard (Colab only; graceful fallback elsewhere).

    Args:
        path: Directory path for the exported artifacts. Created if it does
            not exist. Existing files in the directory are overwritten.

    Returns:
        dict with keys ``gif``, ``config``, ``summary`` mapping to the
        absolute paths of the respective exported files.

    Raises:
        AdapterError: If ``visualize()`` has not been called (no triptych
            available to export).

    Example:
        >>> adapter.fit(trajectories, steps=1000)
        >>> adapter.visualize(trajectories)
        >>> artifacts = adapter.export("./physlink_export")
        >>> artifacts["config"]  # absolute path to config.yaml
        '/abs/path/physlink_export/config.yaml'
    """
```

### YAML Config Structure

The YAML written to `config.yaml` must be parseable by `yaml.safe_load()`:

```yaml
obs_space:
  dims: 14
  include_velocity: true
  clip_bounds: null
  normalize: false
act_space:
  dims: 7
  bounds:
  - - -1.0
    - 1.0
  - - -1.0
    - 1.0
  # ... (one entry per dim)
checkpoint_path: /abs/path/physlink_checkpoints/checkpoint_step_10000.safetensors
```

Use `self.obs_space.explain()` and `self.act_space.explain()` — these already return JSON-serializable dicts (verified in Story 2.4). The `checkpoint_path` is either `self._last_checkpoint_path` (str or None).

`yaml.dump(config, f, default_flow_style=False, allow_unicode=True)` produces clean block-style YAML.

### Summary File Structure

The `summary.txt` should be a human-readable block:
```
physlink Export Summary
=======================
Adapter:          DreamerV3Adapter
obs_dims:         14
act_dims:         7
Fit elapsed:      23.4 min
Triptych GIF:     /abs/path/physlink_triptych.gif
Checkpoint:       /abs/path/checkpoint_step_10000.safetensors
Exported at:      2026-05-22T18:00:00Z
```

Use `datetime.datetime.now(datetime.timezone.utc).isoformat()` for the timestamp (same pattern as `_save_checkpoint` after Story 3.5's fix).

### ruff Compliance (Carry-Over from Stories 3.3–3.5)

- `ANN401` IS enabled — add `# noqa: ANN401` if a function's parameter or return is annotated `Any`
- `BLE` (blind exception) is NOT enabled — `except Exception as exc:` is permitted
- `from __future__ import annotations` is NOT needed in `adapters/dreamer.py`
- `F401` on `import google.colab` — add `# noqa: F401` since it's imported only for side-effect detection
- All third-party imports DEFERRED inside function bodies
- `yaml` is already a dependency (`pyyaml>=6.0` in `pyproject.toml`) — no new deps needed
- `shutil` and `os` are stdlib — no new deps needed

### Deferred Import Pattern in `export()`

```python
def export(self, path: str) -> dict[str, str]:
    import os
    import shutil
    import datetime
    import yaml  # pyyaml — already in dependencies
    from physlink.core.exceptions import AdapterError
    ...
```

Following the established pattern from Stories 3.2–3.5: all third-party and stdlib imports DEFERRED inside method body.

### Updating `TestDreamerV3AdapterStubs`

The two existing stub tests for `export()` use `NotImplementedError` assertions that will break once the implementation is added. They must be updated **in the same PR**:

```python
# BEFORE (will break):
def test_export_raises_not_implemented_error(self) -> None:
    with pytest.raises(NotImplementedError):
        adapter.export("/tmp/test_export")

def test_export_error_message_references_story_36(self) -> None:
    with pytest.raises(NotImplementedError) as exc_info:
        adapter.export("/tmp/test_export")
    assert "3.6" in str(exc_info.value)

# AFTER (correct):
def test_export_raises_adapter_error_without_visualize(self) -> None:
    from physlink.core.exceptions import AdapterError
    with pytest.raises(AdapterError):
        adapter.export("/tmp/test_export")

def test_export_error_message_contains_got_expected_fix(self) -> None:
    from physlink.core.exceptions import AdapterError
    with pytest.raises(AdapterError) as exc_info:
        adapter.export("/tmp/test_export")
    msg = str(exc_info.value)
    assert "Got:" in msg
    assert "Expected:" in msg
    assert "Fix:" in msg
```

### Test Setup Pattern for Export Tests

The export tests need a `DreamerV3Adapter` with `_triptych_path` set to a real GIF file. Use `tmp_path` fixture and create a minimal stub GIF:

```python
@pytest.fixture
def _adapter_with_triptych(tmp_path: Path) -> DreamerV3Adapter:
    from physlink import DreamerV3Adapter
    obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
    act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
    adapter = DreamerV3Adapter(obs, act)
    # Create a minimal valid GIF for export tests
    stub_gif = tmp_path / "stub.gif"
    stub_gif.write_bytes(b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;")
    adapter._triptych_path = str(stub_gif)
    return adapter
```

This avoids needing a real GPU or torch model for export tests.

### Architectural Boundary — No New Violations

The `export()` method imports `yaml` (pyyaml, already a dep), `os`, `shutil`, `datetime` — all stdlib or already-present deps. No new architectural boundary issues.

`_share_panel()` imports `google.colab` (detection only) and `IPython.display` (conditional). These are Colab-runtime packages and cannot be tested in CPU CI — use `capsys` to test the non-Colab path only.

Per `architecture.md#Architectural Boundaries`:
```
physlink.adapters/ →  physlink.core/       ✅ OK  (imports AdapterError from core.exceptions)
physlink.adapters/ →  physlink.utils/      ✅ OK  (already imports from utils.visualization)
```

No new boundary violations introduced.

### Files Being Modified — Current State

**`src/physlink/adapters/dreamer.py`** (UPDATE):
- Current state: `export()` at line 785 raises `NotImplementedError`; `__init__` has `_triptych_path` but NOT `_last_checkpoint_path`; `_save_checkpoint()` return value is discarded in `fit()`
- Add: `self._last_checkpoint_path: str | None = None` in `__init__` after `_triptych_path`
- Update: capture `_save_checkpoint()` return value in both `fit()` branches
- Add: `_share_panel()` module-level function (before the `DreamerV3Adapter` class)
- Replace: `export()` stub with full implementation
- Update: `export()` return type annotation `None` → `dict[str, str]`
- Update: class docstring to mention `export()` returns dict

**`tests/unit/adapters/test_dreamer_cpu.py`** (UPDATE):
- Update: `TestDreamerV3AdapterStubs.test_export_raises_not_implemented_error` → assert `AdapterError`
- Update: `TestDreamerV3AdapterStubs.test_export_error_message_references_story_36` → assert Got/Expected/Fix
- Add: `_adapter_with_triptych` fixture and `TestDreamerV3AdapterExport` class (10 CPU tests)

No new files, no new directories.

### Previous Story Carry-Overs

From Story 3.5 completion notes:
- ruff `# noqa: ANN401` on `Any` annotations — apply to `export()` if needed (not expected)
- `from __future__ import annotations` NOT required in `adapters/dreamer.py`
- File List + Change Log must be complete before marking `done` (Action Item P-1 from Epic 2 retro)

From Story 3.5 debug log:
- `datetime.utcnow()` was deprecated and fixed to `datetime.now(datetime.timezone.utc)` — use this pattern in `summary.txt` timestamp

### Project Structure Notes

- `src/physlink/adapters/dreamer.py` — UPDATE: `__init__`, `fit()`, add `_share_panel()`, replace `export()`
- `tests/unit/adapters/test_dreamer_cpu.py` — UPDATE: fix stub tests + add `TestDreamerV3AdapterExport`

No new directories or new files needed.

### References

- [Source: epics.md#Story 3.6] — Acceptance Criteria and full scope
- [Source: epics.md#FR-05] — `adapter.export(path)` produces artifact list (GIF, YAML config, summary); YAML contains space config and checkpoint path; share panel copies notebook URL
- [Source: epics.md#UX-DR-06] — Export produces GIF + YAML + summary; share panel copies notebook URL
- [Source: epics.md#NFR-09] — Colab cells idempotent (export with same path twice must not error)
- [Source: architecture.md#Category 3] — `utils/visualization.py` FR-04 triptych; `adapters/dreamer.py` FR-03 adapter
- [Source: architecture.md#Architectural Boundaries] — `adapters/ → core/` OK; `adapters/ → utils/` OK
- [Source: architecture.md#Error Message Patterns] — Got/Expected/Fix template for AdapterError
- [Source: architecture.md#Structure Patterns] — `src/physlink/adapters/dreamer.py`; test mirror in `tests/unit/adapters/`
- [Source: implementation-artifacts/3-5-triptych-gif-visualization.md#Dev Notes] — `self._triptych_path` stored for this story; deferred import convention; ruff ANN401/BLE; File List + Change Log closing checklist
- [Source: implementation-artifacts/3-5-triptych-gif-visualization.md#File List] — `dreamer.py` current state: `_fit_elapsed_seconds`, `_triptych_path` in `__init__`; `visualize()` implemented
- [Source: src/physlink/adapters/dreamer.py:279-280] — `_fit_elapsed_seconds` and `_triptych_path` are the existing instance variables to extend with `_last_checkpoint_path`
- [Source: src/physlink/adapters/dreamer.py:785-794] — `export()` stub raising `NotImplementedError`
- [Source: src/physlink/adapters/dreamer.py:638-661] — both `_save_checkpoint()` call sites whose return values must be captured
- [Source: src/physlink/adapters/dreamer.py:160-189] — `_save_checkpoint()` returns `str` (the absolute checkpoint path)
- [Source: tests/unit/adapters/test_dreamer_cpu.py:268-285] — two stub tests for `export()` that must be updated
- [Source: pyproject.toml] — `pyyaml>=6.0` already in dependencies; no new dep needed
- [Source: architecture.md#Category 2] — `AdapterError` scope: I/O explicitly managed by physlink

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- ruff RUF102: removed extraneous `f` prefix on static string in `summary_lines` list
- ruff RUF100: removed unused `# noqa: BLE001` directive — BLE is not enabled in this project

### Completion Notes List

- Added `self._last_checkpoint_path: str | None = None` in `DreamerV3Adapter.__init__()` after `_triptych_path`
- Captured `_save_checkpoint()` return value (`str`) in both debug and non-debug branches of `fit()`; zero behavioral impact on existing tests
- Added `_share_panel(export_path: str) -> None` as a module-level private function before the `DreamerV3Adapter` class; deferred all imports; wrapped in try/except; Colab detection via `import google.colab`
- Implemented `export(path: str) -> dict[str, str]`: directory creation, GIF copy, YAML config (`obs_space`, `act_space`, `checkpoint_path`), summary.txt with adapter metadata, calls `_share_panel()`; raises `AdapterError` with Got/Expected/Fix if `_triptych_path` is None
- Updated 2 stub tests in `TestDreamerV3AdapterStubs` from `NotImplementedError` → `AdapterError`
- Added `_adapter_with_triptych` fixture (stub GIF bytes, no torch/GPU required)
- Added `TestDreamerV3AdapterExport` with 14 CPU tests covering all ACs (4 additional gap-filling tests added: `test_export_returned_paths_all_exist`, `test_export_yaml_obs_space_is_json_serializable_dict`, `test_export_yaml_act_space_is_json_serializable_dict`, `test_export_summary_contains_expected_fields`)
- Full suite: 518 passed, 3 skipped, 18 deselected (no regressions); ruff: zero warnings; mkdocs build: success

### File List

- `src/physlink/adapters/dreamer.py` — modified: added `_last_checkpoint_path` in `__init__`, captured `_save_checkpoint()` return in `fit()`, added `_share_panel()` module-level function, replaced `export()` stub with full implementation
- `tests/unit/adapters/test_dreamer_cpu.py` — modified: added `from pathlib import Path` import, updated 2 stub export tests, fixed stale `TestDreamerV3AdapterStubs` docstring, added `_STUB_GIF` constant, `_adapter_with_triptych` fixture (with return type annotation), `TestDreamerV3AdapterExport` class with 14 tests

## Change Log

- 2026-05-22: Story 3.6 implemented — `export()` method and `_share_panel()` helper added to `DreamerV3Adapter`; stub tests updated; 14 new export tests added; 518 CPU tests pass, ruff clean, mkdocs clean
- 2026-05-22: Code review (AI) — fixed `export()` to return absolute paths (docstring contract); updated stale `TestDreamerV3AdapterStubs` docstring; added return type annotation to `_adapter_with_triptych` fixture; corrected test count in Completion Notes (10 → 14)
