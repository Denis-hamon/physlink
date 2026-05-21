"""PhysLink exception hierarchy.

All public exceptions inherit from PhysLinkError. Error messages MUST follow
the Got/Expected/Fix template for human-readable, machine-parseable context.
"""

from __future__ import annotations


class PhysLinkError(Exception):
    """Base exception for all PhysLink errors.

    All PhysLink exceptions inherit from this class. Catch PhysLinkError
    to handle any PhysLink-specific error at the coarsest granularity.

    Example:
        >>> try:
        ...     raise PhysLinkError("Got: x\\n  Expected: y\\n  Fix: do z")
        ... except PhysLinkError as e:
        ...     print(e)
    """


class ConfigurationError(PhysLinkError):
    """Raised when a PhysLink object receives invalid configuration at init time.

    Use for invalid constructor arguments — wrong types, out-of-range values,
    incompatible parameter combinations. NOT for runtime data validation.

    Example:
        >>> raise ConfigurationError(
        ...     "DreamerV3Adapter: incompatible obs_space.\\n"
        ...     "  Got:      obs_dims=3\\n"
        ...     "  Expected: obs_dims >= 4 (DreamerV3 minimum)\\n"
        ...     "  Fix:      construct ObservationSpace with joints >= 4."
        ... )
    """


class ValidationError(PhysLinkError):
    """Raised when runtime data violates a PhysLink invariant.

    Use for trajectory data, space dimension mismatches, or invariant
    violations detected at runtime. NOT for constructor argument errors.

    Example:
        >>> raise ValidationError(
        ...     "ObservationSpace.from_proprioception: invalid joints value.\\n"
        ...     "  Got:      joints=0\\n"
        ...     "  Expected: joints >= 1 (positive integer)\\n"
        ...     "  Fix:      pass joints >= 1, e.g. joints=7 for a 7-DOF arm."
        ... )
    """


class AdapterError(PhysLinkError):
    """Raised for I/O operations explicitly managed by PhysLink adapters.

    Scope: PhysLink-controlled I/O only — file reads, file writes, network
    calls initiated by the library. NOT for OOM errors, OS timeouts, or
    hardware failures that occur outside PhysLink's control.

    Example:
        >>> raise AdapterError(
        ...     "DreamerV3Adapter.export: write failed.\\n"
        ...     "  Got:      PermissionError writing to /read-only/path.safetensors\\n"
        ...     "  Expected: a writable file path\\n"
        ...     "  Fix:      choose a path with write permissions, e.g. './checkpoint.safetensors'."
        ... )
    """


class CheckpointError(PhysLinkError):
    """Base exception for checkpoint-related failures.

    Inherits directly from PhysLinkError — NOT from AdapterError.
    Checkpoint concerns (versioning, corruption) are cross-cutting
    and independent of adapter I/O scope.

    Example:
        >>> try:
        ...     load_checkpoint(path)
        ... except CheckpointError as e:
        ...     print(f"Checkpoint failed: {e}")
    """


class CheckpointCorruptError(CheckpointError):
    """Raised when a safetensors checkpoint file is unreadable or malformed.

    Triggered before attempting to load weights — on metadata parse failure
    or binary format violation.

    Example:
        >>> raise CheckpointCorruptError(
        ...     "checkpoint_step_1000.safetensors: metadata missing or malformed.\\n"
        ...     "  Got:      file exists but metadata block is absent\\n"
        ...     "  Expected: valid safetensors file with physlink_version metadata\\n"
        ...     "  Fix:      re-run adapter.fit() to generate a fresh checkpoint."
        ... )
    """


class CheckpointVersionError(CheckpointError):
    """Raised when checkpoint physlink_version is incompatible with current version.

    Reads metadata BEFORE loading weights for early detection. Carries
    structured attributes for programmatic recovery.

    Args:
        message: Human-readable Got/Expected/Fix error description.
        checkpoint_version: The physlink version string stored in the checkpoint.
        current_version: The physlink version string currently installed.

    Example:
        >>> raise CheckpointVersionError(
        ...     "Checkpoint version mismatch.\\n"
        ...     "  Got:      checkpoint saved with physlink==0.1.0\\n"
        ...     "  Expected: physlink==0.2.0\\n"
        ...     "  Fix:      re-run adapter.fit() to generate a fresh checkpoint.",
        ...     checkpoint_version="0.1.0",
        ...     current_version="0.2.0",
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        checkpoint_version: str,
        current_version: str,
    ) -> None:
        super().__init__(message)
        self.checkpoint_version = checkpoint_version
        self.current_version = current_version


__all__ = [
    "AdapterError",
    "CheckpointCorruptError",
    "CheckpointError",
    "CheckpointVersionError",
    "ConfigurationError",
    "PhysLinkError",
    "ValidationError",
]
