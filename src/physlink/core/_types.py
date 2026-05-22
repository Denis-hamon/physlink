"""Canonical trajectory data types for PhysLink core.

Implementation in Story 2.1 (TrajectoryBatch) and Story 4.1 (AdaptationConfig, AdaptationRun).
"""

from __future__ import annotations

import datetime
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, cast

import numpy as np

from physlink.core.exceptions import ValidationError
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

    def quality_report(self, schema: TrajectorySchema) -> TrajectoryQualityReport:
        """Inspect this batch against an explicit trajectory schema.

        ``TrajectoryBatch`` remains a lightweight adapter input. Call this
        method before ``fit()`` when data assumptions should be visible and
        reviewable instead of being inferred inside a training loop.
        """
        return schema.inspect(self)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.data)

    def __repr__(self) -> str:
        return f"TrajectoryBatch(n={len(self.data)})"


@dataclass
class TrajectoryBuffer:
    """Mutable buffer for collecting and persisting trajectory data across sessions.

    Wraps a list of trajectory dicts and provides ``export``/``load`` methods for
    cross-session persistence. Use ``to_batch()`` to convert to a ``TrajectoryBatch``
    for direct use with ``adapter.fit()``.

    Args:
        data: List of trajectory dicts, each with at minimum "obs" and "action" keys.

    Example:
        >>> buf = TrajectoryBuffer(data=[{"obs": [1, 2], "action": [0]}])
        >>> buf.export("/tmp/buf.pkl")
        >>> loaded = TrajectoryBuffer.load("/tmp/buf.pkl")
        >>> len(loaded)
        1
    """

    data: list[dict[str, Any]] = field(default_factory=list)

    def export(self, path: str) -> None:
        """Persist buffer to disk at the given path.

        Serialises ``self.data`` using pickle without modifying the in-memory state.

        Args:
            path: File path where the buffer will be written (.pkl extension recommended).

        Raises:
            OSError: If the file cannot be created or written (e.g. invalid path, no permissions).

        Example:
            >>> buf = TrajectoryBuffer(data=[{"obs": [1, 2], "action": [0]}])
            >>> buf.export("/tmp/trajectories.pkl")
        """
        import pickle

        with open(path, "wb") as f:
            pickle.dump(self.data, f)

    @classmethod
    def load(cls, path: str) -> TrajectoryBuffer:
        """Load a previously exported ``TrajectoryBuffer`` from disk.

        Args:
            path: File path to read the buffer from.

        Returns:
            A ``TrajectoryBuffer`` containing the same trajectories as the original.

        Raises:
            FileNotFoundError: If ``path`` does not exist.

        Example:
            >>> loaded = TrajectoryBuffer.load("/tmp/trajectories.pkl")
            >>> isinstance(loaded, TrajectoryBuffer)
            True
        """
        import pickle

        with open(path, "rb") as f:
            data = pickle.load(f)
        return cls(data=data)

    def to_batch(self) -> TrajectoryBatch:
        """Convert buffer to a ``TrajectoryBatch`` for use with ``adapter.fit()``.

        Returns:
            A ``TrajectoryBatch`` wrapping the buffer's data.

        Example:
            >>> buf = TrajectoryBuffer(data=[{"obs": [1], "action": [0]}])
            >>> batch = buf.to_batch()
            >>> isinstance(batch, TrajectoryBatch)
            True
        """
        return TrajectoryBatch.from_list(self.data)

    def quality_report(self, schema: TrajectorySchema) -> TrajectoryQualityReport:
        """Inspect buffered rollout data against an explicit schema."""
        return schema.inspect(self)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.data)

    def __repr__(self) -> str:
        return f"TrajectoryBuffer(n={len(self.data)})"


