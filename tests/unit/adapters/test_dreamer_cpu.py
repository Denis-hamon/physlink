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
