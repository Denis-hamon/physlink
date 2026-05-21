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
