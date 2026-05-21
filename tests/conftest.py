"""Pytest fixtures for physlink test suite.

Global fixtures will be added here as epics are implemented.
"""

import numpy as np
import pytest


@pytest.fixture
def synthetic_trajectories() -> list[dict]:
    """1000 numpy-only trajectories — no GPU required."""
    rng = np.random.default_rng(42)
    return [{"obs": rng.random(7), "action": rng.random(3)} for _ in range(1000)]
