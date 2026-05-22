from __future__ import annotations

import datetime
import inspect
import json

import pytest

from physlink.core._types import AdaptationConfig, AdaptationRun, TrajectoryBatch, TrajectoryBuffer
from physlink.core.spaces import ActionSpace, ObservationSpace


def _make_config(steps: int = 1000) -> AdaptationConfig:
    obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
    act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
    return AdaptationConfig(obs_space=obs, act_space=act, steps=steps)


class TestTrajectoryBatchFromList:
    def test_from_list_returns_trajectory_batch(self) -> None:
        assert isinstance(TrajectoryBatch.from_list([{"obs": [1, 2, 3]}]), TrajectoryBatch)

    def test_from_list_preserves_data(self) -> None:
        tb = TrajectoryBatch.from_list([{"a": 1}, {"a": 2}, {"a": 3}])
        assert len(tb.data) == 3

    def test_from_list_empty_list_is_valid(self) -> None:
        tb = TrajectoryBatch.from_list([])
        assert len(tb) == 0

    def test_from_list_preserves_dict_keys(self) -> None:
        original = [{"obs": [1, 2, 3]}]
        tb = TrajectoryBatch.from_list(original)
        assert tb.data[0]["obs"] == original[0]["obs"]


class TestTrajectoryBatchInterface:
    def test_len_returns_count(self) -> None:
        assert len(TrajectoryBatch.from_list([{}, {}])) == 2

    def test_iter_yields_dicts(self) -> None:
        original = [{"a": 1}, {"b": 2}]
        tb = TrajectoryBatch.from_list(original)
        assert list(tb) == original

    def test_repr_contains_n(self) -> None:
        tb = TrajectoryBatch.from_list([{}, {}, {}])
        assert "n=3" in repr(tb)


class TestTrajectoryBatchNoTorch:
    def test_no_torch_in_public_annotation(self) -> None:
        sig = str(inspect.signature(TrajectoryBatch.from_list))
        assert "torch" not in sig

    def test_no_torch_in_class_constructor_signature(self) -> None:
        sig = str(inspect.signature(TrajectoryBatch))
        assert "torch" not in sig


class TestTrajectoryBatchDirectConstruction:
    def test_direct_construction_with_data(self) -> None:
        tb = TrajectoryBatch(data=[{"obs": 1}])
        assert len(tb) == 1

    def test_direct_construction_default_empty(self) -> None:
        tb = TrajectoryBatch()
        assert len(tb) == 0

    def test_direct_construction_is_trajectory_batch(self) -> None:
        assert isinstance(TrajectoryBatch(data=[]), TrajectoryBatch)


class TestTrajectoryBatchEdgeCases:
    def test_repr_exact_format(self) -> None:
        assert repr(TrajectoryBatch.from_list([{}, {}, {}])) == "TrajectoryBatch(n=3)"

    def test_from_list_creates_distinct_instances(self) -> None:
        data = [{"x": 1}]
        assert TrajectoryBatch.from_list(data) is not TrajectoryBatch.from_list(data)

    def test_data_is_mutable(self) -> None:
        tb = TrajectoryBatch.from_list([{"a": 1}])
        tb.data.append({"b": 2})
        assert len(tb) == 2

    def test_iter_returns_same_dict_objects(self) -> None:
        original = [{"k": 99}]
        tb = TrajectoryBatch.from_list(original)
        assert next(iter(tb)) is original[0]


class TestSyntheticTrajectoriesFixture:
    def test_from_list_with_numpy_trajectories(self, synthetic_trajectories: list[dict]) -> None:
        tb = TrajectoryBatch.from_list(synthetic_trajectories)
        assert len(tb) == 1000

    def test_data_is_list_of_dicts(self, synthetic_trajectories: list[dict]) -> None:
        tb = TrajectoryBatch.from_list(synthetic_trajectories)
        assert all(isinstance(t, dict) for t in tb.data)


