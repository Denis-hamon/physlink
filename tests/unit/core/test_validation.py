"""Tests for physlink.core.validation — register_invariant and ComplianceReport."""

from __future__ import annotations

import pytest

from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
from physlink.core.validation import register_invariant, ComplianceReport
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


def _make_pass_stats(name: str = "mass", total: int = 5) -> list[dict]:
    return [{"name": name, "max_residual": 0.0, "threshold": 0.01, "violation_count": 0, "total": total}]


def _make_fail_stats(name: str = "energy", violations: int = 2, total: int = 5) -> list[dict]:
    return [{"name": name, "max_residual": 0.9, "threshold": 0.01, "violation_count": violations, "total": total}]


def _make_violation_list(name: str = "energy", count: int = 2) -> list[dict]:
    return [
        {
            "invariant_name": name,
            "trajectory_idx": i,
            "residual": 0.5 + i * 0.1,
            "possible_cause": f"Residual {0.5 + i * 0.1:.4f} exceeds tolerance 0.0100.",
        }
        for i in range(count)
    ]


class TestComplianceReportSummaryPass:
    def test_summary_pass_format(self) -> None:
        report = ComplianceReport(
            _stats=[{"name": "mass", "max_residual": 0.0, "threshold": 0.01, "violation_count": 0, "total": 5}],
            _violation_list=[],
        )
        assert report.summary() == "mass: PASS (max_residual=0.0000, threshold=0.0100, violations=0/5)"

    def test_summary_deterministic(self) -> None:
        report = ComplianceReport(_stats=_make_pass_stats(), _violation_list=[])
        assert report.summary() == report.summary()

    def test_summary_zero_violations_contains_pass(self) -> None:
        report = ComplianceReport(_stats=_make_pass_stats(), _violation_list=[])
        assert "PASS" in report.summary()

    def test_summary_zero_violations_count(self) -> None:
        report = ComplianceReport(_stats=_make_pass_stats(), _violation_list=[])
        assert "violations=0/" in report.summary()


class TestComplianceReportSummaryFail:
    def test_summary_fail_format(self) -> None:
        report = ComplianceReport(_stats=_make_fail_stats(violations=2, total=5), _violation_list=[])
        summary = report.summary()
        assert "FAIL" in summary
        assert "violations=2/5" in summary

    def test_summary_fail_max_residual(self) -> None:
        stats = [{"name": "e", "max_residual": 0.75, "threshold": 0.01, "violation_count": 1, "total": 3}]
        report = ComplianceReport(_stats=stats, _violation_list=[])
        assert "max_residual=0.7500" in report.summary()


class TestComplianceReportViolations:
    def test_violations_returns_list(self) -> None:
        report = ComplianceReport(_stats=_make_fail_stats(), _violation_list=_make_violation_list())
        assert isinstance(report.violations(), list)

    def test_violations_entry_keys(self) -> None:
        report = ComplianceReport(_stats=_make_fail_stats(), _violation_list=_make_violation_list(count=1))
        entry = report.violations()[0]
        assert "invariant_name" in entry
        assert "trajectory_idx" in entry
        assert "residual" in entry
        assert "possible_cause" in entry

    def test_violations_no_stack_trace_in_possible_cause(self) -> None:
        report = ComplianceReport(_stats=_make_fail_stats(), _violation_list=_make_violation_list(count=2))
        for v in report.violations():
            assert "Traceback" not in v["possible_cause"]

    def test_violations_trajectory_idx_matches(self) -> None:
        vlist = [{"invariant_name": "m", "trajectory_idx": 3, "residual": 0.5, "possible_cause": "x"}]
        report = ComplianceReport(_stats=_make_pass_stats("m"), _violation_list=vlist)
        assert report.violations()[0]["trajectory_idx"] == 3

    def test_violations_residual_value_correct(self) -> None:
        vlist = [{"invariant_name": "m", "trajectory_idx": 0, "residual": 0.123, "possible_cause": "x"}]
        report = ComplianceReport(_stats=_make_pass_stats("m"), _violation_list=vlist)
        assert report.violations()[0]["residual"] == 0.123

    def test_violations_deterministic(self) -> None:
        report = ComplianceReport(_stats=_make_fail_stats(), _violation_list=_make_violation_list(count=3))
        assert report.violations() == report.violations()


class TestComplianceReportEmpty:
    def test_empty_stats_summary(self) -> None:
        report = ComplianceReport(_stats=[], _violation_list=[])
        assert report.summary() == ""

    def test_empty_violations(self) -> None:
        report = ComplianceReport(_stats=[], _violation_list=[])
        assert report.violations() == []


