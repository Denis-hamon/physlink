# Story 1.3: physlink.doctor() Diagnostic Scan

Status: done

## Story

As a researcher,
I want to run `physlink.doctor()` and get a Go/No-Go verdict in under 15 seconds,
so that I know immediately whether my environment is ready for DreamerV3 adaptation before spending time on setup.

## Acceptance Criteria

1. **Given** a Colab T4 session with GPU enabled  
   **When** I run `physlink.doctor()`  
   **Then** all checks complete end-to-end in < 15 seconds (NFR-01)  
   **And** output displays a structured table with rows for: Python version, PyTorch presence, CUDA availability, VRAM, Colab session estimate  
   **And** each row shows `[OK]`, `[WARN]`, or `[FAIL]` as text labels (no color-only signaling — NFR-12)  
   **And** a GO verdict is displayed as a distinct callout block (UX-DR-03)

2. **Given** a CPU-only Colab runtime (no GPU)  
   **When** I run `physlink.doctor()`  
   **Then** a NO-GO verdict is displayed  
   **And** exactly one actionable fix is shown: a GPU upgrade instruction

3. **Given** a GPU runtime with less than 4 GB VRAM available  
   **When** I run `physlink.doctor()`  
   **Then** the VRAM row shows `[WARN]`  
   **And** one memory optimization suggestion is displayed alongside the WARN

## Tasks / Subtasks