class TestSyntheticTrajectoriesFixtureShapes:
    def test_obs_array_shape(self, synthetic_trajectories: list[dict]) -> None:
        assert all(t["obs"].shape == (7,) for t in synthetic_trajectories)

    def test_action_array_shape(self, synthetic_trajectories: list[dict]) -> None:
        assert all(t["action"].shape == (3,) for t in synthetic_trajectories)

    def test_obs_and_action_keys_present(self, synthetic_trajectories: list[dict]) -> None:
        assert all("obs" in t and "action" in t for t in synthetic_trajectories)


class TestAdaptationConfigImmutability:
    def test_config_raises_on_mutation(self) -> None:
        from dataclasses import FrozenInstanceError

        config = _make_config()
        with pytest.raises(FrozenInstanceError):
            config.steps = 9999  # type: ignore[misc]

    def test_config_stores_correct_fields(self) -> None:
        obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        config = AdaptationConfig(obs_space=obs, act_space=act, steps=500, checkpoint_interval_steps=100)
        assert config.obs_space is obs
        assert config.act_space is act
        assert config.steps == 500
        assert config.checkpoint_interval_steps == 100

    def test_config_default_checkpoint_interval(self) -> None:
        config = _make_config()
        assert config.checkpoint_interval_steps == 1000

    def test_config_default_checkpoint_dir(self) -> None:
        config = _make_config()
        assert config.checkpoint_dir == "physlink_checkpoints"

    def test_config_checkpoint_dir_mutation_raises(self) -> None:
        from dataclasses import FrozenInstanceError

        config = _make_config()
        with pytest.raises(FrozenInstanceError):
            config.checkpoint_dir = "/tmp/other"  # type: ignore[misc]


class TestAdaptationConfigSerialization:
    def test_to_dict_contains_required_keys(self) -> None:
        d = _make_config().to_dict()
        for key in ("obs_space", "act_space", "steps", "checkpoint_interval_steps", "checkpoint_dir"):
            assert key in d

    def test_to_dict_obs_space_is_json_serializable(self) -> None:
        d = _make_config().to_dict()
        json.dumps(d["obs_space"])  # must not raise

    def test_to_dict_act_space_is_json_serializable(self) -> None:
        d = _make_config().to_dict()
        json.dumps(d["act_space"])  # must not raise

    def test_to_dict_no_torch_objects(self) -> None:
        import sys

        d = _make_config().to_dict()

        def _has_torch(val: object) -> bool:
            if "torch" in sys.modules:
                import torch

                if isinstance(val, torch.Tensor):
                    return True
            if isinstance(val, dict):
                return any(_has_torch(v) for v in val.values())
            if isinstance(val, (list, tuple)):
                return any(_has_torch(v) for v in val)
            return False

        assert not _has_torch(d)

    def test_yaml_round_trip_equal(self, tmp_path: pytest.TempPathFactory) -> None:
        config = _make_config()
        path = str(tmp_path / "config.yaml")
        config.to_yaml(path)
        loaded = AdaptationConfig.from_yaml(path)
        assert loaded == config

    def test_from_dict_round_trip_equal(self) -> None:
        config = _make_config()
        assert AdaptationConfig.from_dict(config.to_dict()) == config


class TestAdaptationRunState:
    def test_run_is_not_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        config = _make_config()
        run = AdaptationRun(config=config)
        try:
            run.current_step = 42
        except FrozenInstanceError:
            pytest.fail("AdaptationRun should not be frozen")

    def test_run_stores_config(self) -> None:
        config = _make_config()
        run = AdaptationRun(config=config)
        assert run.config is config

    def test_run_config_unchanged_after_mutation(self) -> None:
        from dataclasses import FrozenInstanceError

        config = _make_config()
        run = AdaptationRun(config=config)
        run.current_step = 999
        run.elapsed_seconds = 3.14
        with pytest.raises(FrozenInstanceError):
            config.steps = 1  # type: ignore[misc]
        assert config.steps == 1000

    def test_run_default_step_is_zero(self) -> None:
        run = AdaptationRun(config=_make_config())
        assert run.current_step == 0

    def test_run_has_started_at_iso_format(self) -> None:
        run = AdaptationRun(config=_make_config())
        assert isinstance(run.started_at, str)
        assert len(run.started_at) > 0
        datetime.datetime.fromisoformat(run.started_at)  # must not raise


