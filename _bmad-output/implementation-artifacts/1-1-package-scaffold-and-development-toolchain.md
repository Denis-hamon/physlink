# Story 1.1: Package Scaffold and Development Toolchain

Status: done

## Story

As a developer,
I want a properly structured Python package with linting and type checking configured,
so that I can develop and publish physlink with guaranteed code quality from day one.

## Acceptance Criteria

1. **Given** a fresh checkout of the repository  
   **When** I run `python -m build` from the project root  
   **Then** a wheel and sdist are produced in `dist/` without errors

2. **And** `import physlink` from the repository root (without `pip install`) fails — the `src/` layout enforces this: no `physlink/` package exists at the root level

3. **And** `ruff check src/` passes with zero warnings

4. **And** `mypy --strict src/physlink/core/` passes with zero type errors

5. **And** a pre-commit hook runs `ruff --fix` silently on staged files before commit (`.pre-commit-config.yaml` present; `pre-commit install` can be run to activate)

## Tasks / Subtasks

- [x] Task 1: Create `pyproject.toml` (AC: #1, #3, #4)
  - [x] `[build-system]`: setuptools>=68, wheel
  - [x] `[project]`: name=physlink, version=0.1.0, python>=3.10, runtime deps
  - [x] `[tool.setuptools.packages.find]`: `where = ["src"]`
  - [x] `[tool.ruff]`: target-version=py310, line-length=100, lint rules E/F/W/I/N/UP/ANN/RUF
  - [x] `[tool.mypy]`: strict=true on core/ + per-module overrides for adapters/ and utils/
  - [x] `[tool.pytest.ini_options]`: testpaths, gpu marker declaration
  - [x] `[project.optional-dependencies]`: dev group (ruff, mypy, pytest, pytest-benchmark, pre-commit, build)

- [x] Task 2: Create `src/physlink/` package scaffold (AC: #1, #2, #3, #4)
  - [x] `src/physlink/__init__.py` — empty `__all__: list[str] = []` placeholder, no imports yet
  - [x] `src/physlink/core/__init__.py` — `from __future__ import annotations` header
  - [x] `src/physlink/core/_types.py` — stub with `from __future__ import annotations` + module docstring
  - [x] `src/physlink/core/adapter.py` — stub
  - [x] `src/physlink/core/exceptions.py` — stub
  - [x] `src/physlink/core/spaces.py` — stub
  - [x] `src/physlink/core/validation.py` — stub
  - [x] `src/physlink/adapters/__init__.py` — empty
  - [x] `src/physlink/adapters/dreamer.py` — stub
  - [x] `src/physlink/utils/__init__.py` — empty
  - [x] `src/physlink/utils/diagnostics.py` — stub
  - [x] `src/physlink/utils/visualization.py` — stub

- [x] Task 3: Create `tests/` directory scaffold (AC: #3, #4)
  - [x] `tests/conftest.py` — empty fixture file with docstring placeholder
  - [x] `tests/unit/core/` — create directory with empty `__init__.py` or leave bare (pytest discovers without it)
  - [x] `tests/unit/adapters/` — create directory
  - [x] `tests/unit/utils/` — create directory
  - [x] `tests/integration/` — create directory
  - [x] `tests/perf/baselines/benchmark_baseline.json` — empty baseline with hardware annotation
  - [x] `tests/perf/test_nfr_benchmarks.py` — stub placeholder

- [x] Task 4: Implement integration test scaffolds (AST checks) (AC: #3)
  - [x] `tests/integration/test_core_no_torch_import.py` — full AST walk: scan all `src/physlink/core/**/*.py`, fail on any torch import
  - [x] `tests/integration/test_core_boundary.py` — full AST walk: scan all `src/physlink/core/**/*.py`, fail on any import from `physlink.adapters`
  - [x] `tests/integration/test_api_stability.py` — placeholder scaffold; commented-out symbol list showing future Epic 1 symbols (`doctor`, `PhysLinkError`) to be activated by Story 1.5

- [x] Task 5: Create `.pre-commit-config.yaml` (AC: #5)
  - [x] Add ruff hook with `args: [--fix]`
  - [x] Add ruff-format hook

- [x] Task 6: Verify all ACs pass locally
  - [x] Run `python -m build` → confirm `dist/` contains `.whl` and `.tar.gz`
  - [x] Confirm `python -c "import physlink"` from repo root (without install) raises `ModuleNotFoundError`
  - [x] Run `ruff check src/` → zero issues
  - [x] Run `mypy --strict src/physlink/core/` → no errors
  - [x] Run `pre-commit run --all-files` → passes (ruff --fix is idempotent on clean stubs)

## Dev Notes

### Critical: pyproject.toml Exact Configuration

This is a **greenfield project** — no existing source files. All files are NEW.

**`pyproject.toml` required structure:**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "physlink"
version = "0.1.0"
description = "Backend-agnostic adapter library for physical simulation ML"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
dependencies = [
    "numpy>=1.24",
    "rich>=13.0",
    "matplotlib>=3.7",
    "pyyaml>=6.0",
    "safetensors>=0.4",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.4",
    "mypy>=1.9",
    "pytest>=8.0",
    "pytest-benchmark>=4.0",
    "pre-commit>=3.7",
    "build>=1.2",
    "torch",  # for adapters/ testing; excluded from core/ strict check
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
target-version = "py310"
line-length = 100
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "ANN", "RUF"]
# ANN101/102 suppress self/cls annotation warnings (irrelevant noise)
ignore = ["ANN101", "ANN102"]

[tool.mypy]
python_version = "3.10"
strict = true

[[tool.mypy.overrides]]
module = "physlink.adapters.*"
ignore_missing_imports = true
strict = false  # PyTorch stubs incomplete — ADR-002 defers to v0.3.0

[[tool.mypy.overrides]]
module = "physlink.utils.*"
ignore_missing_imports = true
# utils/ may import matplotlib/PIL which have partial stubs

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "gpu: requires CUDA GPU — excluded from test-cpu CI job (deselect with '-m not gpu')",
]
```

**Key constraint:** `[tool.setuptools.packages.find]` with `where = ["src"]` is what enforces the src/ layout and makes AC #2 work automatically. Never add `physlink/` at the repo root.

### Critical: Module Stub Content for mypy --strict

Every file in `src/physlink/core/` must start with `from __future__ import annotations`. This is a **hard rule** from architecture (NFR-08 + AR-11).

**Minimum valid stub** that passes `mypy --strict`:

```python
# src/physlink/core/_types.py
from __future__ import annotations
"""Canonical trajectory data types for PhysLink core.

Implementation in Story 2.1 (TrajectoryBatch) and Story 4.1 (AdaptationConfig, AdaptationRun).
"""
```

Do NOT add any untyped function or variable in core/ stubs — mypy --strict will flag them.
If a stub needs a placeholder class/function, annotate it fully or use a `pass` body only.

**src/physlink/__init__.py** at this stage:
```python
"""PhysLink — backend-agnostic adapter library for physical simulation ML."""

__all__: list[str] = []
# Symbols populated incrementally as epics complete:
# Epic 1: doctor, PhysLinkError (Story 1.3, 1.2)
# Epic 2: ObservationSpace, ActionSpace (Story 2.2, 2.3)
# Epic 3: DreamerV3Adapter (Story 3.1)
# Epic 4: register_invariant, ComplianceReport (Story 4.3, 4.4)
```

### Critical: AST Integration Tests — Full Implementations

Both AST tests MUST be fully implemented in this story (not stubs). They scan the scaffold files immediately and will pass on empty/stub-only modules.

**`tests/integration/test_core_no_torch_import.py`:**
```python
"""AST guard: no torch import in src/physlink/core/.

Enforces NFR-08 (backend-agnostic core). Runs in test-cpu CI — no GPU required.
"""
from __future__ import annotations

import ast
from pathlib import Path


def get_core_files() -> list[Path]:
    core_dir = Path(__file__).parent.parent.parent / "src" / "physlink" / "core"
    return list(core_dir.rglob("*.py"))


def test_no_torch_import_in_core() -> None:
    torch_imports: list[str] = []
    for filepath in get_core_files():
        tree = ast.parse(filepath.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "torch" or alias.name.startswith("torch."):
                        torch_imports.append(f"{filepath}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and (
                    node.module == "torch" or node.module.startswith("torch.")
                ):
                    torch_imports.append(f"{filepath}: from {node.module} import ...")
    assert not torch_imports, (
        f"torch imports found in core/ (violates NFR-08):\n"
        + "\n".join(torch_imports)
    )
```

**`tests/integration/test_core_boundary.py`:**
```python
"""AST guard: core/ must not import from physlink.adapters/.

Enforces architectural boundary. BOUNDARY_EXCEPTIONS list is audited on every review.
"""
from __future__ import annotations

import ast
from pathlib import Path

BOUNDARY_EXCEPTIONS: list[str] = []  # explicit empty list — reviewed each PR


def get_core_files() -> list[Path]:
    core_dir = Path(__file__).parent.parent.parent / "src" / "physlink" / "core"
    return list(core_dir.rglob("*.py"))


def test_core_does_not_import_adapters() -> None:
    violations: list[str] = []
    for filepath in get_core_files():
        tree = ast.parse(filepath.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("physlink.adapters"):
                    key = f"{filepath}:{module}"
                    if key not in BOUNDARY_EXCEPTIONS:
                        violations.append(f"{filepath}: from {module} import ...")
    assert not violations, (
        "core/ → adapters/ boundary violated:\n" + "\n".join(violations)
    )
```

**`tests/integration/test_api_stability.py` (scaffold for Story 1.5):**
```python
"""API stability contract — verifies physlink.__all__ surface.

This test is intentionally minimal at Epic 1 stage. It will be activated
incrementally by each epic's final story (Story 1.5 adds 2 symbols, Story 2.6
adds 4, Story 4.5 finalizes all 7).
"""
from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Activated by Story 1.5 once doctor and PhysLinkError are implemented")
def test_epic1_api_symbols() -> None:
    import physlink  # noqa: PLC0415

    expected = {"doctor", "PhysLinkError"}
    actual = set(physlink.__all__)
    assert expected.issubset(actual), (
        f"Missing Epic 1 symbols: {expected - actual}"
    )
```

### Critical: pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.10  # Pin to stable ruff version
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Usage: `pre-commit install` once after checkout. Then `ruff --fix` runs silently on every `git commit`.
Blocking in CI from v0.2.0 (ADR-001 decision) — not blocking in v0.1.x PRs.

### Critical: benchmark_baseline.json Hardware Annotation

```json
{
  "hardware": "T4 GPU",
  "generated_by": "physlink maintainer",
  "note": "Baseline generated on Tesla T4 GPU. Do NOT compare against A100, H100, or other hardware — benchmarks are not portable across GPU generations.",
  "benchmarks": []
}
```

Path: `tests/perf/baselines/benchmark_baseline.json`. This file is committed to the repo. Story 1.4 wires it into pytest-benchmark configuration.

### Architecture Boundaries This Story Must Respect

| Rule | Enforcement |
|------|-------------|
| `src/` layout — no `physlink/` at repo root | `[tool.setuptools.packages.find] where = ["src"]` |
| `from __future__ import annotations` in all `core/` files | Checked by mypy --strict |
| No torch import in `core/` | `test_core_no_torch_import.py` |
| No `core/` → `adapters/` imports | `test_core_boundary.py` |
| Naming: snake_case functions/vars, PascalCase classes | ruff rule N |
| `X \| Y` not `Union[X, Y]` | ruff rule UP (pyupgrade) |

### Implementation Sequence (within this story)

1. `pyproject.toml` first — build system anchors everything
2. `src/physlink/__init__.py` + package scaffold second
3. `tests/conftest.py` + directory structure third
4. AST integration tests fourth (they need the src/ structure to discover files)
5. `.pre-commit-config.yaml` last
6. Verify all 5 ACs locally before marking done

### What NOT to implement in this story

- Any actual class or function implementation — only stubs/docstrings
- `physlink.doctor()` — Story 1.3
- Exception hierarchy content — Story 1.2
- Any GitHub Actions workflow — Story 1.4
- README badges — Story 1.6
- `__init__.py` imports — subsequent stories populate these as symbols are implemented
- `TrajectoryBatch`, `ObservationSpace`, etc. — their respective stories

### Project Structure Notes

- Alignment with canonical architecture structure [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- No conflicts with upstream stories (this IS the first story)
- Tests directories do NOT need `__init__.py` for pytest discovery — bare directories work
- `tests/unit/core/`, `tests/unit/adapters/`, `tests/unit/utils/` can be created empty with just a `.gitkeep` — real test files come in their respective stories

### References

- Architecture ADR-001 (Build Tooling): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-001: Build Tooling & Package Management]
- Architecture Structure Patterns: [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns]
- Architecture Naming Patterns: [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns]
- Architecture Enforcement Guidelines: [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- AR-01 (src/ layout), AR-02 (ruff + mypy), AR-08 (AST tests): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- NFR-08 (backend-agnostic core): [Source: _bmad-output/planning-artifacts/epics.md#NonFunctional Requirements]
- Story 1.4 depends on test scaffold from this story: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4]
- Story 1.5 activates test_api_stability.py Epic 1 guard: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- **Dev Notes error**: `setuptools.backends.legacy:build` doesn't exist in setuptools <=82. Used `setuptools.build_meta` (standard backend) instead.
- **ruff ANN101/ANN102**: Removed from ignore list — rules were removed in ruff >=0.4 and caused a warning. No functional impact.
- **ruff I001 on stubs**: Module docstrings must come before `from __future__ import annotations`. Fixed all core/ stubs to: docstring → blank line → `from __future__`.
- **pre-commit scope**: `.agents/` BMAD framework files don't comply with physlink's strict ruff config. Added exclusions in `[tool.ruff] exclude` for `.agents`, `.claude`, `_bmad`, `_bmad-output`, `.venv`, `dist`, `build`.
- **git init**: Worldchain directory had no git repo; `git init` was required for pre-commit to discover files.

### Completion Notes List

- Created full pyproject.toml with build-system, project metadata, optional-dependencies, ruff, mypy, pytest config (all tasks 1.x ✅)
- Created 12 source stubs in `src/physlink/` — all core/ files pass `mypy --strict`, `ruff --strict` ✅
- Created tests/ scaffold: conftest, 3 unit subdirs (.gitkeep), integration/ dir, perf/ dir + benchmark JSON ✅
- Implemented 2 full AST integration tests (no torch in core/, no adapters import in core/) — both passing ✅
- `test_api_stability.py` scaffold with `@pytest.mark.skip` — activated by Story 1.5 ✅
- Created `.pre-commit-config.yaml` with ruff + ruff-format hooks ✅
- All 5 ACs verified locally: build ✅, import fails ✅, ruff clean ✅, mypy clean ✅, pre-commit clean ✅

### Senior Developer Review (AI)

**Reviewer:** Denis | **Date:** 2026-05-21

**Verdict:** ✅ Approved — 0 critical issues, 3 medium fixed, 1 low fixed

#### Issues Fixed Automatically

| # | Severity | File | Issue | Fix Applied |
|---|----------|------|-------|-------------|
| 1 | MEDIUM | Story File List | `test_toolchain_compliance.py` created by dev agent but not documented | Added to File List |
| 2 | MEDIUM | `tests/integration/test_toolchain_compliance.py:37-46` | `TestRuffCompliance.test_ruff_reports_no_issues` was identical to `test_ruff_check_passes` (same subprocess, same returncode check) | Removed redundant test |
| 3 | MEDIUM | `tests/integration/test_toolchain_compliance.py:54-77` | `TestMypyCompliance.test_mypy_reports_no_errors` ran same subprocess as `test_mypy_strict_on_core_passes` with overlapping assertions | Removed redundant test |
| 4 | LOW | `tests/integration/test_toolchain_compliance.py:149` | `import os` inside `_clean_env()` body instead of module top-level | Moved to module imports |

#### AC Validation

| AC | Status | Evidence |
|----|--------|----------|
| #1 `python -m build` → dist/ | ✅ IMPLEMENTED | pyproject.toml valid; Task 6 local verification; `TestBuildSystemConfig` tests package discovery |
| #2 bare `import physlink` fails | ✅ IMPLEMENTED | `[tool.setuptools.packages.find] where=["src"]` enforced; `TestSrcLayoutEnforcement` tests programmatically |
| #3 `ruff check src/` → zero issues | ✅ IMPLEMENTED | ruff config correct; `TestRuffCompliance` tests programmatically |
| #4 `mypy --strict src/physlink/core/` → no errors | ✅ IMPLEMENTED | All core/ stubs have `from __future__ import annotations`; `TestMypyCompliance` tests programmatically |
| #5 `.pre-commit-config.yaml` with ruff --fix | ✅ IMPLEMENTED | File present with ruff + ruff-format hooks pinned at v0.4.10 |

### File List

- `pyproject.toml`
- `README.md`
- `.pre-commit-config.yaml`
- `src/physlink/__init__.py`
- `src/physlink/core/__init__.py`
- `src/physlink/core/_types.py`
- `src/physlink/core/adapter.py`
- `src/physlink/core/exceptions.py`
- `src/physlink/core/spaces.py`
- `src/physlink/core/validation.py`
- `src/physlink/adapters/__init__.py`
- `src/physlink/adapters/dreamer.py`
- `src/physlink/utils/__init__.py`
- `src/physlink/utils/diagnostics.py`
- `src/physlink/utils/visualization.py`
- `tests/conftest.py`
- `tests/unit/core/.gitkeep`
- `tests/unit/adapters/.gitkeep`
- `tests/unit/utils/.gitkeep`
- `tests/integration/.gitkeep`
- `tests/integration/test_core_no_torch_import.py`
- `tests/integration/test_core_boundary.py`
- `tests/integration/test_api_stability.py`
- `tests/integration/test_toolchain_compliance.py`
- `tests/perf/baselines/benchmark_baseline.json`
- `tests/perf/test_nfr_benchmarks.py`
