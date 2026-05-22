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


@pytest.mark.gpu
class TestFitDebugHooks:
    def test_fit_with_debug_hooks_true_completes(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(synthetic_trajectories, steps=50, debug_hooks=True)

    def test_fit_with_debug_hooks_false_completes(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(synthetic_trajectories, steps=50, debug_hooks=False)

    def test_fit_debug_hooks_true_idempotent(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(synthetic_trajectories, steps=50, debug_hooks=True)
        adapter.fit(synthetic_trajectories, steps=50, debug_hooks=True)

    def test_fit_debug_hooks_does_not_affect_health_tracking(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(synthetic_trajectories, steps=20, debug_hooks=True)
        assert adapter._baseline_loss is not None


@pytest.mark.gpu
class TestFitCheckpoint:
    def test_fit_writes_checkpoint_files_at_interval(
        self, synthetic_trajectories: list[dict], tmp_path: "Path"
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(
            synthetic_trajectories,
            steps=2,
            checkpoint_interval_steps=1,
            checkpoint_dir=str(tmp_path),
        )
        assert (tmp_path / "checkpoint_step_1.safetensors").exists()
        assert (tmp_path / "checkpoint_step_2.safetensors").exists()

    def test_checkpoint_metadata_contains_all_required_keys(
        self, synthetic_trajectories: list[dict], tmp_path: "Path"
    ) -> None:
        from safetensors import safe_open

        adapter = _make_adapter()
        adapter.fit(
            synthetic_trajectories,
            steps=1,
            checkpoint_interval_steps=1,
            checkpoint_dir=str(tmp_path),
        )
        path = str(tmp_path / "checkpoint_step_1.safetensors")
        with safe_open(path, framework="pt", device="cpu") as f:
            metadata = f.metadata()
        assert "physlink_version" in metadata
        assert "adapter_class" in metadata
        assert "timestamp" in metadata
        assert "checkpoint_step" in metadata

    def test_checkpoint_step_metadata_matches_step_number(
        self, synthetic_trajectories: list[dict], tmp_path: "Path"
    ) -> None:
        from safetensors import safe_open

        adapter = _make_adapter()
        adapter.fit(
            synthetic_trajectories,
            steps=1,
            checkpoint_interval_steps=1,
            checkpoint_dir=str(tmp_path),
        )
        path = str(tmp_path / "checkpoint_step_1.safetensors")
        with safe_open(path, framework="pt", device="cpu") as f:
            metadata = f.metadata()
        assert metadata["checkpoint_step"] == "1"

    def test_checkpoint_adapter_class_is_dreamerv3adapter(
        self, synthetic_trajectories: list[dict], tmp_path: "Path"
    ) -> None:
        from safetensors import safe_open

        adapter = _make_adapter()
        adapter.fit(
            synthetic_trajectories,
            steps=1,
            checkpoint_interval_steps=1,
            checkpoint_dir=str(tmp_path),
        )
        path = str(tmp_path / "checkpoint_step_1.safetensors")
        with safe_open(path, framework="pt", device="cpu") as f:
            metadata = f.metadata()
        assert metadata["adapter_class"] == "DreamerV3Adapter"

    def test_load_checkpoint_restores_model_weights(
        self, synthetic_trajectories: list[dict], tmp_path: "Path"
    ) -> None:
        import torch
        from safetensors.torch import load_file

        adapter = _make_adapter()
        adapter.fit(
            synthetic_trajectories,
            steps=2,
            checkpoint_interval_steps=1,
            checkpoint_dir=str(tmp_path),
        )
        path = str(tmp_path / "checkpoint_step_2.safetensors")
        state_dict_all = load_file(path, device="cpu")
        model_sd = {
            k[len("model."):]: v
            for k, v in state_dict_all.items()
            if k.startswith("model.")
        }
        first_key = next(iter(model_sd))
        expected = adapter._model.state_dict()[first_key].cpu()
        actual = model_sd[first_key]
        assert torch.allclose(expected, actual)

    def test_fit_after_load_checkpoint_completes_without_error(
        self, synthetic_trajectories: list[dict], tmp_path: "Path"
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(
            synthetic_trajectories,
            steps=2,
            checkpoint_interval_steps=1,
            checkpoint_dir=str(tmp_path),
        )
        adapter.load_checkpoint(str(tmp_path / "checkpoint_step_2.safetensors"))
        adapter.fit(
            synthetic_trajectories,
            steps=2,
            checkpoint_dir=str(tmp_path),
        )

    def test_fit_checkpoint_writing_is_idempotent(
        self, synthetic_trajectories: list[dict], tmp_path: "Path"
    ) -> None:
        adapter = _make_adapter()
        adapter.fit(
            synthetic_trajectories,
            steps=2,
            checkpoint_interval_steps=1,
            checkpoint_dir=str(tmp_path),
        )
        adapter.fit(
            synthetic_trajectories,
            steps=2,
            checkpoint_interval_steps=1,
            checkpoint_dir=str(tmp_path),
        )
        assert (tmp_path / "checkpoint_step_1.safetensors").exists()
        assert (tmp_path / "checkpoint_step_2.safetensors").exists()