class TestAdaptationConfigEquality:
    """Story 4.1: AdaptationConfig frozen dataclass uses value equality via spaces.__eq__."""

    def test_equal_configs_are_equal(self) -> None:
        assert _make_config() == _make_config()

    def test_equality_is_value_based_not_identity(self) -> None:
        a = _make_config()
        b = _make_config()
        assert a is not b
        assert a == b

    def test_different_steps_not_equal(self) -> None:
        assert _make_config(steps=500) != _make_config(steps=1000)

    def test_different_checkpoint_interval_not_equal(self) -> None:
        obs = ObservationSpace.from_proprioception(joints=7)
        act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        a = AdaptationConfig(
            obs_space=obs, act_space=act, steps=1000, checkpoint_interval_steps=100
        )
        b = AdaptationConfig(
            obs_space=obs, act_space=act, steps=1000, checkpoint_interval_steps=500
        )
        assert a != b

    def test_different_checkpoint_dir_not_equal(self) -> None:
        obs = ObservationSpace.from_proprioception(joints=7)
        act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        a = AdaptationConfig(obs_space=obs, act_space=act, steps=1000, checkpoint_dir="dir_a")
        b = AdaptationConfig(obs_space=obs, act_space=act, steps=1000, checkpoint_dir="dir_b")
        assert a != b

    def test_different_obs_space_not_equal(self) -> None:
        obs_a = ObservationSpace.from_proprioception(joints=7)
        obs_b = ObservationSpace.from_proprioception(joints=5)
        act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        a = AdaptationConfig(obs_space=obs_a, act_space=act, steps=1000)
        b = AdaptationConfig(obs_space=obs_b, act_space=act, steps=1000)
        assert a != b

    def test_different_act_space_not_equal(self) -> None:
        obs = ObservationSpace.from_proprioception(joints=7)
        act_a = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        act_b = ActionSpace.continuous(dims=5, bounds=[(-1.0, 1.0)] * 5)
        a = AdaptationConfig(obs_space=obs, act_space=act_a, steps=1000)
        b = AdaptationConfig(obs_space=obs, act_space=act_b, steps=1000)
        assert a != b

    def test_config_is_hashable(self) -> None:
        config = _make_config()
        d = {config: "run_id"}
        assert d[config] == "run_id"

    def test_equal_configs_have_equal_hash(self) -> None:
        assert hash(_make_config()) == hash(_make_config())

    def test_config_usable_as_set_element(self) -> None:
        configs = {_make_config(), _make_config()}
        assert len(configs) == 1


class TestAdaptationRunDefaults:
    """Story 4.1: AdaptationRun mutable defaults and independent instances."""

    def test_checkpoint_paths_default_is_empty_list(self) -> None:
        run = AdaptationRun(config=_make_config())
        assert run.checkpoint_paths == []

    def test_elapsed_seconds_default_is_zero(self) -> None:
        run = AdaptationRun(config=_make_config())
        assert run.elapsed_seconds == 0.0

    def test_checkpoint_paths_is_mutable_list(self) -> None:
        run = AdaptationRun(config=_make_config())
        run.checkpoint_paths.append("/tmp/ckpt.safetensors")
        assert len(run.checkpoint_paths) == 1

    def test_two_runs_have_independent_checkpoint_paths(self) -> None:
        run_a = AdaptationRun(config=_make_config())
        run_b = AdaptationRun(config=_make_config())
        run_a.checkpoint_paths.append("/tmp/ckpt.safetensors")
        assert run_b.checkpoint_paths == []

    def test_elapsed_seconds_is_float(self) -> None:
        run = AdaptationRun(config=_make_config())
        assert isinstance(run.elapsed_seconds, float)

    def test_current_step_is_int(self) -> None:
        run = AdaptationRun(config=_make_config())
        assert isinstance(run.current_step, int)

    def test_started_at_is_utc_timezone_aware(self) -> None:
        run = AdaptationRun(config=_make_config())
        parsed = datetime.datetime.fromisoformat(run.started_at)
        assert parsed.tzinfo is not None

    def test_two_runs_have_distinct_started_at(self) -> None:
        import time

        run_a = AdaptationRun(config=_make_config())
        time.sleep(0.001)
        run_b = AdaptationRun(config=_make_config())
        assert run_a.started_at <= run_b.started_at


