"""Observation and action space definitions.

Story 2.2 implemented (ObservationSpace). ActionSpace in Story 2.3.
"""

from __future__ import annotations

from physlink.core.exceptions import ValidationError


class ObservationSpace:
    """Proprioceptive observation space with immediate dimension validation.

    Constructed exclusively via the factory classmethod. Validates inputs
    at creation time so configuration errors surface before any training.

    Args:
        dims: Total observation dimension count (joints or joints*2 with velocity).
        include_velocity: Whether joint velocities are included in observations.
        _joints: Raw joint count passed to from_proprioception.
        clip_bounds: Optional (min, max) clipping range applied to observations.
        normalize: Whether observations are normalized to [0, 1] before passing to the model.

    Example:
        >>> obs_space = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        >>> obs_space.dims
        14
    """

    def __init__(
        self,
        dims: int,
        include_velocity: bool,
        _joints: int,
        clip_bounds: tuple[float, float] | None,
        normalize: bool,
    ) -> None:
        self.dims = dims
        self.include_velocity = include_velocity
        self._joints = _joints
        self.clip_bounds = clip_bounds
        self.normalize = normalize

    @classmethod
    def from_proprioception(
        cls,
        joints: int,
        include_velocity: bool = False,
        clip_bounds: tuple[float, float] | None = None,
        normalize: bool = False,
    ) -> ObservationSpace:
        """Construct an ObservationSpace for proprioceptive (joint-based) observations.

        Args:
            joints: Number of robot joints. Must be a positive integer >= 1.
            include_velocity: If True, each joint contributes position + velocity
                to the observation, doubling the dimension count.
            clip_bounds: Optional (min, max) clipping range for raw observations.
                None means no clipping applied.
            normalize: If True, observations will be normalized before passing
                to the model. Default False.

        Returns:
            An ObservationSpace with dims = joints (or joints * 2 if include_velocity).

        Raises:
            ValidationError: If joints is not a positive integer (wrong type or value <= 0).

        Example:
            >>> obs_space = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
            >>> obs_space.dims
            14
        """
        # bool check MUST come before int check — bool is a subclass of int in Python
        if isinstance(joints, bool) or not isinstance(joints, int):
            raise ValidationError(
                f"ObservationSpace.from_proprioception: invalid joints type.\n"
                f"  Got:      joints={joints!r} (type: {type(joints).__name__})\n"
                f"  Expected: joints must be a positive integer (int)\n"
                f"  Fix:      pass an integer, e.g. joints=7 for a 7-DOF arm."
            )
        if joints < 1:
            raise ValidationError(
                f"ObservationSpace.from_proprioception: invalid joints value.\n"
                f"  Got:      joints={joints}\n"
                f"  Expected: joints >= 1 (positive integer)\n"
                f"  Fix:      pass joints >= 1, e.g. joints=7 for a 7-DOF arm."
            )
        dims = joints * 2 if include_velocity else joints
        return cls(
            dims=dims,
            include_velocity=include_velocity,
            _joints=joints,
            clip_bounds=clip_bounds,
            normalize=normalize,
        )

    def __repr__(self) -> str:
        return f"ObservationSpace(dims={self.dims}, velocity={self.include_velocity})"
