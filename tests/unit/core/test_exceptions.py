"""Unit tests for physlink.core.exceptions hierarchy."""

from __future__ import annotations

import pytest

from physlink.core.exceptions import (
    AdapterError,
    CheckpointCorruptError,
    CheckpointError,
    CheckpointVersionError,
    ConfigurationError,
    PhysLinkError,
    ValidationError,
)


class TestInheritanceChain:
    def test_configuration_error_is_physlink_error(self) -> None:
        assert issubclass(ConfigurationError, PhysLinkError)

    def test_validation_error_is_physlink_error(self) -> None:
        assert issubclass(ValidationError, PhysLinkError)

    def test_adapter_error_is_physlink_error(self) -> None:
        assert issubclass(AdapterError, PhysLinkError)

    def test_checkpoint_error_is_physlink_error_not_adapter_error(self) -> None:
        assert issubclass(CheckpointError, PhysLinkError)
        assert not issubclass(CheckpointError, AdapterError)  # critical: NOT via AdapterError

    def test_checkpoint_corrupt_error_is_checkpoint_error(self) -> None:
        assert issubclass(CheckpointCorruptError, CheckpointError)

    def test_checkpoint_version_error_is_checkpoint_error(self) -> None:
        assert issubclass(CheckpointVersionError, CheckpointError)

    def test_physlink_error_is_exception(self) -> None:
        assert issubclass(PhysLinkError, Exception)


class TestCheckpointVersionErrorAttributes:
    def test_attributes_accessible_after_raise(self) -> None:
        with pytest.raises(CheckpointVersionError) as exc_info:
            raise CheckpointVersionError(
                "version mismatch.\n  Got: 0.1.0\n  Expected: 0.2.0\n  Fix: re-run fit()",
                checkpoint_version="0.1.0",
                current_version="0.2.0",
            )
        assert exc_info.value.checkpoint_version == "0.1.0"
        assert exc_info.value.current_version == "0.2.0"

    def test_message_preserved(self) -> None:
        err = CheckpointVersionError(
            "test message",
            checkpoint_version="0.1.0",
            current_version="0.2.0",
        )
        assert "test message" in str(err)


class TestGotExpectedFixFormat:
    def test_configuration_error_message_format(self) -> None:
        msg = (
            "DreamerV3Adapter: bad obs_dims.\n"
            "  Got:      obs_dims=0\n"
            "  Expected: obs_dims >= 1\n"
            "  Fix:      use joints >= 1 when constructing ObservationSpace."
        )
        err = ConfigurationError(msg)
        assert "Got:" in str(err)
        assert "Expected:" in str(err)
        assert "Fix:" in str(err)

    def test_validation_error_catchable_as_physlink_error(self) -> None:
        with pytest.raises(PhysLinkError):
            raise ValidationError(
                "joints=0.\n  Got: 0\n  Expected: >= 1\n  Fix: use positive int."
            )


class TestCheckpointVersionErrorKeywordOnly:
    def test_positional_checkpoint_version_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            CheckpointVersionError("msg", "0.1.0", "0.2.0")  # type: ignore[misc]

    def test_missing_checkpoint_version_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            CheckpointVersionError("msg", current_version="0.2.0")  # type: ignore[call-arg]

    def test_missing_current_version_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            CheckpointVersionError("msg", checkpoint_version="0.1.0")  # type: ignore[call-arg]


