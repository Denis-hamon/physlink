"""Unit tests for DreamerV3Adapter — CPU only (no GPU required).

Construction, validation, and pure-Python helper tests. GPU tests for fit()
are in test_dreamer_gpu.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

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
    """visualize() raises AdapterError (no model); export() raises AdapterError when visualize() was not called."""

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

    def test_export_raises_adapter_error_without_visualize(self) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import AdapterError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(AdapterError):
            adapter.export("/tmp/test_export")

    def test_export_error_message_contains_got_expected_fix(self) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import AdapterError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(AdapterError) as exc_info:
            adapter.export("/tmp/test_export")
        msg = str(exc_info.value)
        assert "Got:" in msg
        assert "Expected:" in msg
        assert "Fix:" in msg


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

    def test_reset_clears_invariant_residuals(self) -> None:
        """Story 4.3: _reset_training_state() must reset _invariant_residuals (NFR-09)."""
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        adapter._invariant_residuals = {"mass": [0.1, 0.2, 0.3]}
        adapter._reset_training_state()
        assert adapter._invariant_residuals == {}

    def test_reset_clears_soft_penalty_per_step(self) -> None:
        """Story 4.3: _reset_training_state() must reset _soft_penalty_per_step (NFR-09)."""
        from physlink import DreamerV3Adapter

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        adapter._soft_penalty_per_step = 42.5
        adapter._reset_training_state()
        assert adapter._soft_penalty_per_step == 0.0

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

    def test_last_checkpoint_path_is_none_before_fit(self) -> None:
        """_last_checkpoint_path must be None until fit() captures the first checkpoint path."""
        adapter = self._make_adapter()
        assert adapter._last_checkpoint_path is None

    def test_reset_training_state_does_not_clear_last_checkpoint_path(self) -> None:
        """_last_checkpoint_path must survive _reset_training_state() (Story 3.6 spec).

        export() always needs the most recent checkpoint path even when fit() is
        called multiple times, each of which invokes _reset_training_state().
        """
        adapter = self._make_adapter()
        adapter._last_checkpoint_path = "/fake/checkpoint_step_10000.safetensors"
        adapter._reset_training_state()
        assert adapter._last_checkpoint_path == "/fake/checkpoint_step_10000.safetensors"

    def test_invariants_list_empty_after_construction(self) -> None:
        """Story 4.3: _invariants must be an empty list on a freshly constructed adapter."""
        adapter = self._make_adapter()
        assert adapter._invariants == []

    def test_invariant_residuals_empty_after_construction(self) -> None:
        """Story 4.3: _invariant_residuals must be an empty dict on a freshly constructed adapter."""
        adapter = self._make_adapter()
        assert adapter._invariant_residuals == {}

    def test_soft_penalty_per_step_zero_after_construction(self) -> None:
        """Story 4.3: _soft_penalty_per_step must be 0.0 on a freshly constructed adapter."""
        adapter = self._make_adapter()
        assert adapter._soft_penalty_per_step == 0.0


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


# ---------------------------------------------------------------------------
# Fixture: adapter with _triptych_path set to a stub GIF file
# ---------------------------------------------------------------------------

_STUB_GIF = b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"


@pytest.fixture
def _adapter_with_triptych(tmp_path: Path) -> "DreamerV3Adapter":  # type: ignore[type-arg]
    from physlink import DreamerV3Adapter

    obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
    act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
    adapter = DreamerV3Adapter(obs, act)
    stub_gif = tmp_path / "stub.gif"
    stub_gif.write_bytes(_STUB_GIF)
    adapter._triptych_path = str(stub_gif)
    return adapter


class TestDreamerV3AdapterExport:
    """AC: all — export() artifact bundle and _share_panel() (CPU only, no GPU)."""

    def test_export_creates_output_directory(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        assert (tmp_path / "out").is_dir()

    def test_export_creates_gif_file(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        assert (tmp_path / "out" / "triptych.gif").is_file()

    def test_export_creates_yaml_config(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        import yaml

        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        yaml_path = tmp_path / "out" / "config.yaml"
        assert yaml_path.is_file()
        loaded = yaml.safe_load(yaml_path.read_text())
        assert isinstance(loaded, dict)

    def test_export_yaml_contains_required_keys(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        import yaml

        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        yaml_path = tmp_path / "out" / "config.yaml"
        loaded = yaml.safe_load(yaml_path.read_text())
        assert "obs_space" in loaded
        assert "act_space" in loaded
        assert "checkpoint_path" in loaded

    def test_export_creates_summary_file(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        summary_path = tmp_path / "out" / "summary.txt"
        assert summary_path.is_file()
        assert summary_path.stat().st_size > 0

    def test_export_returns_artifact_paths_dict(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        export_dir = str(tmp_path / "out")
        result = _adapter_with_triptych.export(export_dir)
        assert isinstance(result, dict)
        assert "gif" in result
        assert "config" in result
        assert "summary" in result

    def test_export_raises_adapter_error_without_triptych(self) -> None:
        from physlink import DreamerV3Adapter
        from physlink.core.exceptions import AdapterError

        obs = _make_valid_obs(joints=7)
        act = _make_valid_act(dims=7)
        adapter = DreamerV3Adapter(obs, act)
        with pytest.raises(AdapterError):
            adapter.export("/tmp/physlink_test_no_triptych")

    def test_export_checkpoint_path_null_in_yaml_when_no_checkpoint(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        import yaml

        _adapter_with_triptych._last_checkpoint_path = None
        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        yaml_path = tmp_path / "out" / "config.yaml"
        loaded = yaml.safe_load(yaml_path.read_text())
        assert loaded["checkpoint_path"] is None

    def test_export_idempotent(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        _adapter_with_triptych.export(export_dir)
        assert (tmp_path / "out" / "triptych.gif").is_file()

    def test_share_panel_outside_colab_prints_message(self, capsys: pytest.CaptureFixture) -> None:
        from physlink.adapters.dreamer import _share_panel

        _share_panel("./export_test")
        captured = capsys.readouterr()
        assert "Share panel" in captured.out
        assert "export_test" in captured.out

    def test_export_returned_paths_all_exist(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        """AC #1: returned dict paths must all point to files that exist on disk."""
        export_dir = str(tmp_path / "out")
        result = _adapter_with_triptych.export(export_dir)
        assert Path(result["gif"]).is_file()
        assert Path(result["config"]).is_file()
        assert Path(result["summary"]).is_file()

    def test_export_yaml_obs_space_is_json_serializable_dict(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        """AC #2: obs_space in YAML must be a JSON-serializable dict, not a raw Python object."""
        import json

        import yaml

        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        loaded = yaml.safe_load((tmp_path / "out" / "config.yaml").read_text())
        assert isinstance(loaded["obs_space"], dict)
        json.dumps(loaded["obs_space"])  # raises TypeError if not serializable

    def test_export_yaml_act_space_is_json_serializable_dict(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        """AC #2: act_space in YAML must be a JSON-serializable dict, not a raw Python object."""
        import json

        import yaml

        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        loaded = yaml.safe_load((tmp_path / "out" / "config.yaml").read_text())
        assert isinstance(loaded["act_space"], dict)
        json.dumps(loaded["act_space"])  # raises TypeError if not serializable

    def test_export_summary_contains_expected_fields(
        self, _adapter_with_triptych: object, tmp_path: Path
    ) -> None:
        """Summary.txt must contain adapter type, obs_dims, act_dims, and export timestamp."""
        export_dir = str(tmp_path / "out")
        _adapter_with_triptych.export(export_dir)
        content = (tmp_path / "out" / "summary.txt").read_text()
        assert "DreamerV3Adapter" in content
        assert "obs_dims" in content
        assert "act_dims" in content
        assert "Exported at" in content


class TestFitReturnTypeStory41:
    """Story 4.1: fit() return type changed None -> AdaptationRun — CPU-safe source inspection."""

    def _fit_source(self) -> str:
        import inspect

        from physlink.adapters.dreamer import DreamerV3Adapter

        return inspect.getsource(DreamerV3Adapter.fit)

    def test_fit_return_annotation_references_adaptation_run(self) -> None:
        assert "AdaptationRun" in self._fit_source()

    def test_fit_source_constructs_adaptation_run_instance(self) -> None:
        assert "AdaptationRun(" in self._fit_source()

    def test_fit_source_constructs_adaptation_config_instance(self) -> None:
        assert "AdaptationConfig(" in self._fit_source()

    def test_fit_source_collects_checkpoint_paths_list(self) -> None:
        assert "_run_checkpoint_paths" in self._fit_source()

    def test_fit_source_returns_run_variable(self) -> None:
        assert "return _run" in self._fit_source()

    def test_fit_source_appends_to_checkpoint_paths(self) -> None:
        assert "_run_checkpoint_paths.append" in self._fit_source()

    def test_fit_source_sets_elapsed_seconds_on_run(self) -> None:
        assert "elapsed_seconds" in self._fit_source()

    def test_fit_type_checking_import_for_annotation(self) -> None:
        import inspect

        from physlink.adapters import dreamer as dreamer_module

        source = inspect.getsource(dreamer_module)
        assert "TYPE_CHECKING" in source
        assert "AdaptationRun" in source


# ---------------------------------------------------------------------------
# Story 4.2 — TrajectoryBuffer accepted by fit()
# ---------------------------------------------------------------------------

class TestFitWithTrajectoryBufferStory42:
    """Verify fit() and related methods accept TrajectoryBuffer (Story 4.2)."""

    @pytest.fixture()
    def adapter(self) -> "DreamerV3Adapter":
        from physlink import DreamerV3Adapter
        obs = ObservationSpace.from_proprioception(joints=7)
        act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        return DreamerV3Adapter(obs, act)

    @pytest.fixture()
    def sample_buffer(self) -> "TrajectoryBuffer":
        from physlink.core._types import TrajectoryBuffer
        data = [{"obs": [float(i)] * 7, "action": [0.0] * 7} for i in range(10)]
        return TrajectoryBuffer(data=data)

    def test_fit_accepts_trajectory_buffer(
        self, adapter: "DreamerV3Adapter", sample_buffer: "TrajectoryBuffer"
    ) -> None:
        pytest.importorskip("torch")
        adapter.fit(sample_buffer, steps=2, checkpoint_interval_steps=1)

    def test_fit_trajectory_buffer_produces_adaptation_run(
        self, adapter: "DreamerV3Adapter", sample_buffer: "TrajectoryBuffer"
    ) -> None:
        pytest.importorskip("torch")
        from physlink.core._types import AdaptationRun
        run = adapter.fit(sample_buffer, steps=2, checkpoint_interval_steps=1)
        assert isinstance(run, AdaptationRun)

    def test_fit_buffer_export_load_round_trip(
        self,
        adapter: "DreamerV3Adapter",
        sample_buffer: "TrajectoryBuffer",
        tmp_path: Path,
    ) -> None:
        pytest.importorskip("torch")
        from physlink.core._types import AdaptationRun, TrajectoryBuffer
        path = str(tmp_path / "buf.pkl")
        sample_buffer.export(path)
        loaded = TrajectoryBuffer.load(path)
        run = adapter.fit(loaded, steps=2, checkpoint_interval_steps=1)
        assert isinstance(run, AdaptationRun)

    def test_trajectory_buffer_import_at_module_level(self) -> None:
        import inspect
        from physlink.adapters import dreamer as dreamer_module
        source = inspect.getsource(dreamer_module)
        assert "TrajectoryBuffer" in source

    def test_fit_trajectory_buffer_raises_validation_error_for_invalid_steps(
        self, adapter: "DreamerV3Adapter", sample_buffer: "TrajectoryBuffer"
    ) -> None:
        from physlink.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            adapter.fit(sample_buffer, steps=0)

    def test_visualize_raises_adapter_error_with_trajectory_buffer_input(
        self, adapter: "DreamerV3Adapter", sample_buffer: "TrajectoryBuffer"
    ) -> None:
        from physlink.core.exceptions import AdapterError
        with pytest.raises(AdapterError):
            adapter.visualize(sample_buffer)

    def test_visualize_source_has_trajectory_buffer_isinstance_check(self) -> None:
        import inspect
        from physlink.adapters.dreamer import DreamerV3Adapter
        source = inspect.getsource(DreamerV3Adapter.visualize)
        assert "isinstance(trajectories, TrajectoryBuffer)" in source


# ---------------------------------------------------------------------------
# Story 4.3 — register_invariant() integration tests (CPU / GPU agnostic)
# ---------------------------------------------------------------------------

def _make_adapter_43() -> "DreamerV3Adapter":
    from physlink import DreamerV3Adapter
    obs = ObservationSpace.from_proprioception(joints=7)
    act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
    return DreamerV3Adapter(obs, act)


def _make_trajectories_43(n: int = 10) -> list[dict]:
    return [{"obs": [float(i)] * 7, "action": [0.0] * 7} for i in range(n)]


class TestRegisterInvariantHardModeStory43:
    """AC #2 — hard mode filtering during fit()."""

    def test_hard_mode_rejects_violating_trajectory_raises(self) -> None:
        from physlink.core.validation import register_invariant
        from physlink.core.exceptions import ValidationError

        adapter = _make_adapter_43()
        register_invariant(adapter, "always_high", lambda t: 1.0, tolerance=0.5, mode="hard")
        with pytest.raises(ValidationError):
            adapter.fit(_make_trajectories_43(), steps=1)

    def test_hard_mode_all_rejected_error_has_got_expected_fix(self) -> None:
        """AC #2: the ValidationError for all-rejected must follow Got/Expected/Fix format."""
        from physlink.core.exceptions import ValidationError
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "always_high", lambda t: 1.0, tolerance=0.5, mode="hard")
        with pytest.raises(ValidationError) as exc_info:
            adapter.fit(_make_trajectories_43(), steps=1)
        msg = str(exc_info.value)
        assert "Got:" in msg
        assert "Expected:" in msg
        assert "Fix:" in msg

    def test_hard_mode_keeps_passing_trajectory(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "always_zero", lambda t: 0.0, tolerance=0.5, mode="hard")
        adapter.fit(_make_trajectories_43(), steps=2, checkpoint_interval_steps=10)

    def test_hard_mode_partial_rejection(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        # reject trajectories where obs[0] > 4 (indices 5-9), keep indices 0-4
        register_invariant(
            adapter, "low_obs", lambda t: float(t["obs"][0]), tolerance=4.0, mode="hard"
        )
        adapter.fit(_make_trajectories_43(10), steps=2, checkpoint_interval_steps=10)
        # residuals stored for all 10 trajectories
        assert len(adapter._invariant_residuals["low_obs"]) == 10

    def test_hard_mode_logs_diagnostic(self, capsys: pytest.CaptureFixture) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        # reject trajectories where obs[0] > 0 (indices 1-9), keep index 0
        register_invariant(
            adapter, "strict_zero", lambda t: float(t["obs"][0]), tolerance=0.0, mode="hard"
        )
        adapter.fit(_make_trajectories_43(10), steps=2, checkpoint_interval_steps=10)
        captured = capsys.readouterr()
        assert "strict_zero" in captured.out
        assert "rejected" in captured.out

    def test_hard_mode_residuals_stored(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "mass", lambda t: 0.0, tolerance=0.5, mode="hard")
        adapter.fit(_make_trajectories_43(10), steps=2, checkpoint_interval_steps=10)
        assert "mass" in adapter._invariant_residuals
        assert len(adapter._invariant_residuals["mass"]) == 10

    def test_fn_exception_treated_as_zero_residual(self, capsys: pytest.CaptureFixture) -> None:
        """fn that raises during _apply_invariants must not crash fit(); residual treated as 0.0."""
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()

        def exploding(t: dict) -> float:
            raise RuntimeError("simulated fn crash")

        register_invariant(adapter, "exploding", exploding, tolerance=0.5, mode="hard")
        # hard mode, fn explodes → residual=0.0 < tolerance=0.5, so no trajectories rejected
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        captured = capsys.readouterr()
        assert "exploding" in captured.out
        assert "treating residual as 0.0" in captured.out
        # All residuals stored as 0.0
        assert all(r == 0.0 for r in adapter._invariant_residuals["exploding"])


class TestRegisterInvariantSoftModeStory43:
    """AC #3 — soft mode keeps all trajectories, penalizes loss."""

    def test_soft_mode_does_not_filter(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        # all trajectories violate (residual=2.0 > tolerance=0.1) but mode=soft
        register_invariant(adapter, "soft_inv", lambda t: 2.0, tolerance=0.1, mode="soft")
        # should not raise ValidationError
        adapter.fit(_make_trajectories_43(), steps=2, checkpoint_interval_steps=10)

    def test_soft_mode_residuals_stored(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "energy", lambda t: 1.0, tolerance=0.5, mode="soft")
        adapter.fit(_make_trajectories_43(10), steps=2, checkpoint_interval_steps=10)
        assert "energy" in adapter._invariant_residuals
        assert len(adapter._invariant_residuals["energy"]) == 10

    def test_soft_mode_zero_residual_no_penalty(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "zero", lambda t: 0.0, tolerance=0.5, mode="soft")
        adapter.fit(_make_trajectories_43(), steps=2, checkpoint_interval_steps=10)
        assert adapter._soft_penalty_per_step == 0.0

    def test_soft_mode_nonzero_penalty_when_violations(self) -> None:
        """AC #3: _soft_penalty_per_step > 0 when soft invariant is violated."""
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        # residual=2.0 >> tolerance=0.1 for every trajectory
        register_invariant(adapter, "violated", lambda t: 2.0, tolerance=0.1, mode="soft")
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        assert adapter._soft_penalty_per_step > 0.0


class TestRegisterInvariantIdempotenceStory43:
    """NFR-09 — fit() twice resets residuals (idempotence)."""

    def test_fit_twice_resets_residuals(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "mass", lambda t: 0.0, tolerance=0.5, mode="soft")
        adapter.fit(_make_trajectories_43(10), steps=2, checkpoint_interval_steps=10)
        first_residuals = list(adapter._invariant_residuals["mass"])
        adapter.fit(_make_trajectories_43(10), steps=2, checkpoint_interval_steps=10)
        second_residuals = adapter._invariant_residuals["mass"]
        # second call must not accumulate on top of first — same length
        assert len(second_residuals) == len(first_residuals)


class TestComplianceReportStory44:
    """Story 4.4 — compliance_report() on DreamerV3Adapter (AC: #1, #2, #3, #4)."""

    def test_compliance_report_returns_compliance_report(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant, ComplianceReport

        adapter = _make_adapter_43()
        register_invariant(adapter, "mass", lambda t: 0.0, tolerance=0.01, mode="soft")
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        assert isinstance(adapter.compliance_report(), ComplianceReport)

    def test_compliance_report_no_side_effects(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "mass", lambda t: 0.0, tolerance=0.01, mode="soft")
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        report1 = adapter.compliance_report()
        report2 = adapter.compliance_report()
        assert report1.summary() == report2.summary()
        assert report1.violations() == report2.violations()

    def test_compliance_report_pass_when_no_violations(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "zero_inv", lambda t: 0.0, tolerance=0.01, mode="soft")
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        assert "PASS" in report.summary()

    def test_compliance_report_fail_when_violations(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        # residual=1.0 > tolerance=0.01, soft mode so no rejection
        register_invariant(adapter, "high_inv", lambda t: 1.0, tolerance=0.01, mode="soft")
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        assert "FAIL" in report.summary()

    def test_compliance_report_violations_list_non_empty_on_fail(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "violated", lambda t: 1.0, tolerance=0.01, mode="soft")
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        assert len(report.violations()) > 0

    def test_compliance_report_no_invariants_empty_report(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import ComplianceReport

        adapter = _make_adapter_43()
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        assert isinstance(report, ComplianceReport)
        assert report.summary() == ""
        assert report.violations() == []

    def test_compliance_report_before_fit_no_error(self) -> None:
        from physlink.core.validation import register_invariant, ComplianceReport

        adapter = _make_adapter_43()
        register_invariant(adapter, "mass", lambda t: 0.0, tolerance=0.01, mode="soft")
        # No fit() called — should return empty-zero report, not crash
        report = adapter.compliance_report()
        assert isinstance(report, ComplianceReport)
        summary = report.summary()
        assert "violations=0/0" in summary

    def test_compliance_report_hard_mode_violations_tracked(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        # keep index 0 (obs[0]=0.0 <= 4.0), reject indices 5-9
        register_invariant(
            adapter, "hard_inv", lambda t: float(t["obs"][0]), tolerance=4.0, mode="hard"
        )
        adapter.fit(_make_trajectories_43(10), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        # residuals stored for all 10 trajectories before filtering
        violations = report.violations()
        # trajectories with obs[0] > 4.0 (indices 5-9) should be violations
        assert len(violations) > 0
        assert all(v["invariant_name"] == "hard_inv" for v in violations)

    def test_compliance_report_possible_cause_contains_diagnostic_text(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "high_inv", lambda t: 1.0, tolerance=0.01, mode="soft")
        adapter.fit(_make_trajectories_43(3), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        for v in report.violations():
            cause = v["possible_cause"]
            assert isinstance(cause, str)
            assert "Residual" in cause
            assert "tolerance" in cause
            assert "Traceback" not in cause

    def test_compliance_report_violations_sorted_by_invariant_then_idx(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "zzz_inv", lambda t: 1.0, tolerance=0.01, mode="soft")
        register_invariant(adapter, "aaa_inv", lambda t: 1.0, tolerance=0.01, mode="soft")
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        violations = report.violations()
        assert len(violations) > 0
        names = [v["invariant_name"] for v in violations]
        assert names == sorted(names), "violations() must be sorted by invariant_name"


class TestComplianceReportStory45:
    """Story 4.5: residuals passed through to ComplianceReport via compliance_report()."""

    def test_compliance_report_has_residuals_by_invariant(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "mass_conservation", lambda t: 0.001, tolerance=0.01)
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        assert isinstance(report._residuals_by_invariant, dict)
        assert len(report._residuals_by_invariant) > 0

    def test_compliance_report_residuals_match_invariant_name(self) -> None:
        pytest.importorskip("torch")
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "mass_conservation", lambda t: 0.001, tolerance=0.01)
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        assert "mass_conservation" in report._residuals_by_invariant

    def test_compliance_report_export_produces_valid_json(self, tmp_path: "Path") -> None:
        pytest.importorskip("torch")
        import json
        from physlink.core.validation import register_invariant

        adapter = _make_adapter_43()
        register_invariant(adapter, "mass_conservation", lambda t: 0.001, tolerance=0.01)
        adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
        report = adapter.compliance_report()
        path = str(tmp_path / "report.json")
        report.export(path)
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, list)

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_compliance_report_plot_runs_via_adapter(self) -> None:
        pytest.importorskip("torch")
        import matplotlib.pyplot as plt
        from physlink.core.validation import register_invariant

        plt.switch_backend("Agg")
        try:
            adapter = _make_adapter_43()
            register_invariant(adapter, "mass_conservation", lambda t: 0.001, tolerance=0.01)
            adapter.fit(_make_trajectories_43(5), steps=2, checkpoint_interval_steps=10)
            report = adapter.compliance_report()
            report.plot()
        finally:
            plt.close("all")