@dataclass(frozen=True)
class TrajectoryQualityIssue:
    """One inspectable data-contract finding from a trajectory quality report."""

    severity: Literal["error", "warning"]
    code: str
    message: str
    row_index: int | None = None
    field: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize the issue into a JSON-compatible mapping."""
        payload: dict[str, object] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.row_index is not None:
            payload["row_index"] = self.row_index
        if self.field is not None:
            payload["field"] = self.field
        return payload


@dataclass(frozen=True)
class TrajectoryQualityReport:
    """Quality gate output for trajectory data inspected before adaptation."""

    checked_rows: int
    errors: tuple[TrajectoryQualityIssue, ...] = ()
    warnings: tuple[TrajectoryQualityIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Return ``True`` when no blocking schema errors were found."""
        return not self.errors

    def summary(self) -> str:
        """Return a compact review line for logs and experiment notes."""
        status = "PASS" if self.is_valid else "FAIL"
        return (
            f"{status}: checked {self.checked_rows} trajectory rows, "
            f"{len(self.errors)} errors, {len(self.warnings)} warnings"
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the report into a JSON-compatible mapping."""
        return {
            "checked_rows": self.checked_rows,
            "is_valid": self.is_valid,
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
        }

    def raise_for_errors(self) -> None:
        """Raise ``ValidationError`` when the report contains blocking issues."""
        if self.is_valid:
            return

        first = self.errors[0]
        location = f"row {first.row_index}, " if first.row_index is not None else ""
        raise ValidationError(
            "TrajectoryQualityReport.raise_for_errors: trajectory schema validation failed.\n"
            f"  Got:      {len(self.errors)} error(s) across {self.checked_rows} rows; "
            f"first={location}{first.code}: {first.message}\n"
            "  Expected: trajectory rows matching the configured TrajectorySchema\n"
            "  Fix:      inspect report.errors, repair the data contract, and run the "
            "quality report again."
        )


@dataclass(frozen=True)
class TrajectorySchema:
    """Per-row contract for rollout data inspected before a model sees it.

    The current adapters consume one row per time step with at least ``obs`` and
    ``action`` vector fields. Sequence context and metadata are kept visible as
    report warnings unless callers make sequence fields blocking with
    ``require_sequence_fields=True``.
    """

    obs_dims: int
    action_dims: int
    action_bounds: tuple[tuple[float, float], ...] | None = None
    metadata_keys: tuple[str, ...] = ()
    require_sequence_fields: bool = False

    def __post_init__(self) -> None:
        self._validate_dims("obs_dims", self.obs_dims)
        self._validate_dims("action_dims", self.action_dims)

        if self.action_bounds is not None and len(self.action_bounds) != self.action_dims:
            raise ValidationError(
                "TrajectorySchema: action_bounds length mismatch.\n"
                f"  Got:      {len(self.action_bounds)} action bounds\n"
                f"  Expected: {self.action_dims} action bounds, one per action dimension\n"
                "  Fix:      build the schema with TrajectorySchema.from_spaces() or provide "
                "one (min, max) tuple per action."
            )
        if any(not isinstance(key, str) or not key for key in self.metadata_keys):
            raise ValidationError(
                "TrajectorySchema: invalid metadata_keys.\n"
                f"  Got:      metadata_keys={self.metadata_keys!r}\n"
                "  Expected: non-empty string keys to inspect inside row['metadata']\n"
                "  Fix:      pass keys such as ('source', 'units') or leave metadata_keys empty."
            )

    @classmethod
    def from_spaces(
        cls,
        obs_space: ObservationSpace,
        act_space: ActionSpace,
        *,
        metadata_keys: tuple[str, ...] = (),
        require_sequence_fields: bool = False,
    ) -> TrajectorySchema:
        """Derive shape and action-bound checks from PhysLink spaces."""
        return cls(
            obs_dims=obs_space.dims,
            action_dims=act_space.dims,
            action_bounds=tuple(act_space.bounds),
            metadata_keys=metadata_keys,
            require_sequence_fields=require_sequence_fields,
        )

    def inspect(
        self,
        trajectories: TrajectoryBatch | TrajectoryBuffer | list[dict[str, Any]],
    ) -> TrajectoryQualityReport:
        """Inspect rollout rows without mutating or training on them."""
        if isinstance(trajectories, (TrajectoryBatch, TrajectoryBuffer)):
            rows = trajectories.data
        else:
            rows = trajectories

        errors: list[TrajectoryQualityIssue] = []
        warnings: list[TrajectoryQualityIssue] = []

        if not rows:
            errors.append(
                TrajectoryQualityIssue(
                    severity="error",
                    code="empty_batch",
                    message="no rollout rows were provided",
                )
            )

        for row_index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(
                    TrajectoryQualityIssue(
                        severity="error",
                        code="row_not_mapping",
                        message=f"row has type {type(row).__name__}, not a mapping",
                        row_index=row_index,
                    )
                )
                continue

            obs_vector = self._inspect_vector(
                row=row,
                row_index=row_index,
                field_name="obs",
                expected_dims=self.obs_dims,
                errors=errors,
            )
            action_vector = self._inspect_vector(
                row=row,
                row_index=row_index,
                field_name="action",
                expected_dims=self.action_dims,
                errors=errors,
            )
            if obs_vector is not None:
                self._inspect_finite_values(obs_vector, row_index, "obs", errors)
            if action_vector is not None:
                action_is_finite = self._inspect_finite_values(
                    action_vector, row_index, "action", errors
                )
                if action_is_finite:
                    self._inspect_action_bounds(action_vector, row_index, errors)

            self._inspect_sequence_context(row, row_index, errors, warnings)
            self._inspect_metadata(row, row_index, errors, warnings)

        return TrajectoryQualityReport(
            checked_rows=len(rows),
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _validate_dims(name: str, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValidationError(
                f"TrajectorySchema: invalid {name}.\n"
                f"  Got:      {name}={value!r}\n"
                f"  Expected: {name} must be a positive integer\n"
                f"  Fix:      pass {name} from a PhysLink space or set it explicitly."
            )

    @staticmethod
    def _inspect_vector(
        *,
        row: Mapping[str, Any],
        row_index: int,
        field_name: str,
        expected_dims: int,
        errors: list[TrajectoryQualityIssue],
    ) -> np.ndarray[Any, Any] | None:
        if field_name not in row:
            errors.append(
                TrajectoryQualityIssue(
                    severity="error",
                    code="missing_field",
                    message=f"required field '{field_name}' is absent",
                    row_index=row_index,
                    field=field_name,
                )
            )
            return None

        try:
            vector = np.asarray(row[field_name], dtype=float)
        except (TypeError, ValueError):
            errors.append(
                TrajectoryQualityIssue(
                    severity="error",
                    code="non_numeric_vector",
                    message=f"field '{field_name}' cannot be converted to a numeric vector",
                    row_index=row_index,
                    field=field_name,
                )
            )
            return None

        if vector.ndim != 1:
            errors.append(
                TrajectoryQualityIssue(
                    severity="error",
                    code="vector_rank_mismatch",
                    message=f"field '{field_name}' has rank {vector.ndim}, expected rank 1",
                    row_index=row_index,
                    field=field_name,
                )
            )
            return None

        if vector.shape[0] != expected_dims:
            errors.append(
                TrajectoryQualityIssue(
                    severity="error",
                    code="vector_dim_mismatch",
                    message=(
                        f"field '{field_name}' has {vector.shape[0]} values, "
                        f"expected {expected_dims}"
                    ),
                    row_index=row_index,
                    field=field_name,
                )
            )
            return None
        return cast(np.ndarray[Any, Any], vector)

    @staticmethod
    def _inspect_finite_values(
        vector: np.ndarray[Any, Any],
        row_index: int,
        field_name: str,
        errors: list[TrajectoryQualityIssue],
    ) -> bool:
        if bool(np.all(np.isfinite(vector))):
            return True
        errors.append(
            TrajectoryQualityIssue(
                severity="error",
                code="non_finite_value",
                message=f"field '{field_name}' contains NaN or infinity",
                row_index=row_index,
                field=field_name,
            )
        )
        return False

    def _inspect_action_bounds(
        self,
        action_vector: np.ndarray[Any, Any],
        row_index: int,
        errors: list[TrajectoryQualityIssue],
    ) -> None:
        if self.action_bounds is None:
            return
        for dim_index, (value, bound) in enumerate(zip(action_vector, self.action_bounds)):
            lo, hi = bound
            if value < lo or value > hi:
                errors.append(
                    TrajectoryQualityIssue(
                        severity="error",
                        code="action_out_of_bounds",
                        message=(
                            f"action dimension {dim_index} has value {value}, "
                            f"outside [{lo}, {hi}]"
                        ),
                        row_index=row_index,
                        field="action",
                    )
                )

    def _inspect_sequence_context(
        self,
        row: Mapping[str, Any],
        row_index: int,
        errors: list[TrajectoryQualityIssue],
        warnings: list[TrajectoryQualityIssue],
    ) -> None:
        sequence_issues = errors if self.require_sequence_fields else warnings
        severity: Literal["error", "warning"] = (
            "error" if self.require_sequence_fields else "warning"
        )
        for field_name in ("sequence_id", "step"):
            if field_name not in row:
                sequence_issues.append(
                    TrajectoryQualityIssue(
                        severity=severity,
                        code="missing_sequence_field",
                        message=f"sequence context field '{field_name}' is absent",
                        row_index=row_index,
                        field=field_name,
                    )
                )

        if "step" in row:
            step = row["step"]
            if isinstance(step, bool) or not isinstance(step, int) or step < 0:
                errors.append(
                    TrajectoryQualityIssue(
                        severity="error",
                        code="invalid_step",
                        message="field 'step' must be a non-negative integer",
                        row_index=row_index,
                        field="step",
                    )
                )

    def _inspect_metadata(
        self,
        row: Mapping[str, Any],
        row_index: int,
        errors: list[TrajectoryQualityIssue],
        warnings: list[TrajectoryQualityIssue],
    ) -> None:
        if "metadata" in row and not isinstance(row["metadata"], Mapping):
            errors.append(
                TrajectoryQualityIssue(
                    severity="error",
                    code="metadata_not_mapping",
                    message="field 'metadata' must be a mapping when present",
                    row_index=row_index,
                    field="metadata",
                )
            )
            return

        if not self.metadata_keys:
            return
        if "metadata" not in row:
            warnings.append(
                TrajectoryQualityIssue(
                    severity="warning",
                    code="missing_metadata",
                    message="metadata is absent, so provenance context is incomplete",
                    row_index=row_index,
                    field="metadata",
                )
            )
            return

        metadata = row["metadata"]
        if not isinstance(metadata, Mapping):
            return
        for key in self.metadata_keys:
            if key not in metadata:
                warnings.append(
                    TrajectoryQualityIssue(
                        severity="warning",
                        code="missing_metadata_key",
                        message=f"metadata key '{key}' is absent",
                        row_index=row_index,
                        field="metadata",
                    )
                )


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