class TestRaiseAndCatch:
    def test_adapter_error_catchable_as_physlink_error(self) -> None:
        with pytest.raises(PhysLinkError):
            raise AdapterError(
                "write failed.\n  Got: PermissionError\n  Expected: writable path\n  Fix: check permissions."
            )

    def test_checkpoint_error_catchable_as_physlink_error(self) -> None:
        with pytest.raises(PhysLinkError):
            raise CheckpointError("Got: corrupt\n  Expected: valid\n  Fix: re-run fit.")

    def test_checkpoint_corrupt_error_catchable_as_checkpoint_error(self) -> None:
        with pytest.raises(CheckpointError):
            raise CheckpointCorruptError(
                "Got: missing metadata\n  Expected: valid safetensors\n  Fix: re-run fit."
            )

    def test_checkpoint_version_error_catchable_as_checkpoint_error(self) -> None:
        with pytest.raises(CheckpointError):
            raise CheckpointVersionError(
                "Got: 0.1.0\n  Expected: 0.2.0\n  Fix: re-run fit.",
                checkpoint_version="0.1.0",
                current_version="0.2.0",
            )

    def test_all_seven_catchable_as_physlink_error(self) -> None:
        exceptions = [
            PhysLinkError("Got: x\n  Expected: y\n  Fix: z"),
            ConfigurationError("Got: x\n  Expected: y\n  Fix: z"),
            ValidationError("Got: x\n  Expected: y\n  Fix: z"),
            AdapterError("Got: x\n  Expected: y\n  Fix: z"),
            CheckpointError("Got: x\n  Expected: y\n  Fix: z"),
            CheckpointCorruptError("Got: x\n  Expected: y\n  Fix: z"),
            CheckpointVersionError(
                "Got: x\n  Expected: y\n  Fix: z",
                checkpoint_version="0.1.0",
                current_version="0.2.0",
            ),
        ]
        for exc in exceptions:
            assert isinstance(exc, PhysLinkError), f"{type(exc).__name__} must be a PhysLinkError"

    def test_checkpoint_error_not_caught_as_adapter_error(self) -> None:
        with pytest.raises(PhysLinkError):
            try:
                raise CheckpointError("Got: x\n  Expected: y\n  Fix: z")
            except AdapterError:
                pytest.fail("CheckpointError should NOT be caught as AdapterError")


class TestGotExpectedFixFormatAllClasses:
    def test_validation_error_message_format(self) -> None:
        msg = "joints=0.\n  Got: 0\n  Expected: >= 1\n  Fix: pass joints >= 1."
        err = ValidationError(msg)
        assert "Got:" in str(err)
        assert "Expected:" in str(err)
        assert "Fix:" in str(err)

    def test_adapter_error_message_format(self) -> None:
        msg = (
            "write failed.\n"
            "  Got:      PermissionError on /read-only/path\n"
            "  Expected: writable path\n"
            "  Fix:      choose a path with write permissions."
        )
        err = AdapterError(msg)
        assert "Got:" in str(err)
        assert "Expected:" in str(err)
        assert "Fix:" in str(err)

    def test_checkpoint_corrupt_error_message_format(self) -> None:
        msg = (
            "checkpoint_step_1000.safetensors: malformed.\n"
            "  Got:      metadata block absent\n"
            "  Expected: valid safetensors file\n"
            "  Fix:      re-run adapter.fit() to regenerate."
        )
        err = CheckpointCorruptError(msg)
        assert "Got:" in str(err)
        assert "Expected:" in str(err)
        assert "Fix:" in str(err)

    def test_checkpoint_version_error_message_format(self) -> None:
        err = CheckpointVersionError(
            "mismatch.\n  Got: 0.1.0\n  Expected: 0.2.0\n  Fix: re-run fit.",
            checkpoint_version="0.1.0",
            current_version="0.2.0",
        )
        assert "Got:" in str(err)
        assert "Expected:" in str(err)
        assert "Fix:" in str(err)


class TestCheckpointVersionErrorStrRepr:
    def test_str_contains_version_mismatch_context(self) -> None:
        err = CheckpointVersionError(
            "Checkpoint mismatch.\n  Got: 0.1.0\n  Expected: 0.2.0\n  Fix: re-run fit.",
            checkpoint_version="0.1.0",
            current_version="0.2.0",
        )
        assert err.checkpoint_version == "0.1.0"
        assert err.current_version == "0.2.0"
        assert "0.1.0" in str(err)
        assert "0.2.0" in str(err)

    def test_attributes_independent_of_message_content(self) -> None:
        err = CheckpointVersionError(
            "no version in msg",
            checkpoint_version="1.5.0",
            current_version="2.0.0",
        )
        assert err.checkpoint_version == "1.5.0"
        assert err.current_version == "2.0.0"


