"""Unit tests for physlink.core.spaces — ObservationSpace and ActionSpace."""

from __future__ import annotations

import inspect
import json

import pytest

from physlink.core.exceptions import ValidationError
from physlink.core.spaces import ActionSpace, ObservationSpace


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


class TestActionSpaceContinuous:
    def test_valid_construction_7dof(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        assert isinstance(result, ActionSpace)

    def test_stores_dims(self) -> None:
        assert ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).dims == 7

    def test_stores_bounds(self) -> None:
        assert ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3).bounds == [(-1.0, 1.0)] * 3

    def test_asymmetric_bounds(self) -> None:
        result = ActionSpace.continuous(dims=2, bounds=[(-2.0, 2.0), (0.0, 1.0)])
        assert isinstance(result, ActionSpace)

    def test_single_dim(self) -> None:
        result = ActionSpace.continuous(dims=1, bounds=[(0.0, 1.0)])
        assert isinstance(result, ActionSpace)

    def test_equal_min_max_bounds(self) -> None:
        result = ActionSpace.continuous(dims=1, bounds=[(0.5, 0.5)])
        assert isinstance(result, ActionSpace)

    def test_negative_bounds(self) -> None:
        result = ActionSpace.continuous(dims=2, bounds=[(-5.0, -1.0), (-3.0, 0.0)])
        assert isinstance(result, ActionSpace)


class TestActionSpaceValidation:
    def test_bounds_length_mismatch_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 3)

    def test_bounds_length_mismatch_message_got(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 3)
        assert "3 bounds" in str(exc_info.value)

    def test_bounds_length_mismatch_message_expected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 3)
        assert "7 bounds" in str(exc_info.value)

    def test_bounds_length_mismatch_message_fix(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 3)
        assert "Fix" in str(exc_info.value)

    def test_zero_dims_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=0, bounds=[])

    def test_negative_dims_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=-1, bounds=[])

    def test_string_dims_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims="seven", bounds=[(-1.0, 1.0)] * 7)  # type: ignore[arg-type]

    def test_float_dims_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=7.0, bounds=[(-1.0, 1.0)] * 7)  # type: ignore[arg-type]

    def test_bool_dims_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=True, bounds=[(-1.0, 1.0)])

    def test_false_bool_dims_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=False, bounds=[])

    def test_none_dims_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=None, bounds=[(-1.0, 1.0)])  # type: ignore[arg-type]

    def test_non_list_bounds_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=7, bounds=((-1.0, 1.0),) * 7)  # type: ignore[arg-type]

    def test_inverted_bound_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=1, bounds=[(1.0, -1.0)])

    def test_inverted_bound_error_message_contains_fix(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims=1, bounds=[(1.0, -1.0)])
        assert "Fix" in str(exc_info.value)

    def test_dims_error_message_got_expected_fix(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims=0, bounds=[])
        msg = str(exc_info.value)
        assert "Got" in msg
        assert "Expected" in msg
        assert "Fix" in msg

    def test_string_dims_error_message_contains_type(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims="seven", bounds=[])  # type: ignore[arg-type]
        assert "str" in str(exc_info.value)


class TestActionSpaceInterface:
    def test_repr_contains_dims(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        assert "dims=7" in repr(result)

    def test_idempotent_construction(self) -> None:
        a = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3)
        b = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3)
        assert a.dims == b.dims
        assert a.bounds == b.bounds


class TestActionSpaceNoTorch:
    def test_no_torch_in_continuous_signature(self) -> None:
        assert "torch" not in str(inspect.signature(ActionSpace.continuous))


