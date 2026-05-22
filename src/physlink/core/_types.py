"""Canonical trajectory data types for PhysLink core.

Implementation in Story 2.1 (TrajectoryBatch) and Story 4.1 (AdaptationConfig, AdaptationRun).
"""

from __future__ import annotations

import datetime
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from physlink.core.spaces import ActionSpace, ObservationSpace


@dataclass
class TrajectoryBatch:
    """Canonical container for a batch of trajectory dicts.

    Backend-agnostic — no torch primitives in any public signature.
    Used as the stable input type for fit() across all adapters.

    Args:
        data: List of trajectory dicts, each with at minimum "obs" and "action" keys.

    Example:
        >>> tb = TrajectoryBatch.from_list([{"obs": [1, 2], "action": [0]}])
        >>> len(tb)
        1
    """

    data: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_list(cls, data: list[dict[str, Any]]) -> TrajectoryBatch:
        """Convert a list of trajectory dicts to a TrajectoryBatch silently.

        Args:
            data: List of trajectory dicts. Empty list is valid.

        Returns:
            A TrajectoryBatch wrapping the provided data.

        Example:
            >>> tb = TrajectoryBatch.from_list([{"obs": [1, 2], "action": [0]}])
            >>> isinstance(tb, TrajectoryBatch)
            True
        """
        return cls(data=data)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.data)

    def __repr__(self) -> str:
        return f"TrajectoryBatch(n={len(self.data)})"


@dataclass(frozen=True)
class AdaptationConfig:
    """Immutable configuration for a named adaptation experiment.

    Separates configuration from execution state so config can be versioned
    in YAML/JSON and tracked independently of any particular run.

    Args:
        obs_space: Observation space defining environment inputs.
        act_space: Action space defining environment outputs.
        steps: Total gradient steps for the adaptation run.
        checkpoint_interval_steps: Steps between checkpoint saves.
        checkpoint_dir: Directory where checkpoint files are written.

    Raises:
        FrozenInstanceError: On any attempt to mutate fields after construction.

    Example:
        >>> from physlink import ObservationSpace, ActionSpace
        >>> obs = ObservationSpace.from_proprioception(joints=7)
        >>> act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        >>> config = AdaptationConfig(obs_space=obs, act_space=act, steps=10000)
        >>> config.steps
        10000
    """

    obs_space: ObservationSpace
    act_space: ActionSpace
    steps: int
    checkpoint_interval_steps: int = 1000
    checkpoint_dir: str = "physlink_checkpoints"

    def to_dict(self) -> dict[str, object]:
        """Serialize config to a JSON-serializable dict.

        Returns:
            A dict with obs_space, act_space (via explain()), steps,
            checkpoint_interval_steps, and checkpoint_dir.

        Example:
            >>> d = config.to_dict()
            >>> d["steps"]
            10000
        """
        return {
            "obs_space": self.obs_space.explain(),
            "act_space": self.act_space.explain(),
            "steps": self.steps,
            "checkpoint_interval_steps": self.checkpoint_interval_steps,
            "checkpoint_dir": self.checkpoint_dir,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> AdaptationConfig:
        """Reconstruct an AdaptationConfig from a serialized dict.

        Args:
            d: Dict produced by to_dict(), with obs_space and act_space sub-dicts.

        Returns:
            An AdaptationConfig equal to the original.

        Example:
            >>> config2 = AdaptationConfig.from_dict(config.to_dict())
            >>> config2 == config
            True
        """
        obs_d: Any = d["obs_space"]
        act_d: Any = d["act_space"]
        obs = ObservationSpace.from_proprioception(
            joints=obs_d["joints"],
            include_velocity=obs_d["include_velocity"],
            clip_bounds=tuple(obs_d["clip_bounds"]) if obs_d["clip_bounds"] else None,
            normalize=obs_d["normalize"],
        )
        act = ActionSpace.continuous(
            dims=act_d["dims"],
            bounds=[tuple(b) for b in act_d["bounds"]],
        )
        return cls(
            obs_space=obs,
            act_space=act,
            steps=d["steps"],  # type: ignore[arg-type]
            checkpoint_interval_steps=d["checkpoint_interval_steps"],  # type: ignore[arg-type]
            checkpoint_dir=d["checkpoint_dir"],  # type: ignore[arg-type]
        )

    def to_yaml(self, path: str) -> None:
        """Write config to a YAML file at the given path.

        Args:
            path: File path where the YAML config will be written.

        Example:
            >>> config.to_yaml("/tmp/config.yaml")
        """
        import yaml  # type: ignore[import-untyped]

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, path: str) -> AdaptationConfig:
        """Load an AdaptationConfig from a YAML file.

        Args:
            path: File path to read the YAML config from.

        Returns:
            An AdaptationConfig equal to the original that was serialized.

        Raises:
            FileNotFoundError: If path does not exist.

        Example:
            >>> loaded = AdaptationConfig.from_yaml("/tmp/config.yaml")
            >>> loaded == config
            True
        """
        import yaml

        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        return cls.from_dict(d)


@dataclass
class AdaptationRun:
    """Stateful record of a single adaptation run.

    Mutable by design — tracks execution state (step count, checkpoints,
    timing) separately from the immutable AdaptationConfig.

    Args:
        config: Immutable configuration for this run.
        current_step: Number of gradient steps completed.
        checkpoint_paths: Paths to checkpoint files saved during the run.
        started_at: ISO-format UTC timestamp of run creation.
        elapsed_seconds: Wall-clock seconds elapsed during fit().

    Example:
        >>> run = AdaptationRun(config=config)
        >>> run.current_step
        0
    """

    config: AdaptationConfig
    current_step: int = 0
    checkpoint_paths: list[str] = field(default_factory=list)
    started_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    elapsed_seconds: float = 0.0
