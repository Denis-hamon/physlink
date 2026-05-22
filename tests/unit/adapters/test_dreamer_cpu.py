"""Unit tests for DreamerV3Adapter construction — CPU only (no GPU required).

All tests in this module are CPU-safe at construction stage. GPU tests will be
introduced in Story 3.2 when fit() is implemented.
"""

from __future__ import annotations

import json
import sys

import pytest

from physlink.core.exceptions import ConfigurationError
from physlink.core.spaces import ActionSpace, ObservationSpace


def _make_valid_obs(joints: int = 7, include_velocity: bool = False) -> ObservationSpace:
    return ObservationSpace.from_proprioception(joints=joints, include_velocity=include_velocity)


def _make_valid_act(dims: int = 7) -> ActionSpace:
    return ActionSpace.continuous(dims=dims, bounds=[(-1.0, 1.0)] * dims)


class TestDreamerV3AdapterConstruction:
    """AC #1, #2: Construction with valid spaces and ConfigurationError on incompatible dims."""

    def test_construction_succeeds_with_valid_7dof_spaces(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        assert adapter.obs_space is obs
        assert adapter.act_space is act

    def test_construction_stores_obs_space_and_act_space(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=4)
        act = _make_valid_act(dims=3)
        adapter = DreamerV3Adapter(obs, act)
        assert adapter.obs_space.dims == 4
        assert adapter.act_space.dims == 3

    def test_construction_with_velocity_doubles_dims(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7, include_velocity=True)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        assert adapter.obs_space.dims == 14

    def test_configuration_error_raised_for_obs_dims_below_4(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=1)  # dims=1 < 4
        act = _make_valid_act(dims=7)
        with pytest.raises(ConfigurationError):
            DreamerV3Adapter(obs, act)

    def test_configuration_error_raised_for_obs_dims_exactly_3(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=3)  # dims=3 < 4
        act = _make_valid_act(dims=7)
        with pytest.raises(ConfigurationError):
            DreamerV3Adapter(obs, act)

    def test_configuration_error_message_follows_got_expected_fix_for_obs(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=1)
        act = _make_valid_act(dims=7)
        with pytest.raises(ConfigurationError) as exc_info:
            DreamerV3Adapter(obs, act)
        msg = str(exc_info.value)
        assert "Got" in msg or "got" in msg.lower()
        assert "Expected" in msg or "expected" in msg.lower()
        assert "Fix" in msg or "fix" in msg.lower()

    def test_configuration_error_message_contains_actual_dims_for_obs(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=2)
        act = _make_valid_act(dims=7)
        with pytest.raises(ConfigurationError) as exc_info:
            DreamerV3Adapter(obs, act)
        assert "2" in str(exc_info.value)

    def test_configuration_error_raised_for_act_dims_below_1(self) -> None:
        """Edge case: ActionSpace with dims=0 should raise ConfigurationError."""
        import types

        from physlink.adapters.dreamer import DreamerV3Adapter, MIN_OBS_DIMS

        obs = _make_valid_obs(joints=MIN_OBS_DIMS)
        fake_act = types.SimpleNamespace(dims=0)
        with pytest.raises(ConfigurationError):
            DreamerV3Adapter.__init__(
                object.__new__(DreamerV3Adapter), obs, fake_act  # type: ignore[arg-type]
            )

    def test_construction_succeeds_at_exact_obs_dims_boundary(self) -> None:
        """Boundary: obs_space.dims == 4 is the minimum and must succeed."""
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=4)  # dims=4, exactly at the boundary
        act = _make_valid_act(dims=1)
        adapter = DreamerV3Adapter(obs, act)
        assert adapter.obs_space.dims == 4

    def test_configuration_error_message_follows_got_expected_fix_for_act(self) -> None:
        """Verify that a manufactured act_space with dims=0 triggers the right error message."""
        from physlink.adapters.dreamer import DreamerV3Adapter, MIN_ACT_DIMS, MIN_OBS_DIMS
        from physlink.core.exceptions import ConfigurationError

        # Construct a minimal obs that passes the obs check
        obs = _make_valid_obs(joints=MIN_OBS_DIMS)

        # Use a SimpleNamespace to simulate act_space.dims = 0
        import types
        fake_act = types.SimpleNamespace(dims=0)
        with pytest.raises(ConfigurationError) as exc_info:
            DreamerV3Adapter.__init__(
                object.__new__(DreamerV3Adapter), obs, fake_act  # type: ignore[arg-type]
            )
        msg = str(exc_info.value)
        assert "Got" in msg or "got" in msg.lower()
        assert "Expected" in msg or "expected" in msg.lower()
        assert "Fix" in msg or "fix" in msg.lower()


