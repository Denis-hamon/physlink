"""Invariant registration and compliance reporting.

Implementation in Story 4.3 (register_invariant) and Story 4.4 (ComplianceReport).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from physlink.core.exceptions import ConfigurationError, ValidationError


@dataclass
class _InvariantRecord:
    name: str
    fn: Callable[[dict[str, Any]], float]
    tolerance: float
    mode: Literal["hard", "soft"]


class _HasInvariants(Protocol):
    """Protocol for adapters that accept registered invariants."""

    _invariants: list[Any]


def _validate_fn_signature(fn: Callable[..., object], name: str) -> None:
    import inspect

    sig = inspect.signature(fn)
    params = [
        p for p in sig.parameters.values()
        if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
    ]
    if len(params) != 1:
        raise ValidationError(
            f"register_invariant: invalid fn signature for '{name}'.\n"
            f"  Got:      {fn.__name__}{sig}\n"
            f"  Expected: fn(trajectory: dict) -> float\n"
            f"  Fix:      define your function with a single dict argument, "
            f"e.g. def {name}(trajectory: dict) -> float: ..."
        )


def register_invariant(
    adapter: _HasInvariants,
    name: str,
    fn: Callable[[dict[str, Any]], float],
    tolerance: float,
    mode: Literal["hard", "soft"] = "soft",
) -> None:
    """Attach a physical invariant check to an adapter via a plain Python callable.

    No subclassing, decorators, or inheritance is required. The function is
    validated immediately at registration time — errors are never deferred to
    ``fit()``.

    Args:
        adapter: The adapter instance to attach the invariant to. Must expose
            a ``_invariants`` list attribute (any duck-type is accepted).
        name: Human-readable identifier for this invariant. Used in diagnostic
            messages and ``ComplianceReport`` output.
        fn: A callable with signature ``fn(trajectory: dict) -> float``. Must
            accept exactly one positional parameter. The return value represents
            the residual — how far the trajectory deviates from the invariant.
        tolerance: Maximum acceptable residual. Violations occur when
            ``fn(trajectory) > tolerance``. Must be >= 0.
        mode: How violations are handled during ``fit()``.
            ``"hard"`` rejects violating trajectories from the training batch.
            ``"soft"`` includes them but adds a penalty to the loss function.
            Defaults to ``"soft"``.

    Raises:
        ValidationError: If ``fn`` does not have exactly one positional parameter.
        ConfigurationError: If ``mode`` is not one of ``["hard", "soft"]``,
            or if ``tolerance`` is negative.

    Example:
        >>> def mass_conservation(trajectory: dict) -> float:
        ...     return abs(trajectory.get("mass_in", 0.0) - trajectory.get("mass_out", 0.0))
        >>> register_invariant(adapter, name="mass_conservation",
        ...                    fn=mass_conservation, tolerance=0.01, mode="hard")
    """
    if mode not in ("hard", "soft"):
        raise ConfigurationError(
            f"register_invariant: invalid mode for '{name}'.\n"
            f"  Got:      mode={mode!r}\n"
            f"  Expected: one of {['hard', 'soft']}\n"
            f"  Fix:      use mode='hard' to reject violations or mode='soft' to penalize them."
        )
    if tolerance < 0:
        raise ConfigurationError(
            f"register_invariant: invalid tolerance for '{name}'.\n"
            f"  Got:      tolerance={tolerance!r}\n"
            f"  Expected: tolerance >= 0\n"
            f"  Fix:      provide a non-negative tolerance value, e.g. tolerance=0.01."
        )
    _validate_fn_signature(fn, name)
    adapter._invariants.append(_InvariantRecord(name=name, fn=fn, tolerance=tolerance, mode=mode))


class ComplianceReport:
    """Pure data object summarizing invariant compliance across adaptation trajectories.

    Constructed by ``DreamerV3Adapter.compliance_report()`` after ``fit()`` is called.
    All methods are deterministic and side-effect-free (NFR-13).

    Args:
        _stats: Per-invariant summary dicts with keys:
            ``name`` (str), ``max_residual`` (float), ``threshold`` (float),
            ``violation_count`` (int), ``total`` (int).
        _violation_list: Per-violation dicts with keys:
            ``invariant_name`` (str), ``trajectory_idx`` (int),
            ``residual`` (float), ``possible_cause`` (str).

    Example:
        >>> report = adapter.compliance_report()
        >>> print(report.summary())
        mass_conservation: PASS (max_residual=0.0042, threshold=0.0100, violations=0/50)
        >>> violations = report.violations()
        >>> violations  # empty list when no violations
        []
    """

    def __init__(
        self,
        _stats: list[dict[str, Any]],
        _violation_list: list[dict[str, Any]],
    ) -> None:
        self._stats: list[dict[str, Any]] = list(_stats)
        self._violation_list: list[dict[str, Any]] = list(_violation_list)

    def summary(self) -> str:
        """Return a human-readable compliance summary string.

        One line per invariant in format:
        ``"name: PASS (max_residual=X.XXXX, threshold=Y.YYYY, violations=Z/N)"``

        Returns:
            Formatted summary string. Empty string if no invariants registered.
            Multiple invariants produce one line each, joined with newline.

        Example:
            >>> report = ComplianceReport(
            ...     _stats=[{"name": "mass", "max_residual": 0.0, "threshold": 0.01,
            ...               "violation_count": 0, "total": 5}],
            ...     _violation_list=[],
            ... )
            >>> report.summary()
            'mass: PASS (max_residual=0.0000, threshold=0.0100, violations=0/5)'
        """
        lines = []
        for s in self._stats:
            status = "PASS" if s["violation_count"] == 0 else "FAIL"
            lines.append(
                f"{s['name']}: {status} ("
                f"max_residual={s['max_residual']:.4f}, "
                f"threshold={s['threshold']:.4f}, "
                f"violations={s['violation_count']}/{s['total']})"
            )
        return "\n".join(lines)

    def violations(self) -> list[dict[str, Any]]:
        """Return a list of all invariant violations detected during fit().

        Returns:
            List of violation dicts, each containing:
            - ``invariant_name`` (str): Name of the violated invariant.
            - ``trajectory_idx`` (int): 0-based index of the violating trajectory.
            - ``residual`` (float): The residual value that exceeded tolerance.
            - ``possible_cause`` (str): Human-readable diagnostic message.
            Sorted by ``(invariant_name, trajectory_idx)`` for determinism.
            Empty list when no violations occurred.

        Example:
            >>> report = ComplianceReport(_stats=[], _violation_list=[])
            >>> report.violations()
            []
        """
        return sorted(
            list(self._violation_list),
            key=lambda v: (v["invariant_name"], v["trajectory_idx"]),
        )
