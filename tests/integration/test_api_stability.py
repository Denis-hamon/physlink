"""API stability contract — verifies physlink.__all__ surface.

This test is intentionally minimal at Epic 1 stage. It will be activated
incrementally by each epic's final story (Story 1.5 adds 2 symbols, Story 2.6
adds 4, Story 4.5 finalizes all 7).
"""

from __future__ import annotations

import pytest


def test_epic1_api_symbols() -> None:
    import physlink

    expected = {"doctor", "PhysLinkError"}
    actual = set(physlink.__all__)
    assert expected.issubset(actual), f"Missing Epic 1 symbols: {expected - actual}"


def test_epic2_api_symbols() -> None:
    """Story 2.6: ObservationSpace and ActionSpace added to public API."""
    import physlink
    from physlink import ObservationSpace, ActionSpace  # noqa: F401 — import test

    expected = {"doctor", "ObservationSpace", "ActionSpace", "PhysLinkError"}
    actual = set(physlink.__all__)
    assert expected.issubset(actual), (
        f"Epic 2 API surface regression.\n"
        f"  Missing: {expected - actual}\n"
        f"  Got:     {sorted(actual)}\n"
        f"  Fix:     restore missing symbols to physlink.__all__"
    )


def test_epic3_api_symbols() -> None:
    """Story 3.1: DreamerV3Adapter added to public API."""
    import physlink
    from physlink import DreamerV3Adapter  # noqa: F401 — import test

    expected = {"doctor", "ObservationSpace", "ActionSpace", "PhysLinkError", "DreamerV3Adapter"}
    actual = set(physlink.__all__)
    assert expected.issubset(actual), (
        f"Epic 3 API surface mismatch.\n"
        f"  Missing: {expected - actual}\n"
        f"  Got:     {sorted(actual)}\n"
        f"  Fix:     add missing symbols to physlink.__all__ in src/physlink/__init__.py"
    )


def test_story43_api_symbols() -> None:
    """Story 4.3: register_invariant added to public API."""
    import physlink
    from physlink import register_invariant  # noqa: F401 — import test

    expected = {
        "doctor", "ObservationSpace", "ActionSpace", "PhysLinkError",
        "DreamerV3Adapter", "register_invariant",
    }
    actual = set(physlink.__all__)
    assert expected.issubset(actual), (
        f"Story 4.3 API surface mismatch.\n"
        f"  Missing: {expected - actual}\n"
        f"  Got:     {sorted(actual)}\n"
        f"  Fix:     add missing symbols to physlink.__all__ in src/physlink/__init__.py"
    )


# DEPRECATION PROTOCOL (NFR-11):
# When a public symbol or behaviour is deprecated, add a test here that:
#   1. Calls the deprecated code path
#   2. Asserts warnings.warn(..., DeprecationWarning) fires via pytest.warns(DeprecationWarning)
#   3. References the CHANGELOG entry that documents the removal timeline
# Epic 4 (Story 4.5) will update to assert the full 7-symbol set.


class TestTopLevelNamespaceAccess:
    """Story 2.6 AC #2: ObservationSpace and ActionSpace accessible via physlink namespace."""

    def test_observation_space_accessible_via_physlink(self) -> None:
        import physlink

        assert hasattr(physlink, "ObservationSpace")

    def test_action_space_accessible_via_physlink(self) -> None:
        import physlink

        assert hasattr(physlink, "ActionSpace")

    def test_physlink_error_accessible_via_physlink(self) -> None:
        import physlink

        assert hasattr(physlink, "PhysLinkError")

    def test_observation_space_is_callable(self) -> None:
        import physlink

        assert callable(physlink.ObservationSpace)

    def test_action_space_is_callable(self) -> None:
        import physlink

        assert callable(physlink.ActionSpace)

    def test_observation_space_functional_from_top_level(self) -> None:
        from physlink import ObservationSpace

        obs = ObservationSpace.from_proprioception(joints=7)
        assert obs.dims == 7

    def test_action_space_functional_from_top_level(self) -> None:
        from physlink import ActionSpace

        act = ActionSpace.continuous(dims=3, bounds=[(-1.0, 1.0)] * 3)
        assert act.dims == 3

    def test_observation_space_same_object_as_core_module(self) -> None:
        from physlink import ObservationSpace
        from physlink.core.spaces import ObservationSpace as CoreObservationSpace

        assert ObservationSpace is CoreObservationSpace

    def test_action_space_same_object_as_core_module(self) -> None:
        from physlink import ActionSpace
        from physlink.core.spaces import ActionSpace as CoreActionSpace

        assert ActionSpace is CoreActionSpace

    def test_dreamer_v3_adapter_accessible_via_physlink(self) -> None:
        import physlink

        assert hasattr(physlink, "DreamerV3Adapter")

    def test_dreamer_v3_adapter_is_callable(self) -> None:
        import physlink

        assert callable(physlink.DreamerV3Adapter)

    def test_dreamer_v3_adapter_same_object_as_adapters_module(self) -> None:
        from physlink import DreamerV3Adapter
        from physlink.adapters.dreamer import DreamerV3Adapter as AdaptersDreamer

        assert DreamerV3Adapter is AdaptersDreamer


class TestPackageMetadata:
    """Story 2.6: Package metadata and __all__ ordering contract."""

    def test_version_attribute_exists(self) -> None:
        import physlink

        assert hasattr(physlink, "__version__")

    def test_version_is_string(self) -> None:
        import physlink

        assert isinstance(physlink.__version__, str)

    def test_version_is_semver_format(self) -> None:
        import physlink

        parts = physlink.__version__.split(".")
        assert len(parts) == 3, f"Expected semver X.Y.Z, got: {physlink.__version__!r}"

    def test_all_is_sorted(self) -> None:
        import physlink

        assert physlink.__all__ == sorted(physlink.__all__), (
            f"physlink.__all__ must be isort-sorted.\n"
            f"  Got:      {physlink.__all__}\n"
            f"  Expected: {sorted(physlink.__all__)}"
        )
