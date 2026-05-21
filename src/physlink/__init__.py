"""PhysLink — backend-agnostic adapter library for physical simulation ML."""

__version__ = "0.1.0"

from physlink.core.exceptions import PhysLinkError
from physlink.utils.diagnostics import doctor

__all__ = [
    "PhysLinkError",
    "doctor",
    # Story 2.2/2.3: ObservationSpace, ActionSpace
    # Story 3.1: DreamerV3Adapter
    # Story 4.3/4.4: register_invariant, ComplianceReport
]
