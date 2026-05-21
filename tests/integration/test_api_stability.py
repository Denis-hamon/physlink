"""API stability contract — verifies physlink.__all__ surface.

This test is intentionally minimal at Epic 1 stage. It will be activated
incrementally by each epic's final story (Story 1.5 adds 2 symbols, Story 2.6
adds 4, Story 4.5 finalizes all 7).
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Activated by Story 1.5 once doctor and PhysLinkError are implemented")
def test_epic1_api_symbols() -> None:
    import physlink

    expected = {"doctor", "PhysLinkError"}
    actual = set(physlink.__all__)
    assert expected.issubset(actual), f"Missing Epic 1 symbols: {expected - actual}"