class TestGotExpectedFixFormatBaseClasses:
    def test_physlink_error_base_message_format(self) -> None:
        msg = "Got: bad value\n  Expected: valid value\n  Fix: pass a valid value."
        err = PhysLinkError(msg)
        assert "Got:" in str(err)
        assert "Expected:" in str(err)
        assert "Fix:" in str(err)

    def test_checkpoint_error_base_message_format(self) -> None:
        msg = (
            "checkpoint load failed.\n"
            "  Got:      corrupted file\n"
            "  Expected: valid checkpoint\n"
            "  Fix:      re-run adapter.fit()."
        )
        err = CheckpointError(msg)
        assert "Got:" in str(err)
        assert "Expected:" in str(err)
        assert "Fix:" in str(err)


class TestInheritanceNegative:
    def test_checkpoint_corrupt_error_not_adapter_error(self) -> None:
        assert not issubclass(CheckpointCorruptError, AdapterError)

    def test_checkpoint_version_error_not_adapter_error(self) -> None:
        assert not issubclass(CheckpointVersionError, AdapterError)

    def test_checkpoint_corrupt_not_version_error(self) -> None:
        with pytest.raises(CheckpointCorruptError):
            try:
                raise CheckpointCorruptError(
                    "Got: corrupt\n  Expected: valid\n  Fix: re-run fit."
                )
            except CheckpointVersionError:
                pytest.fail("CheckpointCorruptError must NOT be caught as CheckpointVersionError")


class TestCheckpointVersionErrorAttributeTypes:
    def test_checkpoint_version_attribute_is_str(self) -> None:
        err = CheckpointVersionError(
            "Got: 0.1.0\n  Expected: 0.2.0\n  Fix: re-run fit.",
            checkpoint_version="0.1.0",
            current_version="0.2.0",
        )
        assert isinstance(err.checkpoint_version, str)

    def test_current_version_attribute_is_str(self) -> None:
        err = CheckpointVersionError(
            "Got: 0.1.0\n  Expected: 0.2.0\n  Fix: re-run fit.",
            checkpoint_version="0.1.0",
            current_version="0.2.0",
        )
        assert isinstance(err.current_version, str)


class TestPhysLinkErrorCatchableAsException:
    def test_physlink_error_catchable_as_exception(self) -> None:
        with pytest.raises(Exception):
            raise PhysLinkError("Got: x\n  Expected: y\n  Fix: z")

    def test_configuration_error_catchable_as_exception(self) -> None:
        with pytest.raises(Exception):
            raise ConfigurationError("Got: x\n  Expected: y\n  Fix: z")

    def test_checkpoint_version_error_catchable_as_exception(self) -> None:
        with pytest.raises(Exception):
            raise CheckpointVersionError(
                "Got: 0.1.0\n  Expected: 0.2.0\n  Fix: re-run fit.",
                checkpoint_version="0.1.0",
                current_version="0.2.0",
            )


class TestStarImport:
    def test_star_import_exports_all_seven(self) -> None:
        import physlink.core.exceptions as exc_module
        exported = set(exc_module.__all__)
        expected = {
            "PhysLinkError",
            "ConfigurationError",
            "ValidationError",
            "AdapterError",
            "CheckpointError",
            "CheckpointCorruptError",
            "CheckpointVersionError",
        }
        assert expected == exported


class TestPhysLinkInitExport:
    def test_physlink_error_importable_from_physlink(self) -> None:
        from physlink import PhysLinkError as PLE  # noqa: PLC0415
        assert PLE is PhysLinkError

    def test_physlink_error_in_dunder_all(self) -> None:
        import physlink  # noqa: PLC0415
        assert "PhysLinkError" in physlink.__all__