class TestActionSpaceGaps:
    """Gap tests discovered by QA audit — AC coverage, edge cases, and contract invariants."""

    # --- bound sub-element size ---

    def test_bound_single_element_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=1, bounds=[(1.0,)])  # type: ignore[arg-type]

    def test_bound_three_elements_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=1, bounds=[(1.0, 2.0, 3.0)])  # type: ignore[arg-type]

    def test_non_sequence_bound_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=1, bounds=[42])  # type: ignore[arg-type]

    # --- mismatch direction: more bounds than dims ---

    def test_bounds_length_excess_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 7)

    def test_bounds_length_excess_message_got(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 7)
        assert "7 bounds" in str(exc_info.value)

    def test_bounds_length_excess_message_expected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 7)
        assert "3 bounds" in str(exc_info.value)

    # --- inverted bound error message completeness ---

    def test_inverted_bound_error_message_got(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims=1, bounds=[(1.0, -1.0)])
        assert "Got" in str(exc_info.value)

    def test_inverted_bound_error_message_expected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ActionSpace.continuous(dims=1, bounds=[(1.0, -1.0)])
        assert "Expected" in str(exc_info.value)

    def test_inverted_bound_at_non_zero_index(self) -> None:
        with pytest.raises(ValidationError):
            ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0), (-1.0, 1.0), (1.0, -1.0)])

    # --- object independence (NFR-09 idempotency) ---

    def test_idempotent_construction_returns_independent_objects(self) -> None:
        a = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3)
        b = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3)
        assert a is not b

    # --- repr exact format ---

    def test_repr_exact_format(self) -> None:
        result = ActionSpace.continuous(dims=5, bounds=[(-1.0, 1.0)] * 5)
        assert repr(result) == "ActionSpace(dims=5)"

    def test_repr_starts_with_class_name(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        assert repr(result).startswith("ActionSpace(")

    # --- scale test ---

    def test_large_dims_100dof(self) -> None:
        result = ActionSpace.continuous(dims=100, bounds=[(-1.0, 1.0)] * 100)
        assert result.dims == 100
        assert len(result.bounds) == 100

    # --- attribute type guarantee ---

    def test_bounds_attribute_is_list(self) -> None:
        result = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3)
        assert isinstance(result.bounds, list)

    # --- mixed int/float bounds ---

    def test_mixed_int_float_bounds_succeed(self) -> None:
        result = ActionSpace.continuous(dims=1, bounds=[(0, 1.0)])  # type: ignore[list-item]
        assert isinstance(result, ActionSpace)


class TestObservationSpaceExplain:
    def test_explain_returns_dict(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True).explain()
        assert isinstance(result, dict)

    def test_explain_contains_dims_key(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True).explain()
        assert "dims" in result

    def test_explain_dims_value_with_velocity(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True).explain()
        assert result["dims"] == 14

    def test_explain_dims_value_without_velocity(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=False).explain()
        assert result["dims"] == 7

    def test_explain_contains_joints_key(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True).explain()
        assert "joints" in result

    def test_explain_joints_raw_value(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True).explain()
        assert result["joints"] == 7

    def test_explain_contains_include_velocity(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True).explain()
        assert "include_velocity" in result
        assert result["include_velocity"] is True

    def test_explain_clip_bounds_none_when_not_set(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7).explain()
        assert result["clip_bounds"] is None

    def test_explain_clip_bounds_when_set(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, clip_bounds=(-1.0, 1.0)).explain()
        assert result["clip_bounds"] == [-1.0, 1.0]

    def test_explain_normalize_false_default(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7).explain()
        assert result["normalize"] is False

    def test_explain_normalize_true_when_set(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, normalize=True).explain()
        assert result["normalize"] is True

    def test_explain_json_serializable(self) -> None:
        obs = ObservationSpace.from_proprioception(
            joints=7, include_velocity=True, clip_bounds=(-1.0, 1.0)
        )
        json.dumps(obs.explain())  # must not raise

    def test_explain_not_string(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7).explain()
        assert isinstance(result, dict)
        assert not isinstance(result, str)


