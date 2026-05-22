"""Abstract base adapter interface for PhysLink."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from physlink.core._types import TrajectoryBatch
from physlink.core.spaces import ActionSpace, ObservationSpace


class BaseAdapter(ABC):
    """Abstract base class for all PhysLink adapters.

    Concrete subclasses implement fit(), visualize(), and export() for
    specific ML backends. Construction validates space compatibility only —
    no model loading or backend imports at init time.

    Args:
        obs_space: Validated ObservationSpace from Epic 2.
        act_space: Validated ActionSpace from Epic 2.

    Example:
        >>> # Do not instantiate BaseAdapter directly — use DreamerV3Adapter
        >>> from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
        >>> obs = ObservationSpace.from_proprioception(joints=7)
        >>> act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        >>> adapter = DreamerV3Adapter(obs, act)
    """

    def __init__(self, obs_space: ObservationSpace, act_space: ActionSpace) -> None:
        self.obs_space = obs_space
        self.act_space = act_space

    @abstractmethod
    def fit(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
        steps: int,
        checkpoint_interval_steps: int = 1000,
    ) -> None:
        """Run the adaptation loop. Implemented in Story 3.2."""

    @abstractmethod
    def visualize(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
    ) -> None:
        """Produce triptych GIF. Implemented in Story 3.5."""

    @abstractmethod
    def export(self, path: str) -> None:
        """Export artifact bundle. Implemented in Story 3.6."""

    @abstractmethod
    def explain(self) -> dict[str, Any]:
        """Return metadata dict describing adapter configuration."""
