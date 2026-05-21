"""PhysLink diagnostics — doctor() entry point.

Zero ML dependencies at module level: safe to call even when PyTorch is
not installed. Torch is detected dynamically at runtime inside check functions.
"""

from __future__ import annotations

import importlib.util
import os
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
        torch = importlib.import_module("torch")
        version = getattr(torch, "__version__", "unknown")
        return CheckResult(
            name="PyTorch presence",
            status="OK",
            value=version,
        ), torch
    except Exception as exc:
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
    except Exception as exc:
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
                status="WARN",
                value="N/A (no GPU — see CUDA availability fix above)",
                fix="",
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
    except Exception as exc:
        return CheckResult(
            name="VRAM",
            status="WARN",
            value=f"Could not read: {exc}",
            fix="Check GPU availability and torch installation.",
        )


def _check_colab_session() -> CheckResult:
    """Detect Colab environment via google.colab import or COLAB_BACKEND_VERSION env var."""
    try:
        colab_spec = importlib.util.find_spec("google.colab")
    except ModuleNotFoundError:
        colab_spec = None
    in_colab = "COLAB_BACKEND_VERSION" in os.environ or colab_spec is not None
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
    print("\nphyslink.doctor() — Environment Diagnostic")
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


__all__ = ["CheckResult", "DiagnosticReport", "doctor"]
