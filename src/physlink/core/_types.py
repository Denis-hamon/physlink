"""Canonical trajectory data types for PhysLink core.

Implementation in Story 2.1 (TrajectoryBatch) and Story 4.1 (AdaptationConfig, AdaptationRun).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


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
