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

    def quality_report(self, schema: TrajectorySchema) -> TrajectoryQualityReport:
        """Validate this batch against a schema and return a quality report.

        Args:
            schema: The TrajectorySchema describing expected obs_dims, act_dims, and action_bounds.

        Returns:
            A TrajectoryQualityReport with per-check results and an overall PASS/WARN/FAIL verdict.

        Example:
            >>> schema = TrajectorySchema(obs_dims=14, act_dims=7)
            >>> report = tb.quality_report(schema)
            >>> report.overall
            'PASS'
        """
        return schema.validate(self)

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

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.data)

    def __repr__(self) -> str:
        return f"TrajectoryBuffer(n={len(self.data)})"


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


# ── Trajectory quality validation ─────────────────────────────────────────────


@dataclass
class CheckResult:
    """Result of a single trajectory schema check.

    Args:
        name: Check identifier (e.g. ``"schema_conformance"``).
        status: ``"PASS"``, ``"WARN"``, or ``"FAIL"``.
        details: Human-readable description of the check outcome.
        count_checked: Number of items examined (0 if not applicable).
        count_failed: Number of items that failed (0 if PASS).
    """

    name: str
    status: str
    details: str
    count_checked: int = 0
    count_failed: int = 0


@dataclass
class TrajectoryQualityReport:
    """Quality report produced by ``TrajectorySchema.validate()``.

    Args:
        checks: Ordered list of individual check results.
        overall: Aggregate verdict — ``"FAIL"`` if any check failed, ``"WARN"`` if any warned,
            ``"PASS"`` otherwise.
        total_steps: Total number of trajectory steps examined.
        episodes: Number of distinct episodes found in the batch.

    Example:
        >>> schema = TrajectorySchema(obs_dims=14, act_dims=7)
        >>> report = schema.validate(batch)
        >>> report.overall
        'PASS'
        >>> d = report.to_dict()
        >>> d["schema_version"]
        '1.0'
    """

    checks: list[CheckResult]
    overall: str
    total_steps: int
    episodes: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (no ``generated_at`` — fully deterministic).

        Returns:
            Dict with ``schema_version``, ``summary``, ``checks``, and ``overall`` keys.

        Example:
            >>> d = report.to_dict()
            >>> d["overall"]
            'PASS'
        """
        return {
            "schema_version": "1.0",
            "summary": {
                "total_steps": self.total_steps,
                "episodes": self.episodes,
            },
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "details": c.details,
                    **({"count_checked": c.count_checked, "count_failed": c.count_failed}
                       if c.count_checked else {}),
                }
                for c in self.checks
            ],
            "overall": self.overall,
        }

    def __str__(self) -> str:
        lines = [f"TrajectoryQualityReport: {self.overall}"]
        for c in self.checks:
            icon = "✓" if c.status == "PASS" else ("⚠" if c.status == "WARN" else "✗")
            lines.append(f"  [{icon}] {c.name}: {c.details}")
        return "\n".join(lines)


@dataclass
class TrajectorySchema:
    """Schema contract for trajectory data — drives the quality gate in ``quality_report()``.

    Args:
        obs_dims: Expected length of the ``"obs"`` vector in every step.
        act_dims: Expected length of the ``"action"`` vector in every step.
        action_bounds: ``(low, high)`` range that every action value must satisfy.
        required_keys: Set of keys that must be present in every trajectory step dict.

    Example:
        >>> schema = TrajectorySchema(obs_dims=14, act_dims=7)
        >>> batch = TrajectoryBatch.from_list(
        ...     [{"obs": [0.0]*14, "action": [0.0]*7, "episode_id": 0, "done": True}]
        ... )
        >>> report = schema.validate(batch)
        >>> report.overall
        'PASS'
    """

    obs_dims: int
    act_dims: int
    action_bounds: tuple[float, float] = (-1.0, 1.0)
    required_keys: frozenset[str] = field(default_factory=lambda: frozenset({"obs", "action"}))

    def validate(self, batch: TrajectoryBatch) -> TrajectoryQualityReport:
        """Run all schema checks against ``batch`` and return a quality report.

        Checks performed (in order):
        1. ``schema_conformance`` — required keys present in every step.
        2. ``obs_dimension_consistency`` — obs vector length equals ``obs_dims``.
        3. ``act_dimension_consistency`` — action vector length equals ``act_dims``.
        4. ``action_range`` — all action values within ``action_bounds``.
        5. ``obs_finite`` — no NaN or Inf in any obs value.
        6. ``episode_termination`` — every episode ends with ``done=True``.

        Args:
            batch: The batch to validate.

        Returns:
            A ``TrajectoryQualityReport`` with per-check results and an overall verdict.

        Example:
            >>> report = schema.validate(batch)
            >>> report.overall in ("PASS", "WARN", "FAIL")
            True
        """
        import math

        data = list(batch)
        checks: list[CheckResult] = []
        lo, hi = self.action_bounds

        # 1 — schema conformance
        bad = [i for i, d in enumerate(data) if not self.required_keys.issubset(d)]
        if bad:
            checks.append(CheckResult(
                "schema_conformance", "FAIL",
                f"{len(bad)} steps missing required keys", len(data), len(bad),
            ))
        else:
            checks.append(CheckResult(
                "schema_conformance", "PASS",
                f"{len(data)}/{len(data)} steps have required keys", len(data),
            ))

        # 2 — obs dimension consistency
        bad = [i for i, d in enumerate(data) if len(d.get("obs", [])) != self.obs_dims]
        if bad:
            checks.append(CheckResult(
                "obs_dimension_consistency", "FAIL",
                f"{len(bad)} steps have wrong obs dim (expected {self.obs_dims})",
                len(data), len(bad),
            ))
        else:
            checks.append(CheckResult(
                "obs_dimension_consistency", "PASS",
                f"All obs vectors are {self.obs_dims}-dimensional", len(data),
            ))

        # 3 — action dimension consistency
        bad = [i for i, d in enumerate(data) if len(d.get("action", [])) != self.act_dims]
        if bad:
            checks.append(CheckResult(
                "act_dimension_consistency", "FAIL",
                f"{len(bad)} steps have wrong action dim (expected {self.act_dims})",
                len(data), len(bad),
            ))
        else:
            checks.append(CheckResult(
                "act_dimension_consistency", "PASS",
                f"All action vectors are {self.act_dims}-dimensional", len(data),
            ))

        # 4 — action range
        total_act, oob = 0, 0
        for d in data:
            for v in d.get("action", []):
                total_act += 1
                if v < lo or v > hi:
                    oob += 1
        if oob:
            checks.append(CheckResult(
                "action_range", "FAIL",
                f"{oob}/{total_act} action values outside [{lo}, {hi}]", total_act, oob,
            ))
        else:
            checks.append(CheckResult(
                "action_range", "PASS",
                f"All {total_act} action values in [{lo}, {hi}]", total_act,
            ))

        # 5 — obs finiteness
        total_obs, non_finite = 0, 0
        for d in data:
            for v in d.get("obs", []):
                total_obs += 1
                if not math.isfinite(v):
                    non_finite += 1
        if non_finite:
            checks.append(CheckResult(
                "obs_finite", "FAIL",
                f"{non_finite}/{total_obs} obs values are NaN or Inf", total_obs, non_finite,
            ))
        else:
            checks.append(CheckResult(
                "obs_finite", "PASS",
                f"No NaN or Inf in {total_obs} obs values", total_obs,
            ))

        # 6 — episode termination
        eps: dict[int, list[dict[str, Any]]] = {}
        for d in data:
            eps.setdefault(d.get("episode_id", 0), []).append(d)
        incomplete = [ep for ep, steps in eps.items() if not steps[-1].get("done", False)]
        if incomplete:
            checks.append(CheckResult(
                "episode_termination", "WARN",
                f"{len(incomplete)} episodes do not end with done=True", len(eps), len(incomplete),
            ))
        else:
            checks.append(CheckResult(
                "episode_termination", "PASS",
                f"{len(eps)}/{len(eps)} episodes terminate with done=True", len(eps),
            ))

        overall = (
            "FAIL" if any(c.status == "FAIL" for c in checks)
            else "WARN" if any(c.status == "WARN" for c in checks)
            else "PASS"
        )
        return TrajectoryQualityReport(
            checks=checks,
            overall=overall,
            total_steps=len(data),
            episodes=len(eps),
        )
