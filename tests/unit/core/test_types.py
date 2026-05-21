from __future__ import annotations

import inspect

from physlink.core._types import TrajectoryBatch


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
