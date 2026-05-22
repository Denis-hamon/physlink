# PhysLink

**Backend-agnostic adapter library for physical simulation ML.**

PhysLink lets you connect any physical simulation backend to any ML framework in under 15 lines of code. It handles space configuration, trajectory batching, and compliance validation so you can focus on your research.

## Quick Navigation

- [Getting Started](getting-started.md) — Install and run your first adaptation loop in minutes
- [Domain Scientists](domain-scientists.md) — Physical hallucinations and invariant validation
- [API Reference](api/index.md) — Full API documentation
- [Lab Adoption Guide](lab-adoption-guide.md) — Evaluate PhysLink for your lab
- [Changelog](changelog.md) — Release history

## Why PhysLink?

| Problem | PhysLink Solution |
|---------|-------------------|
| Different sims have incompatible interfaces | Universal `ObservationSpace` / `ActionSpace` API |
| ML models violate physical laws | `register_invariant` + `ComplianceReport` (Epic 4) |
| Hard to debug space mismatches | `.explain()` introspection on every space |
| Slow environment diagnosis | `doctor()` Go/No-Go in < 15 s on Colab T4 |

## Installation

```bash
pip install physlink
# or with GPU support
pip install "physlink[gpu]"
```

## Status

PhysLink v0.1.0 is in active development. See the [Changelog](changelog.md) for current capabilities.