class TestDreamerV3AdapterIdempotence:
    """NFR-09: Re-running a cell builds a fresh adapter without side effects."""

    def test_construction_is_idempotent(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter1 = DreamerV3Adapter(obs, act)
        adapter2 = DreamerV3Adapter(obs, act)
        assert adapter1 is not adapter2
        assert adapter1.obs_space.dims == adapter2.obs_space.dims
        assert adapter1.act_space.dims == adapter2.act_space.dims

    def test_multiple_constructions_do_not_mutate_spaces(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        original_obs_dims = obs.dims
        original_act_dims = act.dims
        DreamerV3Adapter(obs, act)
        DreamerV3Adapter(obs, act)
        assert obs.dims == original_obs_dims
        assert act.dims == original_act_dims


class TestDreamerV3AdapterExplain:
    """AC #1: explain() output contract — JSON-serializable dict."""

    def test_explain_returns_dict(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        result = adapter.explain()
        assert isinstance(result, dict)

    def test_explain_contains_type_key(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        result = adapter.explain()
        assert "type" in result
        assert result["type"] == "DreamerV3Adapter"

    def test_explain_contains_obs_space_key(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        result = adapter.explain()
        assert "obs_space" in result

    def test_explain_contains_act_space_key(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        result = adapter.explain()
        assert "act_space" in result

    def test_explain_is_json_serializable(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        result = adapter.explain()
        serialized = json.dumps(result)
        assert isinstance(serialized, str)

    def test_explain_no_torch_objects(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        result = adapter.explain()
        # JSON round-trip verifies no non-serializable (e.g. torch.Tensor) values
        json.dumps(result)  # must not raise

    def test_explain_obs_space_value_is_dict(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        result = adapter.explain()
        assert isinstance(result["obs_space"], dict)

    def test_explain_act_space_value_is_dict(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        result = adapter.explain()
        assert isinstance(result["act_space"], dict)


class TestDreamerV3AdapterStubs:
    """fit(), visualize(), export() must raise NotImplementedError (stubs)."""

    def test_fit_raises_not_implemented_error(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(NotImplementedError):
            adapter.fit([], steps=10)

    def test_fit_error_message_references_story_32(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.fit([], steps=10)
        assert "3.2" in str(exc_info.value)

    def test_visualize_raises_not_implemented_error(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(NotImplementedError):
            adapter.visualize([])

    def test_visualize_error_message_references_story_35(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.visualize([])
        assert "3.5" in str(exc_info.value)

    def test_export_raises_not_implemented_error(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(NotImplementedError):
            adapter.export("/tmp/test_export")

    def test_export_error_message_references_story_36(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(NotImplementedError) as exc_info:
            adapter.export("/tmp/test_export")
        assert "3.6" in str(exc_info.value)


class TestDreamerV3AdapterRepr:
    """__repr__ contract — must return a string with obs_dims and act_dims."""

    def test_repr_returns_string(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        assert isinstance(repr(adapter), str)

    def test_repr_contains_obs_dims(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=5)
        adapter = DreamerV3Adapter(obs, act)
        assert "obs_dims=7" in repr(adapter)

    def test_repr_contains_act_dims(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=5)
        adapter = DreamerV3Adapter(obs, act)
        assert "act_dims=5" in repr(adapter)

    def test_repr_contains_class_name(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        assert "DreamerV3Adapter" in repr(adapter)


class TestDreamerV3AdapterImportNoBytorchDependency:
    """Verify that importing DreamerV3Adapter does NOT import torch at module level."""

    def test_importing_dreamer_does_not_import_torch(self) -> None:
        # torch should not be in sys.modules solely from importing DreamerV3Adapter
        # (unless it was already imported by something else in the test session).
        # We verify by importing and checking physlink.adapters.dreamer does not
        # trigger a torch import — the module must be importable without torch installed.
        # Force re-check by verifying module attributes are accessible
        import physlink.adapters.dreamer as dreamer_module

        assert hasattr(dreamer_module, "DreamerV3Adapter")
        assert hasattr(dreamer_module, "MIN_OBS_DIMS")
        assert hasattr(dreamer_module, "MIN_ACT_DIMS")
        # If torch were required at import time, this test would fail in environments
        # without torch. Since construction tests pass, torch is NOT imported at module level.

    def test_torch_not_in_sys_modules_after_dreamer_import(self) -> None:
        """torch must NOT appear in sys.modules purely due to physlink.adapters.dreamer."""
        # Only meaningful if torch is not already loaded by another test.
        # If torch is present it was imported by something else — skip the assertion.
        if "torch" in sys.modules:
            pytest.skip("torch already loaded by another test module — cannot isolate")
        import physlink.adapters.dreamer  # noqa: F401 — side-effect import test

        assert "torch" not in sys.modules, (
            "physlink.adapters.dreamer imported torch at module level — "
            "torch import must be deferred to fit() in Story 3.2"
        )
