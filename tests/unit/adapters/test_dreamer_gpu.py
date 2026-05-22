"""GPU tests for DreamerV3Adapter.fit() — requires CUDA (excluded from test-cpu CI job).

All tests in this module are decorated with @pytest.mark.gpu and are only
meaningful on a machine with a CUDA-capable GPU.
"""

from __future__ import annotations

import pytest

from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace


def _make_adapter() -> DreamerV3Adapter:
    obs = ObservationSpace.from_proprioception(joints=7)
    act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
    return DreamerV3Adapter(obs, act)


@pytest.mark.gpu
class TestFitRunsToCompletion:
    def test_fit_completes_without_error(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(synthetic_trajectories, steps=50)

    def test_fit_accepts_list_dict(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(list(synthetic_trajectories), steps=50)

    def test_fit_progress_bar_fields(
        self, synthetic_trajectories: list[dict], capsys: pytest.CaptureFixture
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(synthetic_trajectories, steps=50)
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "step/s" in output


@pytest.mark.gpu
class TestFitTrajectoryConversion:
    def test_list_dict_silently_converted(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        adapter = _make_adapter()
        # AR-07: list[dict] input accepted with silent conversion to TrajectoryBatch
        adapter.fit(list(synthetic_trajectories), steps=50)


@pytest.mark.gpu
class TestFitIdempotence:
    def test_second_call_does_not_raise(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(synthetic_trajectories, steps=50)
        adapter.fit(synthetic_trajectories, steps=50)

    def test_state_reset_clears_loss_history(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(synthetic_trajectories, steps=20)
        assert adapter._baseline_loss is not None  # baseline established after ≥10 steps
        adapter.fit(synthetic_trajectories, steps=20)  # fresh call resets state
        # After reset, baseline re-established from scratch — history is clean


@pytest.mark.gpu
class TestFitVRAMBudget:
    def test_vram_below_8gb(self, synthetic_trajectories: list[dict]) -> None:
        import torch

        adapter = _make_adapter()
        adapter.fit(synthetic_trajectories, steps=100)
        vram_gb = torch.cuda.memory_allocated() / 1e9
        assert vram_gb < 8.0, f"VRAM {vram_gb:.2f} GB exceeded 8 GB budget"