- [x] Task 1: Implement `src/physlink/utils/diagnostics.py` (AC: #1, #2, #3)
  - [x] Replace stub with full implementation: `DiagnosticReport` dataclass, `CheckResult` dataclass, `doctor()` function
  - [x] Implement 5 check functions: `_check_python_version`, `_check_torch_presence`, `_check_cuda_availability`, `_check_vram`, `_check_colab_session`
  - [x] Dynamic torch detection (NEVER import torch at module level — use `importlib.util.find_spec` + conditional dynamic import)
  - [x] GO/NO-GO verdict: any FAIL → NO-GO; otherwise GO
  - [x] Output: formatted table with `[OK]`/`[WARN]`/`[FAIL]` text labels + distinct GO callout block
  - [x] Track and include `elapsed_seconds` in returned `DiagnosticReport`
  - [x] Wrap all checks in try/except to prevent one failing check from crashing the full diagnostic
  - [x] Module docstring FIRST, then `from __future__ import annotations` (ruff I001 ordering rule)
  - [x] Google-style docstring with Args/Raises/Example on `doctor()`

- [x] Task 2: Update `src/physlink/__init__.py` (AC: #1)
  - [x] Add import: `from physlink.utils.diagnostics import doctor`
  - [x] Add `"doctor"` to `__all__` list (keep all existing comments for Story 2–4 symbols)

- [x] Task 3: Create `tests/unit/utils/test_diagnostics.py` (AC: #1, #2, #3)
  - [x] Test `doctor()` returns a `DiagnosticReport` with `checks`, `verdict`, `elapsed_seconds`
  - [x] Test all 5 check names are present in the report
  - [x] Test output text contains literal `[OK]`, `[WARN]`, or `[FAIL]` strings (text label enforcement)
  - [x] Test GO verdict when all checks pass (mock torch + CUDA available)
  - [x] Test NO-GO verdict when CUDA is not available (mock `torch.cuda.is_available()` → False)
  - [x] Test WARN status when VRAM < 4 GB (mock VRAM = 3.5 GB)
  - [x] Test `elapsed_seconds` is a non-negative float
  - [x] Test `doctor()` completes in < 15 seconds on CPU (no GPU required — timed assertion)
  - [x] Test `doctor()` does NOT raise when torch is not installed (mock `importlib.util.find_spec("torch")` → None)

- [x] Task 4: Verify all ACs
  - [x] `ruff check src/physlink/utils/diagnostics.py` → zero issues
  - [x] `mypy --strict src/physlink/core/` → still zero errors (diagnostics.py is in utils/, not core/)
  - [x] `pytest tests/unit/utils/test_diagnostics.py -v` → all pass
  - [x] `pytest tests/integration/test_core_no_torch_import.py` → still passes (diagnostics.py is in utils/, not core/ — AST check only covers core/)
  - [x] `pytest tests/integration/test_core_boundary.py` → still passes
  - [x] `pytest tests/integration/test_api_stability.py` → still 1 skipped (DO NOT remove `@pytest.mark.skip`)

## Dev Notes

### File: `src/physlink/utils/diagnostics.py` — Full Implementation

**Current state:** stub with only module docstring. Replace entirely.

**Critical constraint: ZERO torch import at module level.** `import physlink` must succeed on a machine without PyTorch. Torch must be detected dynamically at runtime inside the check functions.

**Allowed imports in this file:**
- stdlib: `importlib.util`, `platform`, `sys`, `time`, `os`, `dataclasses`, `typing`
- physlink: `from physlink.core.exceptions import PhysLinkError` (only this — no adapters, no spaces)

**Forbidden imports in this file:**
- `import torch` at module level (breaks non-GPU environments)
- `from physlink.adapters import ...` (architectural boundary: utils → adapters forbidden)
- Any non-stdlib, non-physlink.core.exceptions import

```python
"""PhysLink diagnostics — doctor() entry point.

Zero ML dependencies at module level: safe to call even when PyTorch is
not installed. Torch is detected dynamically at runtime inside check functions.
"""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
import time
from dataclasses import dataclass, field
from typing import Literal


CheckStatus = Literal["OK", "WARN", "FAIL"]


@dataclass
class CheckResult:
    """Result of a single diagnostic check.

    Attributes:
        name: Human-readable check name shown in the diagnostic table.
        status: "OK", "WARN", or "FAIL" — always a text label (NFR-12).
        value: Detected value or description to display alongside the status.
        fix: Actionable instruction shown only for WARN and FAIL results.
    """

    name: str
    status: CheckStatus
    value: str
    fix: str = ""


@dataclass
class DiagnosticReport:
    """Complete diagnostic report returned by physlink.doctor().

    Attributes:
        checks: Ordered list of CheckResult for all 5 diagnostic checks.
        verdict: "GO" if no FAIL; "NO-GO" if any check is FAIL.
        elapsed_seconds: Wall-clock time for the full diagnostic run.
    """

    checks: list[CheckResult] = field(default_factory=list)
    verdict: Literal["GO", "NO-GO"] = "GO"
    elapsed_seconds: float = 0.0


def _check_python_version() -> CheckResult:
    """Check Python version is >= 3.10 (physlink minimum requirement)."""
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    if version_info >= (3, 10):
        return CheckResult(
            name="Python version",
            status="OK",
            value=f"{version_str} (required: >=3.10)",
        )
    return CheckResult(
        name="Python version",
        status="FAIL",
        value=f"{version_str}",
        fix="Upgrade to Python 3.10 or later.",
    )


def _check_torch_presence() -> tuple[CheckResult, object | None]:
    """Check if PyTorch is installed. Returns (CheckResult, torch_module | None).

    Uses importlib.util.find_spec to avoid ImportError when torch is absent.
    Dynamically imports torch only if find_spec confirms it is installed.
    """
    spec = importlib.util.find_spec("torch")
    if spec is None:
        return CheckResult(
            name="PyTorch presence",
            status="FAIL",
            value="Not found",
            fix="Install PyTorch: pip install torch  (see https://pytorch.org/get-started/)",
        ), None

    try:
        import importlib as _il
        torch = _il.import_module("torch")
        version = getattr(torch, "__version__", "unknown")
        return CheckResult(
            name="PyTorch presence",
            status="OK",
            value=version,
        ), torch
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            name="PyTorch presence",
            status="FAIL",
            value=f"Import failed: {exc}",
            fix="Reinstall PyTorch: pip install --force-reinstall torch",
        ), None


def _check_cuda_availability(torch: object | None) -> CheckResult:
    """Check CUDA availability via dynamically-imported torch module."""
    if torch is None:
        return CheckResult(
            name="CUDA availability",
            status="FAIL",
            value="N/A (PyTorch not installed)",
            fix="Install PyTorch first: pip install torch",
        )
    try:
        cuda_available = torch.cuda.is_available()  # type: ignore[union-attr]
        if not cuda_available:
            return CheckResult(
                name="CUDA availability",
                status="FAIL",
                value="No GPU detected",
                fix=(
                    "Enable GPU runtime in Colab: "
                    "Runtime > Change runtime type > T4 GPU."
                ),
            )
        device_count = torch.cuda.device_count()  # type: ignore[union-attr]
        cuda_version = getattr(torch.version, "cuda", "unknown")  # type: ignore[union-attr]
        return CheckResult(
            name="CUDA availability",
            status="OK",
            value=f"CUDA {cuda_version} ({device_count} device(s))",
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            name="CUDA availability",
            status="FAIL",
            value=f"Error: {exc}",
            fix="Enable GPU runtime in Colab: Runtime > Change runtime type > T4 GPU.",
        )


def _check_vram(torch: object | None) -> CheckResult:
    """Check VRAM: WARN if < 4 GB, OK if >= 4 GB. N/A if CUDA unavailable."""
    if torch is None:
        return CheckResult(
            name="VRAM",
            status="FAIL",
            value="N/A (PyTorch not installed)",
            fix="Install PyTorch first: pip install torch",
        )
    try:
        if not torch.cuda.is_available():  # type: ignore[union-attr]
            return CheckResult(
                name="VRAM",
                status="FAIL",
                value="N/A (no GPU)",
                fix="Enable GPU runtime in Colab: Runtime > Change runtime type > T4 GPU.",
            )
        props = torch.cuda.get_device_properties(0)  # type: ignore[union-attr]
        total_gb = props.total_memory / (1024 ** 3)
        device_name = props.name
        if total_gb < 4.0:
            return CheckResult(
                name="VRAM",
                status="WARN",
                value=f"{total_gb:.1f} GB ({device_name})",
                fix=(
                    f"Low VRAM ({total_gb:.1f} GB < 4 GB). "
                    "Reduce batch size or enable gradient checkpointing."
                ),
            )
        return CheckResult(
            name="VRAM",
            status="OK",
            value=f"{total_gb:.1f} GB ({device_name})",
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            name="VRAM",
            status="WARN",
            value=f"Could not read: {exc}",
            fix="Check GPU availability and torch installation.",
        )


def _check_colab_session() -> CheckResult:
    """Detect Colab environment via google.colab import or COLAB_BACKEND_VERSION env var."""
    in_colab = (
        "COLAB_BACKEND_VERSION" in os.environ
        or importlib.util.find_spec("google.colab") is not None
    )
    if in_colab:
        return CheckResult(
            name="Colab session",
            status="OK",
            value="Google Colab detected",
        )
    return CheckResult(
        name="Colab session",
        status="WARN",
        value="Not in Colab (local or other environment)",
        fix=(
            "physlink is optimized for Google Colab T4. "
            "Local GPU environments are supported but untested."
        ),
    )


def doctor() -> DiagnosticReport:
    """Run a Go/No-Go environment diagnostic and print a structured report.

    Checks Python version, PyTorch presence, CUDA availability, VRAM, and
    Colab session — all without requiring torch at module import time.

    Returns:
        DiagnosticReport with ordered checks, verdict ("GO" or "NO-GO"),
        and elapsed_seconds.

    Example:
        >>> report = physlink.doctor()
        >>> report.verdict
        'GO'
        >>> report.checks[0].status
        'OK'
    """
    start = time.monotonic()

    torch_result, torch_module = _check_torch_presence()
    checks = [
        _check_python_version(),
        torch_result,
        _check_cuda_availability(torch_module),
        _check_vram(torch_module),
        _check_colab_session(),
    ]

    verdict: Literal["GO", "NO-GO"] = (
        "NO-GO" if any(c.status == "FAIL" for c in checks) else "GO"
    )

    elapsed = time.monotonic() - start
    report = DiagnosticReport(checks=checks, verdict=verdict, elapsed_seconds=elapsed)

    _print_report(report)
    return report


def _print_report(report: DiagnosticReport) -> None:
    """Print the formatted diagnostic table to stdout."""
    separator = "=" * 52
    print(f"\nphyslink.doctor() — Environment Diagnostic")
    print(separator)

    name_width = max(len(c.name) for c in report.checks) + 2
    for check in report.checks:
        label = f"[{check.status}]"
        print(f"  {check.name:<{name_width}} {label:<8} {check.value}")

    print(separator)

    if report.verdict == "GO":
        print("  ** GO — Environment ready for PhysLink **")
        warnings = [c for c in report.checks if c.status == "WARN"]
        if warnings:
            print()
            for w in warnings:
                print(f"  Warning: {w.fix}")
    else:
        print("  ** NO-GO **")
        print()
        fails = [c for c in report.checks if c.status == "FAIL"]
        for f in fails:
            print(f"  Fix: {f.name} — {f.fix}")

    print(f"\n  ({report.elapsed_seconds:.1f}s)")
    print()


__all__ = ["DiagnosticReport", "CheckResult", "doctor"]
```

### File: `src/physlink/__init__.py` — Add `doctor`

**Current state (after Story 1.2):**
```python
"""PhysLink — backend-agnostic adapter library for physical simulation ML."""

from physlink.core.exceptions import PhysLinkError

__all__ = [
    "PhysLinkError",
    # Story 1.3: doctor
    ...
]
```

**Update to:**
```python
"""PhysLink — backend-agnostic adapter library for physical simulation ML."""

from physlink.core.exceptions import PhysLinkError
from physlink.utils.diagnostics import doctor

__all__ = [
    "PhysLinkError",
    "doctor",
    # Story 2.2/2.3: ObservationSpace, ActionSpace
    # Story 3.1: DreamerV3Adapter
    # Story 4.3/4.4: register_invariant, ComplianceReport
]
```

**Critical:** `doctor` added. Remove the `# Story 1.3: doctor` comment placeholder and replace with the actual import + list entry. Keep all other story comment placeholders intact.

### File: `tests/unit/utils/test_diagnostics.py` — New Test File

Currently only a `.gitkeep` exists in `tests/unit/utils/`. Create the full test file.

```python
"""Unit tests for physlink.utils.diagnostics — doctor() function."""

from __future__ import annotations

import time
import types
from unittest.mock import MagicMock, patch

import pytest

from physlink.utils.diagnostics import CheckResult, DiagnosticReport, doctor


class TestDiagnosticReportStructure:
    def test_doctor_returns_diagnostic_report(self) -> None:
        report = doctor()
        assert isinstance(report, DiagnosticReport)

    def test_report_has_five_checks(self) -> None:
        report = doctor()
        assert len(report.checks) == 5

    def test_check_names_are_expected(self) -> None:
        report = doctor()
        names = [c.name for c in report.checks]
        assert "Python version" in names
        assert "PyTorch presence" in names
        assert "CUDA availability" in names
        assert "VRAM" in names
        assert "Colab session" in names

    def test_check_results_are_check_result_instances(self) -> None:
        report = doctor()
        for check in report.checks:
            assert isinstance(check, CheckResult)

    def test_elapsed_seconds_is_non_negative(self) -> None:
        report = doctor()
        assert report.elapsed_seconds >= 0.0

    def test_verdict_is_go_or_no_go(self) -> None:
        report = doctor()
        assert report.verdict in ("GO", "NO-GO")


class TestCheckStatusValues:
    def test_all_statuses_are_valid_literals(self) -> None:
        report = doctor()
        for check in report.checks:
            assert check.status in ("OK", "WARN", "FAIL"), (
                f"Check '{check.name}' has invalid status: {check.status!r}"
            )

    def test_output_contains_text_labels(self, capsys: pytest.CaptureFixture[str]) -> None:
        doctor()
        captured = capsys.readouterr()
        # At least one text label must appear in output (NFR-12 — no color-only)
        assert any(label in captured.out for label in ("[OK]", "[WARN]", "[FAIL]"))


class TestVerdictLogic:
    def test_no_go_when_cuda_unavailable(self, capsys: pytest.CaptureFixture[str]) -> None:
        """CPU-only environment must produce NO-GO verdict (UX-DR-03)."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = False

        with patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()), \
             patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch):
            report = doctor()

        assert report.verdict == "NO-GO"
        cuda_check = next(c for c in report.checks if c.name == "CUDA availability")
        assert cuda_check.status == "FAIL"

    def test_no_go_output_contains_fix(self, capsys: pytest.CaptureFixture[str]) -> None:
        """NO-GO must display exactly one actionable fix for CUDA failure."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = False

        with patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()), \
             patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch):
            doctor()

        captured = capsys.readouterr()
        assert "NO-GO" in captured.out
        assert "Fix:" in captured.out

    def test_go_when_gpu_available(self) -> None:
        """Full GPU environment must produce GO verdict."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.version.cuda = "12.1"
        mock_props = MagicMock()
        mock_props.total_memory = 16 * 1024 ** 3  # 16 GB
        mock_props.name = "Tesla T4"
        mock_torch.cuda.get_device_properties.return_value = mock_props

        with patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()), \
             patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch):
            report = doctor()

        assert report.verdict == "GO"


class TestWarnOnLowVram:
    def test_warn_when_vram_below_4gb(self) -> None:
        """VRAM < 4 GB must produce WARN status (UX-DR-03, AC #3)."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.version.cuda = "11.8"
        mock_props = MagicMock()
        mock_props.total_memory = int(3.5 * 1024 ** 3)  # 3.5 GB
        mock_props.name = "Tesla T4"
        mock_torch.cuda.get_device_properties.return_value = mock_props

        with patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()), \
             patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch):
            report = doctor()

        vram_check = next(c for c in report.checks if c.name == "VRAM")
        assert vram_check.status == "WARN"
        assert vram_check.fix != "", "Low VRAM WARN must include a fix suggestion"

    def test_warn_fix_mentions_memory_optimization(self) -> None:
        """VRAM < 4 GB fix message must mention memory optimization."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.version.cuda = "11.8"
        mock_props = MagicMock()
        mock_props.total_memory = int(3.5 * 1024 ** 3)
        mock_props.name = "Tesla T4"
        mock_torch.cuda.get_device_properties.return_value = mock_props

        with patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()), \
             patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch):
            report = doctor()

        vram_check = next(c for c in report.checks if c.name == "VRAM")
        fix_lower = vram_check.fix.lower()
        assert "batch" in fix_lower or "gradient" in fix_lower or "memory" in fix_lower


class TestTorchNotInstalled:
    def test_no_crash_when_torch_absent(self) -> None:
        """doctor() must not raise when PyTorch is not installed."""
        with patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=None):
            try:
                report = doctor()
            except Exception as exc:
                pytest.fail(f"doctor() raised unexpectedly when torch is absent: {exc}")

        torch_check = next(c for c in report.checks if c.name == "PyTorch presence")
        assert torch_check.status == "FAIL"
        assert report.verdict == "NO-GO"


class TestPerformance:
    def test_doctor_completes_within_15_seconds(self) -> None:
        """NFR-01: doctor() must complete in < 15 seconds."""
        start = time.monotonic()
        doctor()
        elapsed = time.monotonic() - start
        assert elapsed < 15.0, f"doctor() took {elapsed:.1f}s (limit: 15s, NFR-01)"
```

### Architecture Boundaries This Story Must Respect

| Rule | How to comply |
|------|--------------|
| `utils/diagnostics.py` has ZERO ML imports at module level | Never write `import torch` at module level — use `importlib.util.find_spec` + dynamic import |
| `utils/ → adapters/` boundary is forbidden | diagnostics.py only imports stdlib + `physlink.core.exceptions` |
| `from __future__ import annotations` in core/ files | diagnostics.py is in utils/ — this rule applies to core/ only; adding it to utils/ is still good practice |
| Got/Expected/Fix template for error messages | N/A: doctor() doesn't raise PhysLink errors, it reports them as CheckResult |
| `X | Y` union syntax | Use `object | None` for torch module parameter type |
| Google-style docstrings | doctor(), DiagnosticReport, CheckResult must have Args/Example sections |
| `src/` layout | All files stay under `src/physlink/utils/` |

### What NOT to implement in this story

- pytest-benchmark integration for NFR-01 — Story 1.4 sets up the CI pipeline and benchmark wiring
- GitHub Actions CI jobs — Story 1.4
- Removal of `@pytest.mark.skip` from `test_api_stability.py` — Story 1.5 activates this guard
- Any changes to `test_core_no_torch_import.py` — AST checks only cover `core/`, not `utils/`
- `physlink.doctor()` CLI entry point — not specified in Epic 1 stories
- `AdaptationConfig`, `TrajectoryBatch`, or other types from other epics

### Previous Story Intelligence (Stories 1.1 and 1.2)

Critical learnings carried forward:

- **Module docstring order**: docstring FIRST, then blank line, then `from __future__ import annotations` — ruff I001 enforces this ordering. Violating it causes a linting error.
- **ruff ANN101/ANN102**: these rules were removed in ruff >=0.4 — do not reference them.
- **setuptools backend**: `setuptools.build_meta` (not `setuptools.backends.legacy:build`).
- **ruff exclude**: `.agents/`, `.claude/`, `_bmad/`, `_bmad-output/` are excluded in `pyproject.toml` — never create stub files there.
- **`tests/unit/utils/` contains only `.gitkeep`**: create `test_diagnostics.py` directly in that directory, no `__init__.py` needed.
- **`test_api_stability.py` skip intact**: the skip decorator was introduced in Story 1.1 and must NOT be removed until Story 1.5. After Story 1.3, `physlink.__all__` will contain `["PhysLinkError", "doctor"]` — the test is ready to pass, but the decorator must stay.
- **mypy strict on core/ only**: `mypy --strict src/physlink/core/` — diagnostics.py is in `utils/`, so it is NOT checked by mypy strict. Do not add it to the mypy strict path.
- **`test_all_contains_physlink_error` in `test_package_scaffold.py`**: this test uses `"PhysLinkError" in exported` — adding `"doctor"` to `__all__` does not break it (it's an inclusion check, not equality).

### Git Intelligence

Last commit: `feat(story-1.2): Exception Hierarchy Foundation`

Key patterns established in Story 1.2:
- Commit message format: `feat(story-X.Y): Short Description`
- All `core/` files have `from __future__ import annotations` as first non-docstring line
- Tests are organized under `tests/unit/core/` mirroring `src/physlink/core/`
- Test class structure: `class TestSomeTopic:` wrapping related test methods
- No `__init__.py` needed in test subdirectories (pytest discovers by path)

### Project Structure Notes

Files to create/modify in this story:

| File | Action | Notes |
|------|--------|-------|
| `src/physlink/utils/diagnostics.py` | UPDATE (full replace of stub) | Core implementation |
| `src/physlink/__init__.py` | UPDATE (add doctor import + __all__ entry) | Remove comment placeholder, add real import |
| `tests/unit/utils/test_diagnostics.py` | NEW (replace .gitkeep pattern) | Full test suite |

Files that MUST NOT be touched:
- `pyproject.toml` — no new deps needed (`importlib`, `os`, `time` are stdlib)
- `tests/integration/test_core_no_torch_import.py` — must still pass (checks `core/` only)
- `tests/integration/test_core_boundary.py` — must still pass
- `tests/integration/test_api_stability.py` — keep `@pytest.mark.skip` intact
- `tests/unit/test_package_scaffold.py` — must still pass (uses `in` not `==` for `__all__` check)
- `src/physlink/core/exceptions.py` — do not touch

### References

- FR-01 (`physlink.doctor()` spec): [Source: _bmad-output/planning-artifacts/epics.md#Functional Requirements]
- NFR-01 (< 15s execution): [Source: _bmad-output/planning-artifacts/epics.md#NonFunctional Requirements]
- NFR-12 (text labels, no color-only): [Source: _bmad-output/planning-artifacts/epics.md#NonFunctional Requirements]
- UX-DR-03 (GO/NO-GO callout, VRAM WARN): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- Architecture utils/diagnostics.py placement: [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- Architecture critical rule for doctor(): [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries — `utils/diagnostics → (rien) — Zéro dépendance ML`]
- Architecture Category 3 (doctor in __init__): [Source: _bmad-output/planning-artifacts/architecture.md#Category 3 — Module Public API Surface]
- Implementation sequence (doctor is step 7): [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Handoff]
- Story 1.1 Dev Agent Record (toolchain patterns): [Source: _bmad-output/implementation-artifacts/1-1-package-scaffold-and-development-toolchain.md#Dev Agent Record]
- Story 1.2 Dev Agent Record (module docstring order, ruff rules): [Source: _bmad-output/implementation-artifacts/1-2-exception-hierarchy-foundation.md#Dev Notes]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `importlib.util.find_spec("google.colab")` raises `ModuleNotFoundError` when the `google` namespace package is absent (Python 3.12 local env). Fixed with try/except wrapping in `_check_colab_session()`. The spec in the story Dev Notes does not mention this edge case, but it is mandatory for robustness on any non-Colab environment.

### Completion Notes List

- Implemented full `diagnostics.py` replacing stub: `CheckResult`, `DiagnosticReport` dataclasses + `doctor()` + 5 check functions + `_print_report()`. Zero ML imports at module level — torch loaded dynamically via `importlib.import_module` only when `find_spec` confirms it is installed.
- `_check_colab_session()` guards `find_spec("google.colab")` inside try/except to handle the `ModuleNotFoundError` raised in environments where the `google` namespace package does not exist.
- `src/physlink/__init__.py` updated: `doctor` imported from `utils.diagnostics`, added to `__all__`, placeholder comment `# Story 1.3: doctor` removed, all other story placeholders preserved.
- 24/24 unit tests pass (23 original + 1 added by AI review for AC #2 "exactly one fix"). All 3 integration tests pass (2 pass + 1 skipped as expected). ruff → 0 issues. mypy --strict on core/ → 0 issues.

### File List

- src/physlink/utils/diagnostics.py (modified — full implementation replacing stub)
- src/physlink/__init__.py (modified — added doctor import and __all__ entry)
- tests/unit/utils/test_diagnostics.py (created — 15 unit tests)

## Senior Developer Review (AI)

**Reviewer:** AI Code Reviewer (claude-sonnet-4-6) — 2026-05-22

**Verdict:** APPROVED with auto-fixes applied (0 CRITICAL, 3 MEDIUM fixed, 1 LOW fixed)

### Issues Found and Fixed

**🟡 MEDIUM — AC #2 violation: "exactly one actionable fix"** (FIXED)
- `_check_vram` returned `FAIL` when `torch.cuda.is_available()` was False, causing 2 "Fix:" lines in NO-GO output — contradicting AC #2 ("exactly one actionable fix: GPU upgrade").
- Fix: Changed `_check_vram` no-CUDA branch from `status="FAIL"` to `status="WARN"` with `fix=""`. The GPU upgrade fix is already surfaced via `_check_cuda_availability`.
- Added test `test_no_go_shows_exactly_one_fix_when_cuda_unavailable` to enforce AC #2 going forward.
- Files: `src/physlink/utils/diagnostics.py`, `tests/unit/utils/test_diagnostics.py`

**🟡 MEDIUM — Completion notes inaccuracy: "15/15 unit tests"** (FIXED)
- Dev Agent Record stated "15/15 unit tests pass" but the file contained 23 tests (8 additional edge-case tests beyond spec).
- Fix: Updated completion notes to "24/24 unit tests pass" (23 original + 1 added by review).

**🟡 MEDIUM — Pre-existing failures in `test_toolchain_compliance.py`** (DOCUMENTED, not caused by Story 1.3)
- `TestSrcLayoutEnforcement` (2 tests) fail because physlink is installed as editable in .venv — `_clean_env()` removes PYTHONPATH but not the venv's editable install link.
- Story 1.3 did not introduce these failures (created in Story 1.2). Task 4 correctly omitted these tests from claims.

**🟢 LOW — Redundant `import importlib as _il` inside function** (FIXED)
- `_check_torch_presence()` used an inner `import importlib as _il` alias. After module-level `import importlib.util`, `importlib.import_module` is already accessible directly.
- Fix: Replaced `_il.import_module("torch")` with `importlib.import_module("torch")`. Test mocks still work (both reference the same `importlib` object).

### Post-fix Verification
- `ruff check src/physlink/utils/diagnostics.py` → 0 issues ✅
- `mypy --strict src/physlink/core/` → 0 issues ✅
- `pytest tests/unit/utils/test_diagnostics.py -v` → 24/24 pass ✅
- `pytest tests/integration/test_core_no_torch_import.py tests/integration/test_core_boundary.py tests/integration/test_api_stability.py` → 2 pass, 1 skipped ✅

## Change Log

- 2026-05-22: Implemented Story 1.3 — physlink.doctor() diagnostic scan. Full replace of diagnostics.py stub; doctor() exposed in package __all__; 23 unit tests created covering all ACs (GO/NO-GO verdict, WARN on low VRAM, no-crash without torch, < 15s performance). Fixed google.colab find_spec edge case.
- 2026-05-22: AI code review — 3 MEDIUM + 1 LOW issues fixed: (1) AC #2 "exactly one fix" restored by changing VRAM FAIL→WARN when no GPU; (2) completion notes corrected to 24/24; (3) redundant `import importlib as _il` removed; (4) AC #2 enforcement test added. Status → done.
