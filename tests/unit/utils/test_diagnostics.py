"""Unit tests for physlink.utils.diagnostics — doctor() function."""

from __future__ import annotations

import collections
import os
import time
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

        with (
            patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()),
            patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch),
        ):
            report = doctor()

        assert report.verdict == "NO-GO"
        cuda_check = next(c for c in report.checks if c.name == "CUDA availability")
        assert cuda_check.status == "FAIL"

    def test_no_go_output_contains_fix(self, capsys: pytest.CaptureFixture[str]) -> None:
        """NO-GO must display exactly one actionable fix for CUDA failure."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = False

        with (
            patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()),
            patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch),
        ):
            doctor()

        captured = capsys.readouterr()
        assert "NO-GO" in captured.out
        assert "Fix:" in captured.out

    def test_no_go_shows_exactly_one_fix_when_cuda_unavailable(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """AC #2: CPU-only must show exactly one actionable fix (GPU upgrade only)."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = False

        with (
            patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()),
            patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch),
        ):
            report = doctor()
            captured = capsys.readouterr()

        fix_count = captured.out.count("Fix:")
        assert fix_count == 1, (
            f"AC #2: exactly one Fix: line expected for CPU-only NO-GO, got {fix_count}"
        )
        vram_check = next(c for c in report.checks if c.name == "VRAM")
        assert vram_check.status == "WARN", (
            "VRAM must be WARN (not FAIL) when GPU absent to avoid duplicate fix messages"
        )

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

        with (
            patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()),
            patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch),
        ):
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

        with (
            patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()),
            patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch),
        ):
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
        mock_props.total_memory = int(3.5 * 1024**3)
        mock_props.name = "Tesla T4"
        mock_torch.cuda.get_device_properties.return_value = mock_props

        with (
            patch("physlink.utils.diagnostics.importlib.util.find_spec", return_value=MagicMock()),
            patch("physlink.utils.diagnostics.importlib.import_module", return_value=mock_torch),
        ):
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


_FakeVersionInfo = collections.namedtuple(
    "version_info", ["major", "minor", "micro", "releaselevel", "serial"]
)


class TestPythonVersionCheck:
    def test_fail_when_python_below_3_10(self) -> None:
        """Python < 3.10 must produce FAIL status on Python version check."""
        fake_version = _FakeVersionInfo(3, 9, 7, "final", 0)
        with patch("physlink.utils.diagnostics.sys") as mock_sys:
            mock_sys.version_info = fake_version
            report = doctor()

        py_check = next(c for c in report.checks if c.name == "Python version")
        assert py_check.status == "FAIL"
        assert py_check.fix != "", "Python version FAIL must include a fix suggestion"
        assert report.verdict == "NO-GO"


class TestColabSessionCheck:
    def test_ok_when_colab_backend_env_var_set(self) -> None:
        """COLAB_BACKEND_VERSION env var must produce OK for Colab session check."""
        env = os.environ.copy()
        env["COLAB_BACKEND_VERSION"] = "3"
        with patch.dict(os.environ, {"COLAB_BACKEND_VERSION": "3"}):
            report = doctor()

        colab_check = next(c for c in report.checks if c.name == "Colab session")
        assert colab_check.status == "OK"
        assert "Colab" in colab_check.value


class TestPrintReportGoWithWarnings:
    def test_go_verdict_with_warn_displays_warning_text(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GO verdict with at least one WARN must display 'Warning:' in output."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.version.cuda = "12.1"
        mock_props = MagicMock()
        mock_props.total_memory = int(3.5 * 1024**3)  # 3.5 GB → WARN
        mock_props.name = "Tesla T4"
        mock_torch.cuda.get_device_properties.return_value = mock_props

        with patch(
            "physlink.utils.diagnostics.importlib.util.find_spec",
            return_value=MagicMock(),
        ), patch(
            "physlink.utils.diagnostics.importlib.import_module",
            return_value=mock_torch,
        ):
            report = doctor()

        captured = capsys.readouterr()
        assert report.verdict == "GO"
        assert "Warning:" in captured.out, (
            "GO verdict with WARN checks must print 'Warning:' prefix in output"
        )


class TestTorchImportFailure:
    def test_fail_when_torch_importlib_raises(self) -> None:
        """find_spec returns truthy but import_module raises — must produce FAIL, not crash."""
        with patch(
            "physlink.utils.diagnostics.importlib.util.find_spec",
            return_value=MagicMock(),
        ), patch(
            "physlink.utils.diagnostics.importlib.import_module",
            side_effect=RuntimeError("corrupt torch installation"),
        ):
            try:
                report = doctor()
            except Exception as exc:
                pytest.fail(f"doctor() raised unexpectedly on import failure: {exc}")

        torch_check = next(c for c in report.checks if c.name == "PyTorch presence")
        assert torch_check.status == "FAIL"
        assert "Import failed" in torch_check.value


class TestVramExceptionPath:
    def test_warn_when_get_device_properties_raises(self) -> None:
        """get_device_properties raising must produce WARN, not crash."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.version.cuda = "12.1"
        mock_torch.cuda.get_device_properties.side_effect = RuntimeError("VRAM unavailable")

        with patch(
            "physlink.utils.diagnostics.importlib.util.find_spec",
            return_value=MagicMock(),
        ), patch(
            "physlink.utils.diagnostics.importlib.import_module",
            return_value=mock_torch,
        ):
            try:
                report = doctor()
            except Exception as exc:
                pytest.fail(f"doctor() raised unexpectedly on VRAM error: {exc}")

        vram_check = next(c for c in report.checks if c.name == "VRAM")
        assert vram_check.status == "WARN"
        assert vram_check.fix != ""


class TestCudaExceptionPath:
    def test_fail_when_cuda_is_available_raises(self) -> None:
        """torch.cuda.is_available() raising must produce FAIL, not crash."""
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.side_effect = RuntimeError("CUDA init error")

        with patch(
            "physlink.utils.diagnostics.importlib.util.find_spec",
            return_value=MagicMock(),
        ), patch(
            "physlink.utils.diagnostics.importlib.import_module",
            return_value=mock_torch,
        ):
            try:
                report = doctor()
            except Exception as exc:
                pytest.fail(f"doctor() raised unexpectedly on CUDA error: {exc}")

        cuda_check = next(c for c in report.checks if c.name == "CUDA availability")
        assert cuda_check.status == "FAIL"


class TestTopLevelPackageExport:
    def test_doctor_importable_from_physlink_namespace(self) -> None:
        """physlink.doctor must be accessible from the top-level package."""
        import physlink

        assert hasattr(physlink, "doctor"), "physlink.doctor must be in __all__ and importable"
        assert callable(physlink.doctor)

    def test_doctor_in_physlink_all(self) -> None:
        """'doctor' must be listed in physlink.__all__."""
        import physlink

        assert "doctor" in physlink.__all__
