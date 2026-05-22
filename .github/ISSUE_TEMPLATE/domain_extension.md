---
name: "Domain Extension"
about: Propose a new physical domain invariant for PhysLink (community contribution path)
title: "[DOMAIN] "
labels: enhancement
assignees: ''
---

## Physical domain

_Describe the physical system you want to model as a PhysLink invariant._

Examples of physical domains: computational fluid dynamics (CFD), rigid-body robotics,
combustion simulation, molecular dynamics, structural mechanics, …

**Domain name**: (e.g. "Navier–Stokes mass conservation")
**Physical system**: (e.g. "Incompressible flow on a 2-D grid")
**Conserved / constrained quantity**: (e.g. "∇·u = 0, divergence-free velocity field")

## Invariant function

_Provide a Python implementation (or prototype) of your invariant function.
The function must follow the `fn(trajectory: dict) -> float` signature
expected by `register_invariant()`._

```python
from physlink import register_invariant

def my_invariant(trajectory: dict) -> float:
    """Return 0.0 when the invariant holds; larger values indicate larger violations."""
    # TODO: implement your domain-specific check
    raise NotImplementedError

# Register with a PhysLink adapter:
# register_invariant(adapter, name="my_domain/my_invariant", fn=my_invariant,
#                    tolerance=1e-3, mode="absolute")
```

_Please document any assumptions about the `trajectory` dict keys your function reads._

## Expected PASS output

_Describe what a `ComplianceReport` should look like when this invariant passes.
Reference the `ComplianceReport` summary format introduced in Story 4.4._

Example:
```
ComplianceReport
  status  : PASS
  checked : 100 trajectories
  violations: 0 / 100
```

## Reference literature

_Optional — but strongly encouraged. List any papers, textbooks, or standards that
define or validate this invariant._

- Author et al. (Year). _Title_. Journal / Conference.
- Equation reference: …
