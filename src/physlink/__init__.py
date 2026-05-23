"""PhysLink — backend-agnostic adapter library for physical simulation ML."""

__version__ = "0.1.3"

from physlink.adapters.dreamer import DreamerV3Adapter  # Story 3.1
from physlink.core._types import TrajectoryBatch, TrajectoryBuffer, TrajectorySchema
from physlink.core.exceptions import PhysLinkError
from physlink.core.spaces import ActionSpace, ObservationSpace  # Story 2.6
from physlink.core.validation import ComplianceReport, register_invariant  # Story 4.3 + 4.4
from physlink.utils.diagnostics import doctor

__all__ = [
    "ActionSpace",
    "ComplianceReport",
    "DreamerV3Adapter",
    "ObservationSpace",
    "PhysLinkError",
    "TrajectoryBatch",
    "TrajectoryBuffer",
    "TrajectorySchema",
    "doctor",
    "register_invariant",
]