# ---------------------------------------------------------------------------
# TrajectoryBuffer — Story 4.2
# ---------------------------------------------------------------------------

_SAMPLE_TRAJECTORIES: list[dict[str, object]] = [
    {"obs": [1.0, 2.0, 3.0], "action": [0.1, 0.2]},
    {"obs": [4.0, 5.0, 6.0], "action": [0.3, 0.4]},
    {"obs": [7.0, 8.0, 9.0], "action": [0.5, 0.6]},
]


class TestTrajectoryBufferConstruction:
    def test_empty_buffer_has_zero_length(self) -> None:
        buf = TrajectoryBuffer()
        assert len(buf) == 0

    def test_buffer_with_data_reports_length(self) -> None:
        buf = TrajectoryBuffer(data=[{}, {}])
        assert len(buf) == 2

    def test_repr_shows_n(self) -> None:
        buf = TrajectoryBuffer(data=[{}, {}])
        assert repr(buf) == "TrajectoryBuffer(n=2)"

    def test_repr_empty(self) -> None:
        assert repr(TrajectoryBuffer()) == "TrajectoryBuffer(n=0)"

    def test_iter_yields_dicts(self) -> None:
        data = [{"a": 1}, {"b": 2}]
        buf = TrajectoryBuffer(data=data)
        assert list(buf) == data

    def test_isinstance(self) -> None:
        assert isinstance(TrajectoryBuffer(), TrajectoryBuffer)

    def test_to_batch_returns_trajectory_batch(self) -> None:
        buf = TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES)
        batch = buf.to_batch()
        assert isinstance(batch, TrajectoryBatch)

    def test_to_batch_preserves_data_length(self) -> None:
        buf = TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES)
        assert len(buf.to_batch()) == len(_SAMPLE_TRAJECTORIES)

    def test_to_batch_data_equal(self) -> None:
        buf = TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES)
        assert buf.to_batch().data == _SAMPLE_TRAJECTORIES

    def test_to_batch_on_empty_buffer_returns_empty_batch(self) -> None:
        batch = TrajectoryBuffer().to_batch()
        assert isinstance(batch, TrajectoryBatch)
        assert len(batch) == 0


class TestTrajectoryBufferExport:
    def test_export_creates_file(self, tmp_path: pytest.TempdirFactory) -> None:
        path = str(tmp_path / "t.pkl")
        buf = TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES)
        buf.export(path)
        import os
        assert os.path.exists(path)

    def test_export_does_not_modify_data(self, tmp_path: pytest.TempdirFactory) -> None:
        path = str(tmp_path / "t.pkl")
        buf = TrajectoryBuffer(data=list(_SAMPLE_TRAJECTORIES))
        original_data = list(buf.data)
        buf.export(path)
        assert buf.data == original_data

    def test_export_file_is_non_empty(self, tmp_path: pytest.TempdirFactory) -> None:
        path = str(tmp_path / "t.pkl")
        buf = TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES)
        buf.export(path)
        import os
        assert os.path.getsize(path) > 0

    def test_export_empty_buffer(self, tmp_path: pytest.TempdirFactory) -> None:
        path = str(tmp_path / "empty.pkl")
        TrajectoryBuffer().export(path)
        import os
        assert os.path.exists(path)


