"""Unit tests for physlink.core.spaces.ObservationSpace."""

from __future__ import annotations

import inspect

import pytest

from physlink.core.exceptions import ValidationError
from physlink.core.spaces import ObservationSpace


class TestObservationSpaceFromProprioception:
    def test_valid_construction_7dof(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=False)
        assert isinstance(result, ObservationSpace)

    def test_valid_construction_with_velocity(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        assert result.dims == 14

    def test_dims_without_velocity_equals_joints(self) -> None:
        assert ObservationSpace.from_proprioception(joints=3).dims == 3

    def test_dims_with_velocity_doubles(self) -> None:
        assert ObservationSpace.from_proprioception(joints=5, include_velocity=True).dims == 10

    def test_stores_joints_attribute(self) -> None:
        assert ObservationSpace.from_proprioception(joints=7)._joints == 7

    def test_stores_velocity_flag(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        assert result.include_velocity is True

    def test_default_include_velocity_is_false(self) -> None:
        assert ObservationSpace.from_proprioception(joints=7).include_velocity is False

    def test_clip_bounds_default_none(self) -> None:
        assert ObservationSpace.from_proprioception(joints=7).clip_bounds is None

    def test_clip_bounds_stored(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, clip_bounds=(-1.0, 1.0))
        assert result.clip_bounds == (-1.0, 1.0)

    def test_normalize_default_false(self) -> None:
        assert ObservationSpace.from_proprioception(joints=7).normalize is False

    def test_normalize_stored_true(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, normalize=True)
        assert result.normalize is True


class TestObservationSpaceValidation:
    def test_zero_joints_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ObservationSpace.from_proprioception(joints=0)

    def test_negative_joints_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ObservationSpace.from_proprioception(joints=-1)

    def test_string_joints_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ObservationSpace.from_proprioception(joints="seven")  # type: ignore[arg-type]

    def test_float_joints_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ObservationSpace.from_proprioception(joints=7.0)  # type: ignore[arg-type]

    def test_bool_joints_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ObservationSpace.from_proprioception(joints=True)

    def test_false_bool_joints_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ObservationSpace.from_proprioception(joints=False)

    def test_none_joints_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ObservationSpace.from_proprioception(joints=None)  # type: ignore[arg-type]

    def test_zero_joints_error_message_got_expected_fix(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ObservationSpace.from_proprioception(joints=0)
        msg = str(exc_info.value)
        assert "Got" in msg
        assert "Expected" in msg
        assert "Fix" in msg

    def test_zero_joints_error_message_contains_value(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ObservationSpace.from_proprioception(joints=0)
        assert "joints=0" in str(exc_info.value)

    def test_negative_joints_error_message_got_expected_fix(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ObservationSpace.from_proprioception(joints=-1)
        msg = str(exc_info.value)
        assert "Got" in msg
        assert "Expected" in msg
        assert "Fix" in msg

    def test_string_joints_error_message_contains_type(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ObservationSpace.from_proprioception(joints="seven")  # type: ignore[arg-type]
        assert "str" in str(exc_info.value)

    def test_string_joints_error_message_got_expected_fix(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ObservationSpace.from_proprioception(joints="seven")  # type: ignore[arg-type]
        msg = str(exc_info.value)
        assert "Got" in msg
        assert "Expected" in msg
        assert "Fix" in msg


class TestObservationSpaceInterface:
    def test_repr_contains_dims(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7)
        assert "dims=7" in repr(result)

    def test_repr_contains_velocity(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7)
        assert "velocity=False" in repr(result)

    def test_repr_with_velocity_true(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        assert "velocity=True" in repr(result)

    def test_idempotent_construction(self) -> None:
        a = ObservationSpace.from_proprioception(joints=5, include_velocity=True)
        b = ObservationSpace.from_proprioception(joints=5, include_velocity=True)
        assert a.dims == b.dims


class TestObservationSpaceNoTorch:
    def test_no_torch_in_from_proprioception_signature(self) -> None:
        assert "torch" not in str(inspect.signature(ObservationSpace.from_proprioception))
