"""PhysLink — backend-agnostic adapter library for physical simulation ML."""

__version__ = "0.1.0"

from physlink.adapters.dreamer import DreamerV3Adapter  # Story 3.1
from physlink.core.exceptions import PhysLinkError
from physlink.core.spaces import ActionSpace, ObservationSpace  # Story 2.6
from physlink.utils.diagnostics import doctor

__all__ = [
    "ActionSpace",
    "DreamerV3Adapter",     # Story 3.1
    "ObservationSpace",
    "PhysLinkError",
    "doctor",
    # Story 4.3/4.4: register_invariant, ComplianceReport
]