class TestActionSpaceExplain:
    def test_explain_returns_dict(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()
        assert isinstance(result, dict)

    def test_explain_contains_dims_key(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()
        assert "dims" in result

    def test_explain_dims_value(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()
        assert result["dims"] == 7

    def test_explain_contains_bounds_key(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()
        assert "bounds" in result

    def test_explain_bounds_length(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()
        assert len(result["bounds"]) == 7

    def test_explain_bounds_values(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()
        assert result["bounds"][0] == [-1.0, 1.0]

    def test_explain_bounds_are_lists_not_tuples(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()
        for item in result["bounds"]:
            assert isinstance(item, list)

    def test_explain_json_serializable(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()
        json.dumps(result)  # must not raise

    def test_explain_not_none(self) -> None:
        result = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7).explain()
        assert result is not None

    def test_explain_asymmetric_bounds(self) -> None:
        result = ActionSpace.continuous(dims=2, bounds=[(-2.0, 2.0), (0.0, 1.0)]).explain()
        assert result["bounds"] == [[-2.0, 2.0], [0.0, 1.0]]


class TestObservationSpaceExplainGaps:
    """Gap tests for explain() — contract keys, type invariants, and NFR-09 idempotency."""

    def test_explain_type_key_exists(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7).explain()
        assert "type" in result

    def test_explain_type_value(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7).explain()
        assert result["type"] == "ObservationSpace"

    def test_explain_normalize_key_exists(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7).explain()
        assert "normalize" in result

    def test_explain_clip_bounds_key_exists(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7).explain()
        assert "clip_bounds" in result

    def test_explain_clip_bounds_is_list_when_set(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, clip_bounds=(-1.0, 1.0)).explain()
        assert isinstance(result["clip_bounds"], list)

    def test_explain_all_expected_keys_present(self) -> None:
        result = ObservationSpace.from_proprioception(joints=7, include_velocity=True).explain()
        expected_keys = {"type", "dims", "joints", "include_velocity", "clip_bounds", "normalize"}
        assert set(result.keys()) == expected_keys

    def test_explain_idempotent(self) -> None:
        obs = ObservationSpace.from_proprioception(joints=5, include_velocity=True, normalize=True)
        assert obs.explain() == obs.explain()

    def test_explain_minimum_joints(self) -> None:
        result = ObservationSpace.from_proprioception(joints=1).explain()
        assert result["dims"] == 1
        assert result["joints"] == 1

    def test_explain_clip_bounds_with_normalize_true(self) -> None:
        result = ObservationSpace.from_proprioception(
            joints=3, clip_bounds=(-2.0, 2.0), normalize=True
        ).explain()
        assert result["clip_bounds"] == [-2.0, 2.0]
        assert result["normalize"] is True
        assert result["dims"] == 3


class TestActionSpaceExplainGaps:
    """Gap tests for explain() — contract keys, clipping_behavior, and NFR-09 idempotency."""

    def test_explain_type_key_exists(self) -> None:
        result = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3).explain()
        assert "type" in result

    def test_explain_type_value(self) -> None:
        result = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3).explain()
        assert result["type"] == "ActionSpace"

    def test_explain_clipping_behavior_key_exists(self) -> None:
        result = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3).explain()
        assert "clipping_behavior" in result

    def test_explain_clipping_behavior_value(self) -> None:
        result = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3).explain()
        assert result["clipping_behavior"] == "per_dimension"

    def test_explain_all_expected_keys_present(self) -> None:
        result = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3).explain()
        expected_keys = {"type", "dims", "bounds", "clipping_behavior"}
        assert set(result.keys()) == expected_keys

    def test_explain_idempotent(self) -> None:
        act = ActionSpace.continuous(dims=4, bounds=[(-1.0, 1.0)] * 4)
        assert act.explain() == act.explain()

    def test_explain_minimum_dims(self) -> None:
        result = ActionSpace.continuous(dims=1, bounds=[(0.0, 1.0)]).explain()
        assert result["dims"] == 1
        assert result["bounds"] == [[0.0, 1.0]]

    def test_explain_clipping_behavior_is_string(self) -> None:
        result = ActionSpace.continuous(dims=2, bounds=[(-1.0, 1.0)] * 2).explain()
        assert isinstance(result["clipping_behavior"], str)
