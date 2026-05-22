"""NFR performance benchmarks for physlink.

CPU benchmarks (no mark) run in test-cpu and test-gpu CI.
GPU benchmarks (@pytest.mark.gpu) will be added in Stories 3.x/4.x for
DreamerV3Adapter fit() and compliance_report().

In test-gpu CI, pytest-benchmark compares results against
tests/perf/baselines/benchmark_baseline.json (generated on Tesla T4 GPU).
Do not compare baselines across GPU generations.
"""

from __future__ import annotations

import pytest

from physlink.utils.diagnostics import doctor


class TestDoctorNFR:
    """NFR-01: physlink.doctor() must complete in < 15 seconds end-to-end."""

    def test_doctor_under_15s(self, benchmark: pytest.FixtureRequest) -> None:
        """Benchmark doctor() execution time against NFR-01 (< 15 seconds).

        Args:
            benchmark: pytest-benchmark fixture — measures mean execution time.

        This test is CPU-safe (no GPU required). It runs in both test-cpu and
        test-gpu CI. In test-gpu, the result is compared against the committed
        JSON baseline for regression detection.
        """
        benchmark(doctor)
        mean_s = benchmark.stats.stats.mean
        assert mean_s < 15.0, (
            f"doctor() NFR-01 violation: mean {mean_s:.2f}s (limit: 15.0s)\n"
            f"  Got:      {mean_s:.2f}s mean execution time\n"
            f"  Expected: < 15.0s (NFR-01)\n"
            f"  Fix:      investigate doctor() check functions for unexpected blocking I/O"
        )


class TestComplianceReportNFR:
    """NFR-05: compliance_report() on 1000 trajectories must complete in < 30 seconds."""

    def test_compliance_report_1000_trajectories_under_30s(
        self, benchmark: pytest.FixtureRequest
    ) -> None:
        """NFR-05 CPU gate for compliance_report() computation time.

        Bypasses fit() (GPU-required) by directly populating _invariant_residuals
        with 1000 synthetic residuals. Tests the report computation path only.

        Args:
            benchmark: pytest-benchmark fixture.
        """
        import numpy as np
        from physlink import ActionSpace, DreamerV3Adapter, ObservationSpace, register_invariant

        obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        adapter = DreamerV3Adapter(obs, act)

        def mass_conservation(trajectory: dict) -> float:
            return abs(trajectory.get("mass_in", 0.0) - trajectory.get("mass_out", 0.0))

        register_invariant(adapter, "mass_conservation", mass_conservation, tolerance=0.01)

        rng = np.random.default_rng(42)
        adapter._invariant_residuals["mass_conservation"] = rng.random(1000).tolist()

        result = benchmark(adapter.compliance_report)
        mean_s = benchmark.stats.stats.mean
        assert mean_s < 30.0, (
            f"compliance_report() NFR-05 violation: mean {mean_s:.4f}s (limit: 30.0s)\n"
            f"  Got:      {mean_s:.4f}s mean on 1000 trajectories\n"
            f"  Expected: < 30.0s (NFR-05, CPU-only CI threshold)\n"
            f"  Fix:      optimize compliance_report() in adapters/dreamer.py"
        )
        assert result is not None
