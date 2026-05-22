# API Reference

PhysLink v0.1 — tous les symboles publics sont importables directement depuis `physlink`.

```python
from physlink import (
    DreamerV3Adapter,
    ObservationSpace,
    ActionSpace,
    ComplianceReport,
    register_invariant,
    doctor,
    PhysLinkError,
)
```

---

## Adapter

The main adapter class. Wraps your simulator environment and drives the DreamerV3 training loop.

::: physlink.adapters.dreamer.DreamerV3Adapter

---

## Spaces

Space descriptors passed to `DreamerV3Adapter`. They validate dimensions and dtypes at construction time — no silent mismatches at runtime.

::: physlink.core.spaces.ObservationSpace

::: physlink.core.spaces.ActionSpace

---

## Compliance

Register physical invariants (energy conservation, mass conservation, joint limits, …) and inspect violations after training.

::: physlink.core.validation.register_invariant

::: physlink.core.validation.ComplianceReport

---

## Diagnostics

::: physlink.utils.diagnostics.doctor

---

## Exceptions

::: physlink.core.exceptions.PhysLinkError
