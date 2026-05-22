"""Tests for physlink.core.validation — register_invariant."""

from __future__ import annotations

import pytest

from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
from physlink.core.validation import register_invariant
from physlink.core.exceptions import ConfigurationError, ValidationError


def _make_adapter() -> DreamerV3Adapter:
    obs = ObservationSpace.from_proprioception(joints=7, include_velocity=False)
    act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
    return DreamerV3Adapter(obs, act)


def _fn_valid(trajectory: dict) -> float:
    return 0.0


class TestRegisterInvariantSuccess:
    def test_attach_valid_fn(self) -> None:
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        assert len(adapter._invariants) == 1

    def test_attach_sets_name(self) -> None:
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        assert adapter._invariants[0].name == "mass"

    def test_attach_sets_mode_default_soft(self) -> None:
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        assert adapter._invariants[0].mode == "soft"

    def test_attach_hard_mode(self) -> None:
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="hard")
        assert adapter._invariants[0].mode == "hard"

    def test_attach_multiple_invariants(self) -> None:
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        register_invariant(adapter, "energy", _fn_valid, tolerance=0.05, mode="hard")
        assert len(adapter._invariants) == 2

    def test_no_subclassing_required(self) -> None:
        adapter = _make_adapter()

        def raw_fn(t: dict) -> float:
            return abs(t.get("x", 0.0))

        register_invariant(adapter, "pos", raw_fn, tolerance=1.0)
        assert len(adapter._invariants) == 1

    def test_attach_sets_tolerance(self) -> None:
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.05)
        assert adapter._invariants[0].tolerance == 0.05

    def test_attach_stores_fn(self) -> None:
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        assert adapter._invariants[0].fn is _fn_valid


class TestRegisterInvariantMultiple:
    def test_two_invariants_both_stored(self) -> None:
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.01)
        register_invariant(adapter, "energy", _fn_valid, tolerance=0.05, mode="hard")
        names = [inv.name for inv in adapter._invariants]
        assert "mass" in names
        assert "energy" in names


class TestRegisterInvariantInvalidFn:
    def test_two_params_raises(self) -> None:
        adapter = _make_adapter()

        def bad(pressure, volume):  # noqa: ANN001, ANN202
            return 0.0

        with pytest.raises(ValidationError) as exc_info:
            register_invariant(adapter, "bad", bad, tolerance=0.01)
        assert "bad" in str(exc_info.value)
        assert "fn(trajectory: dict) -> float" in str(exc_info.value)

    def test_zero_params_raises(self) -> None:
        adapter = _make_adapter()

        def no_params():  # noqa: ANN202
            return 0.0

        with pytest.raises(ValidationError):
            register_invariant(adapter, "no_params", no_params, tolerance=0.01)

    def test_error_message_contains_fn_name(self) -> None:
        adapter = _make_adapter()

        def check_pressure(p, v):  # noqa: ANN001, ANN202
            return 0.0

        with pytest.raises(ValidationError) as exc_info:
            register_invariant(adapter, "check_pressure", check_pressure, tolerance=0.01)
        assert "check_pressure" in str(exc_info.value)
        assert "Got:" in str(exc_info.value)
        assert "Fix:" in str(exc_info.value)

    def test_error_raised_immediately_not_at_fit(self) -> None:
        adapter = _make_adapter()

        def bad(a, b):  # noqa: ANN001, ANN202
            return 0.0

        with pytest.raises(ValidationError):
            register_invariant(adapter, "bad", bad, tolerance=0.01)
        assert len(adapter._invariants) == 0


class TestRegisterInvariantInvalidMode:
    def test_medium_raises(self) -> None:
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError) as exc_info:
            register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="medium")  # type: ignore[arg-type]
        assert "medium" in str(exc_info.value)
        assert "hard" in str(exc_info.value)
        assert "soft" in str(exc_info.value)

    def test_uppercase_hard_raises(self) -> None:
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError):
            register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="HARD")  # type: ignore[arg-type]

    def test_empty_mode_raises(self) -> None:
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError):
            register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="")  # type: ignore[arg-type]

    def test_got_expected_fix_in_message(self) -> None:
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError) as exc_info:
            register_invariant(adapter, "mass", _fn_valid, tolerance=0.01, mode="medium")  # type: ignore[arg-type]
        msg = str(exc_info.value)
        assert "Got:" in msg
        assert "Expected:" in msg
        assert "Fix:" in msg


class TestRegisterInvariantNegativeTolerance:
    def test_negative_tolerance_raises(self) -> None:
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError):
            register_invariant(adapter, "mass", _fn_valid, tolerance=-0.01)

    def test_zero_tolerance_accepted(self) -> None:
        adapter = _make_adapter()
        register_invariant(adapter, "mass", _fn_valid, tolerance=0.0)
        assert len(adapter._invariants) == 1

    def test_negative_tolerance_error_has_got_expected_fix(self) -> None:
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError) as exc_info:
            register_invariant(adapter, "mass", _fn_valid, tolerance=-0.5)
        msg = str(exc_info.value)
        assert "Got:" in msg
        assert "Expected:" in msg
        assert "Fix:" in msg

    def test_negative_tolerance_error_contains_value(self) -> None:
        adapter = _make_adapter()
        with pytest.raises(ConfigurationError) as exc_info:
            register_invariant(adapter, "mass", _fn_valid, tolerance=-0.99)
        assert "-0.99" in str(exc_info.value)


class TestRegisterInvariantValidationOrder:
    """Validate that mode → tolerance → fn signature is the enforcement order."""

    def test_mode_error_fires_before_fn_signature_error(self) -> None:
        adapter = _make_adapter()

        def bad(a, b):  # noqa: ANN001, ANN202
            return 0.0

        with pytest.raises(ConfigurationError):
            register_invariant(adapter, "mass", bad, tolerance=0.01, mode="invalid")  # type: ignore[arg-type]

    def test_tolerance_error_fires_before_fn_signature_error(self) -> None:
        adapter = _make_adapter()

        def bad(a, b):  # noqa: ANN001, ANN202
            return 0.0

        with pytest.raises(ConfigurationError):
            register_invariant(adapter, "mass", bad, tolerance=-1.0)


class TestRegisterInvariantErrorContent:
    """Verify rich diagnostic content in ValidationError messages (AC #4 / UX-DR-12)."""

    def test_got_line_shows_actual_parameter_names(self) -> None:
        adapter = _make_adapter()

        def check_pressure(pressure, volume):  # noqa: ANN001, ANN202
            return 0.0

        with pytest.raises(ValidationError) as exc_info:
            register_invariant(adapter, "check_pressure", check_pressure, tolerance=0.01)
        msg = str(exc_info.value)
        assert "pressure" in msg
        assert "volume" in msg

    def test_expected_line_shows_correct_signature(self) -> None:
        adapter = _make_adapter()

        def bad(a, b):  # noqa: ANN001, ANN202
            return 0.0

        with pytest.raises(ValidationError) as exc_info:
            register_invariant(adapter, "bad", bad, tolerance=0.01)
        assert "fn(trajectory: dict) -> float" in str(exc_info.value)