class TestTrajectoryBufferLoad:
    def test_load_returns_trajectory_buffer(self, tmp_path: pytest.TempdirFactory) -> None:
        path = str(tmp_path / "t.pkl")
        TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES).export(path)
        loaded = TrajectoryBuffer.load(path)
        assert isinstance(loaded, TrajectoryBuffer)

    def test_round_trip_fidelity_single_trajectory(self, tmp_path: pytest.TempdirFactory) -> None:
        data = [{"obs": [1.0, 2.0], "action": [0.5]}]
        path = str(tmp_path / "single.pkl")
        TrajectoryBuffer(data=data).export(path)
        loaded = TrajectoryBuffer.load(path)
        assert loaded.data == data

    def test_round_trip_fidelity_multiple_trajectories(
        self, tmp_path: pytest.TempdirFactory
    ) -> None:
        path = str(tmp_path / "multi.pkl")
        TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES).export(path)
        loaded = TrajectoryBuffer.load(path)
        assert loaded.data == _SAMPLE_TRAJECTORIES

    def test_round_trip_fidelity_nested_data(self, tmp_path: pytest.TempdirFactory) -> None:
        import numpy as np
        data = [{"obs": np.array([1.0, 2.0, 3.0]), "action": np.array([0.1])}]
        path = str(tmp_path / "numpy.pkl")
        TrajectoryBuffer(data=data).export(path)
        loaded = TrajectoryBuffer.load(path)
        assert len(loaded.data) == 1
        np.testing.assert_array_equal(loaded.data[0]["obs"], data[0]["obs"])

    def test_load_result_length(self, tmp_path: pytest.TempdirFactory) -> None:
        path = str(tmp_path / "t.pkl")
        TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES).export(path)
        loaded = TrajectoryBuffer.load(path)
        assert len(loaded) == len(_SAMPLE_TRAJECTORIES)

    def test_load_result_usable_in_to_batch(self, tmp_path: pytest.TempdirFactory) -> None:
        path = str(tmp_path / "t.pkl")
        TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES).export(path)
        loaded = TrajectoryBuffer.load(path)
        batch = loaded.to_batch()
        assert isinstance(batch, TrajectoryBatch)
        assert len(batch) == len(_SAMPLE_TRAJECTORIES)

    def test_load_nonexistent_raises_file_not_found(
        self, tmp_path: pytest.TempdirFactory
    ) -> None:
        with pytest.raises(FileNotFoundError):
            TrajectoryBuffer.load(str(tmp_path / "nonexistent.pkl"))

    def test_round_trip_fidelity_empty_buffer(self, tmp_path: pytest.TempdirFactory) -> None:
        path = str(tmp_path / "empty.pkl")
        TrajectoryBuffer().export(path)
        loaded = TrajectoryBuffer.load(path)
        assert isinstance(loaded, TrajectoryBuffer)
        assert len(loaded) == 0
        assert loaded.data == []


class TestTrajectoryBufferIdempotence:
    def test_re_export_same_path_overwrites_cleanly(
        self, tmp_path: pytest.TempdirFactory
    ) -> None:
        path = str(tmp_path / "t.pkl")
        buf = TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES)
        buf.export(path)
        buf.export(path)  # re-run same export — must not fail or corrupt
        loaded = TrajectoryBuffer.load(path)
        assert loaded.data == _SAMPLE_TRAJECTORIES

    def test_re_load_produces_equal_buffer(self, tmp_path: pytest.TempdirFactory) -> None:
        path = str(tmp_path / "t.pkl")
        TrajectoryBuffer(data=_SAMPLE_TRAJECTORIES).export(path)
        loaded_a = TrajectoryBuffer.load(path)
        loaded_b = TrajectoryBuffer.load(path)
        assert loaded_a.data == loaded_b.data