class TestComplianceReportMultiInvariant:
    def test_summary_multi_invariant_multiline(self) -> None:
        stats = [
            {"name": "mass", "max_residual": 0.0, "threshold": 0.01, "violation_count": 0, "total": 5},
            {"name": "energy", "max_residual": 0.5, "threshold": 0.01, "violation_count": 2, "total": 5},
        ]
        report = ComplianceReport(_stats=stats, _violation_list=[])
        lines = report.summary().splitlines()
        assert len(lines) == 2

    def test_violations_multi_invariant_combined(self) -> None:
        vlist = [
            {"invariant_name": "mass", "trajectory_idx": 0, "residual": 0.5, "possible_cause": "x"},
            {"invariant_name": "energy", "trajectory_idx": 1, "residual": 0.6, "possible_cause": "y"},
        ]
        report = ComplianceReport(_stats=[], _violation_list=vlist)
        names = {v["invariant_name"] for v in report.violations()}
        assert "mass" in names
        assert "energy" in names

    def test_summary_lines_in_insertion_order(self) -> None:
        stats = [
            {"name": "zzz_last", "max_residual": 0.0, "threshold": 0.01, "violation_count": 0, "total": 3},
            {"name": "aaa_first", "max_residual": 0.0, "threshold": 0.01, "violation_count": 0, "total": 3},
        ]
        report = ComplianceReport(_stats=stats, _violation_list=[])
        lines = report.summary().splitlines()
        assert lines[0].startswith("zzz_last:")
        assert lines[1].startswith("aaa_first:")

    def test_violations_total_count_across_invariants(self) -> None:
        vlist = [
            {"invariant_name": "mass", "trajectory_idx": 0, "residual": 0.5, "possible_cause": "a"},
            {"invariant_name": "mass", "trajectory_idx": 2, "residual": 0.6, "possible_cause": "b"},
            {"invariant_name": "energy", "trajectory_idx": 1, "residual": 0.7, "possible_cause": "c"},
        ]
        report = ComplianceReport(_stats=[], _violation_list=vlist)
        assert len(report.violations()) == 3


class TestComplianceReportDefensiveCopy:
    def test_stats_mutation_after_construction_does_not_affect_summary(self) -> None:
        original_stats = [{"name": "mass", "max_residual": 0.0, "threshold": 0.01, "violation_count": 0, "total": 5}]
        report = ComplianceReport(_stats=original_stats, _violation_list=[])
        summary_before = report.summary()
        original_stats.clear()
        assert report.summary() == summary_before

    def test_violation_list_mutation_after_construction_does_not_affect_violations(self) -> None:
        original_vlist = [{"invariant_name": "m", "trajectory_idx": 0, "residual": 0.5, "possible_cause": "x"}]
        report = ComplianceReport(_stats=[], _violation_list=original_vlist)
        violations_before = report.violations()
        original_vlist.clear()
        assert report.violations() == violations_before

    def test_violations_returns_new_list_each_call(self) -> None:
        vlist = [{"invariant_name": "m", "trajectory_idx": 0, "residual": 0.5, "possible_cause": "x"}]
        report = ComplianceReport(_stats=[], _violation_list=vlist)
        v1 = report.violations()
        v2 = report.violations()
        assert v1 is not v2


class TestComplianceReportSortingOrder:
    def test_violations_sorted_by_invariant_name_then_idx(self) -> None:
        vlist = [
            {"invariant_name": "zzz", "trajectory_idx": 0, "residual": 0.5, "possible_cause": "a"},
            {"invariant_name": "aaa", "trajectory_idx": 5, "residual": 0.6, "possible_cause": "b"},
            {"invariant_name": "aaa", "trajectory_idx": 2, "residual": 0.7, "possible_cause": "c"},
        ]
        report = ComplianceReport(_stats=[], _violation_list=vlist)
        result = report.violations()
        assert result[0]["invariant_name"] == "aaa"
        assert result[0]["trajectory_idx"] == 2
        assert result[1]["invariant_name"] == "aaa"
        assert result[1]["trajectory_idx"] == 5
        assert result[2]["invariant_name"] == "zzz"
        assert result[2]["trajectory_idx"] == 0

    def test_violations_same_invariant_sorted_by_idx(self) -> None:
        vlist = [
            {"invariant_name": "mass", "trajectory_idx": 9, "residual": 0.5, "possible_cause": "a"},
            {"invariant_name": "mass", "trajectory_idx": 1, "residual": 0.6, "possible_cause": "b"},
            {"invariant_name": "mass", "trajectory_idx": 4, "residual": 0.7, "possible_cause": "c"},
        ]
        report = ComplianceReport(_stats=[], _violation_list=vlist)
        idxs = [v["trajectory_idx"] for v in report.violations()]
        assert idxs == sorted(idxs)


class TestComplianceReportPossibleCause:
    def test_violations_possible_cause_is_nonempty_string(self) -> None:
        vlist = [{"invariant_name": "m", "trajectory_idx": 0, "residual": 0.5, "possible_cause": "some cause"}]
        report = ComplianceReport(_stats=[], _violation_list=vlist)
        for v in report.violations():
            assert isinstance(v["possible_cause"], str)
            assert len(v["possible_cause"]) > 0
