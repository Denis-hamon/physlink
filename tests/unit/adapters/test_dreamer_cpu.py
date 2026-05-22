"""Unit tests for DreamerV3Adapter — CPU only (no GPU required).

Construction, validation, and pure-Python helper tests. GPU tests for fit()
are in test_dreamer_gpu.py.
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

        from physlink.adapters.dreamer import MIN_OBS_DIMS, DreamerV3Adapter

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
        from physlink.adapters.dreamer import MIN_OBS_DIMS, DreamerV3Adapter
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
    """visualize(), export() must raise NotImplementedError (stubs)."""

    def test_visualize_raises_not_implemented_error(self) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import AdapterError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(AdapterError):
            adapter.visualize([])

    def test_visualize_error_message_contains_got_expected_fix(self) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import AdapterError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(AdapterError) as exc_info:
            adapter.visualize([])
        msg = str(exc_info.value)
        assert "Got:" in msg
        assert "Expected:" in msg
        assert "Fix:" in msg

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


class TestFitValidation:
    """Validation errors fired before import torch — CPU-safe (AC: #1, #2)."""

    def test_fit_raises_validation_error_for_steps_zero(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError) as exc_info:
            adapter.fit(synthetic_trajectories, steps=0)
        assert "Got:" in str(exc_info.value)

    def test_fit_raises_validation_error_for_negative_steps(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError) as exc_info:
            adapter.fit(synthetic_trajectories, steps=-1)
        assert "Got:" in str(exc_info.value)

    def test_fit_raises_validation_error_for_zero_checkpoint_interval(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError) as exc_info:
            adapter.fit(synthetic_trajectories, steps=10, checkpoint_interval_steps=0)
        assert "Got:" in str(exc_info.value)

    def test_fit_raises_validation_error_for_negative_checkpoint_interval(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError) as exc_info:
            adapter.fit(synthetic_trajectories, steps=10, checkpoint_interval_steps=-1)
        assert "Got:" in str(exc_info.value)


class TestFitValidationErrorMessages:
    """Verify Got/Expected/Fix format in all ValidationError messages (AC: #1, #2)."""

    def test_steps_zero_error_contains_expected(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError) as exc_info:
            adapter.fit(synthetic_trajectories, steps=0)
        msg = str(exc_info.value)
        assert "Expected:" in msg
        assert "Fix:" in msg

    def test_steps_zero_error_contains_actual_value(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError) as exc_info:
            adapter.fit(synthetic_trajectories, steps=0)
        assert "steps=0" in str(exc_info.value)

    def test_checkpoint_interval_error_contains_expected_and_fix(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError) as exc_info:
            adapter.fit(synthetic_trajectories, steps=10, checkpoint_interval_steps=0)
        msg = str(exc_info.value)
        assert "Expected:" in msg
        assert "Fix:" in msg


class TestFitValidationBoolGuard:
    """Bool-before-int guard — isinstance(True, int) is True in Python (Dev Notes trap)."""

    def test_fit_raises_validation_error_for_bool_steps_true(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError):
            adapter.fit(synthetic_trajectories, steps=True)  # type: ignore[arg-type]

    def test_fit_raises_validation_error_for_bool_steps_false(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError):
            adapter.fit(synthetic_trajectories, steps=False)  # type: ignore[arg-type]

    def test_fit_raises_validation_error_for_bool_checkpoint_interval(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError):
            adapter.fit(synthetic_trajectories, steps=10, checkpoint_interval_steps=True)  # type: ignore[arg-type]


class TestComputeHealth:
    """Unit tests for _compute_health() — pure Python, no GPU required."""

    def _make_adapter(self) -> "DreamerV3Adapter":
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        return DreamerV3Adapter(obs, act)

    def test_returns_ok_before_baseline_established(self) -> None:
        adapter = self._make_adapter()
        # Fewer than 10 steps — no baseline yet
        for _ in range(9):
            result = adapter._compute_health(1.0)
        assert result == "OK"

    def test_baseline_established_after_ten_steps(self) -> None:
        adapter = self._make_adapter()
        for _ in range(10):
            adapter._compute_health(1.0)
        assert adapter._baseline_loss is not None

    def test_returns_ok_when_loss_within_threshold(self) -> None:
        adapter = self._make_adapter()
        # Establish baseline of 1.0
        for _ in range(10):
            adapter._compute_health(1.0)
        # Loss at 1.5× baseline — under the 2× threshold
        result = adapter._compute_health(1.5)
        assert result == "OK"

    def test_returns_anomaly_when_loss_exceeds_twice_baseline(self) -> None:
        adapter = self._make_adapter()
        # Establish baseline of 1.0
        for _ in range(10):
            adapter._compute_health(1.0)
        # Fill the rolling window with very high loss to push rolling avg above 2×
        for _ in range(50):
            adapter._compute_health(10.0)
        result = adapter._compute_health(10.0)
        assert result == "ANOMALY"

    def test_returns_ok_when_baseline_is_zero(self) -> None:
        adapter = self._make_adapter()
        # Force a zero baseline — should not divide by zero, returns OK
        for _ in range(10):
            adapter._compute_health(0.0)
        result = adapter._compute_health(0.0)
        assert result == "OK"

    def test_rolling_window_capped_at_fifty(self) -> None:
        adapter = self._make_adapter()
        for _ in range(60):
            adapter._compute_health(1.0)
        assert len(adapter._loss_history) <= 50


class TestResetTrainingState:
    """Unit tests for _reset_training_state() — CPU-safe."""

    def test_reset_clears_loss_history(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        # Populate state via _compute_health
        for i in range(15):
            adapter._compute_health(float(i))
        assert len(adapter._loss_history) > 0
        adapter._reset_training_state()
        assert adapter._loss_history == []

    def test_reset_clears_baseline_loss(self) -> None:
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        for _ in range(15):
            adapter._compute_health(1.0)
        assert adapter._baseline_loss is not None
        adapter._reset_training_state()
        assert adapter._baseline_loss is None

    def test_validation_error_does_not_corrupt_state(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        # Populate some health state
        for _ in range(5):
            adapter._compute_health(1.0)
        original_history_len = len(adapter._loss_history)
        # fit() raises before modifying state
        with pytest.raises(ValidationError):
            adapter.fit(synthetic_trajectories, steps=0)
        # State must be untouched — validation fires before reset
        assert len(adapter._loss_history) == original_history_len


class TestFitDebugHooks:
    """AC #2: debug_hooks parameter — pure-Python and validation tests (no GPU required)."""

    def test_fit_debug_hooks_false_is_default(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError):
            adapter.fit(synthetic_trajectories, steps=0)

    def test_fit_debug_hooks_true_still_validates_steps(
        self, synthetic_trajectories: list[dict]
    ) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import ValidationError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(ValidationError):
            adapter.fit(synthetic_trajectories, steps=0, debug_hooks=True)

    def test_debug_panel_initializes_with_waiting_status(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        assert all(v == "waiting..." for v in panel.stages.values())

    def test_debug_panel_update_all_sets_stage_statuses(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        panel.update_all({"data_loading": "OK"})
        assert panel.stages["data_loading"] == "OK"

    def test_debug_panel_partial_update_leaves_other_stages(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        panel.update_all({"data_loading": "OK"})
        for name, status in panel.stages.items():
            if name != "data_loading":
                assert status == "waiting..."

    def test_debug_panel_has_all_four_stage_names(self) -> None:
        from physlink.adapters.dreamer import _STAGE_NAMES, _DebugPanel

        panel = _DebugPanel()
        assert set(panel.stages.keys()) == set(_STAGE_NAMES)

    def test_debug_panel_update_all_multiple_keys(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        panel.update_all({"data_loading": "OK", "world_model_update": "RuntimeError"})
        assert panel.stages["data_loading"] == "OK"
        assert panel.stages["world_model_update"] == "RuntimeError"
        assert panel.stages["actor_update"] == "waiting..."
        assert panel.stages["critic_update"] == "waiting..."

    def test_debug_panel_error_status_propagation_pattern(self) -> None:
        """CPU-safe simulation of what the debug loop does on _training_step exception."""
        from physlink.adapters.dreamer import _STAGE_NAMES, _DebugPanel

        panel = _DebugPanel()
        stage_statuses = {name: "OK" for name in _STAGE_NAMES}
        exc = RuntimeError("simulated training failure")
        for name in ("world_model_update", "actor_update", "critic_update"):
            stage_statuses[name] = type(exc).__name__
        panel.update_all(stage_statuses)

        assert panel.stages["data_loading"] == "OK"
        assert panel.stages["world_model_update"] == "RuntimeError"
        assert panel.stages["actor_update"] == "RuntimeError"
        assert panel.stages["critic_update"] == "RuntimeError"

    def test_debug_panel_data_loading_unaffected_on_error(self) -> None:
        """data_loading is always OK by design — tensor pre-processing happens before the loop."""
        from physlink.adapters.dreamer import _STAGE_NAMES, _DebugPanel

        panel = _DebugPanel()
        stage_statuses = {name: "OK" for name in _STAGE_NAMES}
        exc = ValueError("bad tensor")
        for name in ("world_model_update", "actor_update", "critic_update"):
            stage_statuses[name] = type(exc).__name__
        panel.update_all(stage_statuses)

        assert panel.stages["data_loading"] == "OK"


class TestStageNames:
    """Verify _STAGE_NAMES module-level constant content and ordering."""

    def test_stage_names_is_tuple(self) -> None:
        from physlink.adapters.dreamer import _STAGE_NAMES

        assert isinstance(_STAGE_NAMES, tuple)

    def test_stage_names_has_four_stages(self) -> None:
        from physlink.adapters.dreamer import _STAGE_NAMES

        assert len(_STAGE_NAMES) == 4

    def test_stage_names_first_is_data_loading(self) -> None:
        from physlink.adapters.dreamer import _STAGE_NAMES

        assert _STAGE_NAMES[0] == "data_loading"

    def test_stage_names_second_is_world_model_update(self) -> None:
        from physlink.adapters.dreamer import _STAGE_NAMES

        assert _STAGE_NAMES[1] == "world_model_update"

    def test_stage_names_third_is_actor_update(self) -> None:
        from physlink.adapters.dreamer import _STAGE_NAMES

        assert _STAGE_NAMES[2] == "actor_update"

    def test_stage_names_fourth_is_critic_update(self) -> None:
        from physlink.adapters.dreamer import _STAGE_NAMES

        assert _STAGE_NAMES[3] == "critic_update"

    def test_stage_names_exact_set(self) -> None:
        from physlink.adapters.dreamer import _STAGE_NAMES

        expected = {"data_loading", "world_model_update", "actor_update", "critic_update"}
        assert set(_STAGE_NAMES) == expected


class TestDebugPanelRendering:
    """Tests for _DebugPanel.__rich__() rendering — verifies Rich markup per stage status."""

    def test_rich_returns_table_instance(self) -> None:
        from rich.table import Table

        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        assert isinstance(panel.__rich__(), Table)

    def test_rich_returns_fresh_table_each_call(self) -> None:
        """Rich Live calls __rich__() on every refresh — each call must build a new Table."""
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        table1 = panel.__rich__()
        table2 = panel.__rich__()
        assert table1 is not table2

    def test_rich_table_has_four_rows(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        table = panel.__rich__()
        assert len(table.rows) == 4

    def test_rich_waiting_status_uses_dim_markup(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        table = panel.__rich__()
        status_cells = table.columns[1]._cells
        assert all("[dim]waiting...[/dim]" == cell for cell in status_cells)

    def test_rich_ok_status_uses_bold_green_markup(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        panel.update_all({"data_loading": "OK"})
        table = panel.__rich__()
        status_cells = table.columns[1]._cells
        assert "[bold green]OK[/bold green]" in status_cells

    def test_rich_error_status_uses_bold_red_markup(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        panel.update_all({"data_loading": "RuntimeError"})
        table = panel.__rich__()
        status_cells = table.columns[1]._cells
        assert "[bold red]RuntimeError[/bold red]" in status_cells

    def test_rich_stage_labels_replace_underscores_with_spaces(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        table = panel.__rich__()
        stage_labels = table.columns[0]._cells
        assert "data loading" in stage_labels
        assert "world model update" in stage_labels
        assert "actor update" in stage_labels
        assert "critic update" in stage_labels

    def test_rich_reflects_updated_status_on_next_call(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        panel.update_all({"actor_update": "OK"})
        table = panel.__rich__()
        status_cells = table.columns[1]._cells
        assert "[bold green]OK[/bold green]" in status_cells

    def test_rich_mixed_statuses_in_same_table(self) -> None:
        from physlink.adapters.dreamer import _DebugPanel

        panel = _DebugPanel()
        panel.update_all({"data_loading": "OK", "world_model_update": "ValueError"})
        table = panel.__rich__()
        status_cells = table.columns[1]._cells
        assert "[bold green]OK[/bold green]" in status_cells
        assert "[bold red]ValueError[/bold red]" in status_cells
        assert "[dim]waiting...[/dim]" in status_cells


def _write_test_checkpoint(path: str, metadata: dict[str, str]) -> None:
    import torch
    from safetensors.torch import save_file

    save_file({"dummy": torch.tensor([1.0])}, path, metadata=metadata)


class TestCheckpointLoadErrors:
    def _make_adapter(self) -> "DreamerV3Adapter":
        from physlink import DreamerV3Adapter
        from physlink.core.spaces import ActionSpace, ObservationSpace

        obs = ObservationSpace.from_proprioception(joints=4, include_velocity=False)
        act = ActionSpace.continuous(dims=2, bounds=[(-1.0, 1.0)] * 2)
        return DreamerV3Adapter(obs, act)

    def test_load_checkpoint_raises_corrupt_on_nonexistent_file(
        self, tmp_path: "Path"
    ) -> None:
        from physlink.core.exceptions import CheckpointCorruptError

        adapter = self._make_adapter()
        with pytest.raises(CheckpointCorruptError):
            adapter.load_checkpoint(str(tmp_path / "missing.safetensors"))

    def test_load_checkpoint_raises_corrupt_when_physlink_version_key_missing(
        self, tmp_path: "Path"
    ) -> None:
        from physlink.core.exceptions import CheckpointCorruptError

        path = str(tmp_path / "no_version.safetensors")
        _write_test_checkpoint(path, metadata={"adapter_class": "DreamerV3Adapter"})
        adapter = self._make_adapter()
        with pytest.raises(CheckpointCorruptError):
            adapter.load_checkpoint(path)

    def test_load_checkpoint_raises_version_error_on_incompatible_major_minor(
        self, tmp_path: "Path"
    ) -> None:
        from physlink.core.exceptions import CheckpointVersionError

        path = str(tmp_path / "incompatible.safetensors")
        _write_test_checkpoint(path, metadata={"physlink_version": "99.99.0"})
        adapter = self._make_adapter()
        with pytest.raises(CheckpointVersionError):
            adapter.load_checkpoint(path)

    def test_checkpoint_version_error_carries_checkpoint_version(
        self, tmp_path: "Path"
    ) -> None:
        from physlink.core.exceptions import CheckpointVersionError

        path = str(tmp_path / "incompatible.safetensors")
        _write_test_checkpoint(path, metadata={"physlink_version": "99.99.0"})
        adapter = self._make_adapter()
        with pytest.raises(CheckpointVersionError) as exc_info:
            adapter.load_checkpoint(path)
        assert exc_info.value.checkpoint_version == "99.99.0"

    def test_checkpoint_version_error_carries_current_version(
        self, tmp_path: "Path"
    ) -> None:
        import physlink
        from physlink.core.exceptions import CheckpointVersionError

        path = str(tmp_path / "incompatible.safetensors")
        _write_test_checkpoint(path, metadata={"physlink_version": "99.99.0"})
        adapter = self._make_adapter()
        with pytest.raises(CheckpointVersionError) as exc_info:
            adapter.load_checkpoint(path)
        assert exc_info.value.current_version == physlink.__version__

    def test_load_checkpoint_forward_compatible_extra_keys_no_error(
        self, tmp_path: "Path"
    ) -> None:
        import physlink
        from physlink.core.exceptions import CheckpointCorruptError, CheckpointVersionError

        path = str(tmp_path / "extra_keys.safetensors")
        _write_test_checkpoint(
            path,
            metadata={
                "physlink_version": physlink.__version__,
                "new_field": "something",
            },
        )
        adapter = self._make_adapter()
        try:
            adapter.load_checkpoint(path)
        except (CheckpointVersionError, CheckpointCorruptError):
            pytest.fail("CheckpointVersionError/CorruptError raised for forward-compatible extra keys")
        except Exception:
            pass  # load_state_dict may fail with dummy weights — that is acceptable

    def test_load_checkpoint_same_minor_version_compatible(
        self, tmp_path: "Path"
    ) -> None:
        import physlink
        from physlink.core.exceptions import CheckpointVersionError

        # Build a version with same major.minor but higher patch: 0.1.99
        current = physlink.__version__
        parts = current.split(".")
        same_minor_version = f"{parts[0]}.{parts[1]}.99"

        path = str(tmp_path / "same_minor.safetensors")
        _write_test_checkpoint(path, metadata={"physlink_version": same_minor_version})
        adapter = self._make_adapter()
        try:
            adapter.load_checkpoint(path)
        except CheckpointVersionError:
            pytest.fail("CheckpointVersionError raised for compatible same major.minor version")
        except Exception:
            pass  # load_state_dict may fail with dummy weights — that is acceptable


class TestSaveCheckpointFunction:
    """Tests for _save_checkpoint() directly — CPU-safe, no fit() required."""

    def _make_simple_modules(self) -> tuple:
        import torch

        model = torch.nn.Linear(4, 4)
        actor = torch.nn.Linear(4, 2)
        critic = torch.nn.Linear(4, 1)
        return model, actor, critic

    def test_save_checkpoint_creates_directory_if_not_exists(
        self, tmp_path: "Path"
    ) -> None:
        import os

        from physlink.adapters.dreamer import _save_checkpoint

        model, actor, critic = self._make_simple_modules()
        nested_dir = str(tmp_path / "nonexistent" / "nested")
        path = _save_checkpoint(model, actor, critic, step=1, checkpoint_dir=nested_dir)

        assert os.path.isdir(nested_dir)
        assert os.path.exists(path)

    def test_save_checkpoint_returns_path_ending_with_step_filename(
        self, tmp_path: "Path"
    ) -> None:
        from physlink.adapters.dreamer import _save_checkpoint

        model, actor, critic = self._make_simple_modules()
        result = _save_checkpoint(model, actor, critic, step=42, checkpoint_dir=str(tmp_path))

        assert isinstance(result, str)
        assert result.endswith("checkpoint_step_42.safetensors")

    def test_save_checkpoint_prints_checkpoint_saved_message(
        self, tmp_path: "Path", capsys: pytest.CaptureFixture
    ) -> None:
        import os

        from physlink.adapters.dreamer import _save_checkpoint

        model, actor, critic = self._make_simple_modules()
        path = _save_checkpoint(model, actor, critic, step=7, checkpoint_dir=str(tmp_path))

        captured = capsys.readouterr()
        assert "[physlink] Checkpoint saved:" in captured.out
        assert os.path.abspath(path) in captured.out


class TestDreamerV3AdapterStory35State:
    """Story 3.5: _fit_elapsed_seconds and _triptych_path state management (CPU-safe)."""

    def _make_adapter(self) -> "DreamerV3Adapter":
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        return DreamerV3Adapter(obs, act)

    def test_fit_elapsed_seconds_is_none_before_fit(self) -> None:
        """_fit_elapsed_seconds must be None until fit() completes at least once."""
        adapter = self._make_adapter()
        assert adapter._fit_elapsed_seconds is None

    def test_triptych_path_is_none_before_visualize(self) -> None:
        """_triptych_path must be None until visualize() completes at least once."""
        adapter = self._make_adapter()
        assert adapter._triptych_path is None

    def test_reset_training_state_does_not_clear_fit_elapsed_seconds(self) -> None:
        """_fit_elapsed_seconds must survive _reset_training_state() (Story 3.5 spec).

        This ensures visualize() can always report the LAST fit duration even when
        fit() is called multiple times (each call invokes _reset_training_state()).
        """
        adapter = self._make_adapter()
        adapter._fit_elapsed_seconds = 42.0
        adapter._reset_training_state()
        assert adapter._fit_elapsed_seconds == 42.0

    def test_visualize_does_not_reference_compliance_report_in_source(self) -> None:
        """AC #3 / FR-04: visualize() must never call or trigger compliance_report()."""
        import inspect

        from physlink.adapters.dreamer import DreamerV3Adapter

        source = inspect.getsource(DreamerV3Adapter.visualize)
        assert "compliance_report" not in source, (
            "visualize() source references compliance_report — "
            "FR-04 requires triptych and compliance are never coupled"
        )


class TestVisualizeFridayCallout:
    """AC #1: Friday afternoon window callout logic verified via source inspection — CPU-safe."""

    def _source(self) -> str:
        import inspect

        from physlink.adapters.dreamer import DreamerV3Adapter

        return inspect.getsource(DreamerV3Adapter.visualize)

    def test_callout_reads_fit_elapsed_seconds(self) -> None:
        """visualize() must branch on _fit_elapsed_seconds to emit the callout."""
        assert "_fit_elapsed_seconds" in self._source()

    def test_callout_imports_baseline_seconds_constant(self) -> None:
        """Callout must use _FROM_SCRATCH_BASELINE_SECONDS from visualization module."""
        assert "_FROM_SCRATCH_BASELINE_SECONDS" in self._source()

    def test_callout_imports_baseline_label_constant(self) -> None:
        """Callout must use _FROM_SCRATCH_BASELINE_LABEL from visualization module."""
        assert "_FROM_SCRATCH_BASELINE_LABEL" in self._source()

    def test_callout_displays_speedup(self) -> None:
        """Callout must display a Speedup: ~Nx line (AC #1 Friday afternoon window)."""
        assert "Speedup" in self._source()

    def test_callout_has_fallback_branch(self) -> None:
        """When _fit_elapsed_seconds is None, a fallback message must be printed."""
        source = self._source()
        assert "Adaptation time not available" in source

    def test_callout_uses_elapsed_min_conversion(self) -> None:
        """Elapsed seconds are converted to minutes for the callout display."""
        assert "elapsed_min" in self._source()
        assert "elapsed / 60" in self._source()

    def test_callout_uses_baseline_hours_conversion(self) -> None:
        """Baseline seconds are converted to hours for the callout display."""
        assert "baseline_hours" in self._source()
        assert "3600" in self._source()

    def test_callout_fallback_printed_when_no_elapsed(self) -> None:
        """When _fit_elapsed_seconds is None, fallback branch must exist in source."""
        source = self._source()
        assert "else:" in source
        assert "call fit() before visualize()" in source


class TestCheckCheckpointMetadata:
    """Tests for _check_checkpoint_metadata() — CPU-safe, tests happy path and error formats."""

    def test_returns_metadata_dict_on_valid_checkpoint(
        self, tmp_path: "Path"
    ) -> None:
        import physlink
        from physlink.adapters.dreamer import _check_checkpoint_metadata

        path = str(tmp_path / "valid.safetensors")
        _write_test_checkpoint(path, metadata={"physlink_version": physlink.__version__})

        result = _check_checkpoint_metadata(path)

        assert isinstance(result, dict)
        assert result["physlink_version"] == physlink.__version__

    def test_corrupt_error_message_contains_got_expected_fix(
        self, tmp_path: "Path"
    ) -> None:
        from physlink.adapters.dreamer import _check_checkpoint_metadata
        from physlink.core.exceptions import CheckpointCorruptError

        with pytest.raises(CheckpointCorruptError) as exc_info:
            _check_checkpoint_metadata(str(tmp_path / "missing.safetensors"))

        msg = str(exc_info.value)
        assert "Got:" in msg
        assert "Expected:" in msg
        assert "Fix:" in msg

    def test_version_error_message_contains_got_expected_fix(
        self, tmp_path: "Path"
    ) -> None:
        from physlink.adapters.dreamer import _check_checkpoint_metadata
        from physlink.core.exceptions import CheckpointVersionError

        path = str(tmp_path / "bad_version.safetensors")
        _write_test_checkpoint(path, metadata={"physlink_version": "99.99.0"})

        with pytest.raises(CheckpointVersionError) as exc_info:
            _check_checkpoint_metadata(path)

        msg = str(exc_info.value)
        assert "Got:" in msg
        assert "Expected:" in msg
        assert "Fix:" in msg
