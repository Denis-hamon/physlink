"""DreamerV3 adapter for PhysLink."""

from typing import Any

from physlink.core._types import TrajectoryBatch
from physlink.core.adapter import BaseAdapter
from physlink.core.exceptions import ConfigurationError
from physlink.core.spaces import ActionSpace, ObservationSpace

MIN_OBS_DIMS: int = 4   # DreamerV3 requires >= 4 observation dimensions
MIN_ACT_DIMS: int = 1   # at least 1 action dimension required


class DreamerV3Adapter(BaseAdapter):
    """DreamerV3 adapter for physical simulation reinforcement learning.

    Validates space compatibility at construction time. Training, visualization,
    and export are deferred to fit() / visualize() / export() respectively.
    No model weights are loaded and no GPU is required at construction.

    Args:
        obs_space: Observation space with dims >= 4.
        act_space: Action space with dims >= 1.

    Raises:
        ConfigurationError: If obs_space.dims < 4 or act_space.dims < 1.

    Example:
        >>> from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
        >>> obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        >>> act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        >>> adapter = DreamerV3Adapter(obs, act)
        >>> adapter.obs_space.dims
        14
    """

    def __init__(self, obs_space: ObservationSpace, act_space: ActionSpace) -> None:
        if obs_space.dims < MIN_OBS_DIMS:
            raise ConfigurationError(
                f"DreamerV3Adapter: incompatible obs_space.\n"
                f"  Got:      obs_space.dims={obs_space.dims}\n"
                f"  Expected: obs_space.dims >= {MIN_OBS_DIMS} (DreamerV3 minimum)\n"
                f"  Fix:      construct ObservationSpace with joints >= {MIN_OBS_DIMS}, "
                f"or use include_velocity=True to double the dimension count."
            )
        if act_space.dims < MIN_ACT_DIMS:
            raise ConfigurationError(
                f"DreamerV3Adapter: incompatible act_space.\n"
                f"  Got:      act_space.dims={act_space.dims}\n"
                f"  Expected: act_space.dims >= {MIN_ACT_DIMS}\n"
                f"  Fix:      construct ActionSpace with dims >= 1."
            )
        super().__init__(obs_space, act_space)

    def explain(self) -> dict[str, Any]:
        """Return a metadata dict describing this adapter's space configuration.

        Returns:
            A JSON-serializable dict with keys: type, obs_space, act_space.

        Example:
            >>> adapter = DreamerV3Adapter(obs, act)
            >>> info = adapter.explain()
            >>> info["type"]
            'DreamerV3Adapter'
        """
        return {
            "type": "DreamerV3Adapter",
            "obs_space": self.obs_space.explain(),
            "act_space": self.act_space.explain(),
        }

    def fit(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
        steps: int,
        checkpoint_interval_steps: int = 1000,
    ) -> None:
        """Run the DreamerV3 adaptation loop. Implemented in Story 3.2.

        Args:
            trajectories: Trajectory dataset (list of dicts or TrajectoryBatch).
            steps: Total adaptation steps to run.
            checkpoint_interval_steps: Steps between checkpoint saves.

        Raises:
            NotImplementedError: Always — implemented in Story 3.2.
        """
        raise NotImplementedError("fit() is implemented in Story 3.2.")

    def visualize(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
    ) -> None:
        """Produce triptych GIF. Implemented in Story 3.5.

        Args:
            trajectories: Trajectory dataset to visualize.

        Raises:
            NotImplementedError: Always — implemented in Story 3.5.
        """
        raise NotImplementedError("visualize() is implemented in Story 3.5.")

    def export(self, path: str) -> None:
        """Export artifact bundle. Implemented in Story 3.6.

        Args:
            path: Directory path for the exported artifacts.

        Raises:
            NotImplementedError: Always — implemented in Story 3.6.
        """
        raise NotImplementedError("export() is implemented in Story 3.6.")

    def __repr__(self) -> str:
        return (
            f"DreamerV3Adapter("
            f"obs_dims={self.obs_space.dims}, "
            f"act_dims={self.act_space.dims})"
        )
