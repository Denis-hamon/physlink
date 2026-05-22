# Lab Adoption Guide

This guide follows **Petra's DD-002 path**: a lab manager evaluating PhysLink for institutional adoption in under one day.

## Evaluation Checklist

### Hour 1 — Installation & Diagnostics

- [ ] Install PhysLink: `pip install physlink`
- [ ] Run `physlink.doctor()` — confirm Go/No-Go output
- [ ] Verify no dependency conflicts with your existing ML stack

### Hour 2 — Space Configuration

- [ ] Configure an `ObservationSpace` matching your simulation's state representation
- [ ] Configure an `ActionSpace` matching your simulation's action interface
- [ ] Use `.explain()` to verify your configuration is correct
- [ ] Compare with your existing space definitions — spot any mismatches

### Hour 3 — Integration Assessment

- [ ] Check [API Reference](api/index.md) against your simulation's data format
- [ ] Review [Getting Started](getting-started.md) for the 5-step adaptation path
- [ ] Assess the `TrajectoryBatch` schema against your existing data pipelines

### Hour 4 — Compliance Planning (preview)

> **Note:** `register_invariant` and `ComplianceReport` are available after Epic 4.

- [ ] List the physical invariants your domain requires (velocity bounds, energy conservation, etc.)
- [ ] Review the [Domain Scientists Guide](domain-scientists.md) for the compliance API preview
- [ ] Identify which invariants map to PhysLink's upcoming compliance system

## Decision Matrix

| Requirement | PhysLink v0.1 | Target (v0.2) |
|-------------|---------------|---------------|
| Install in Colab | ✅ | ✅ |
| Diagnose env < 15 s | ✅ | ✅ |
| Universal space API | ✅ | ✅ |
| Space introspection | ✅ | ✅ |
| DreamerV3 adapter | 🔄 Epic 3 | ✅ |
| Physical invariants | 🔄 Epic 4 | ✅ |
| Versioned docs | ✅ (mike in v0.2) | ✅ |

## License & Compliance

PhysLink is released under the **MIT License** — no restrictions on academic or commercial use.

## Support

- [GitHub Issues](https://github.com/YOUR-ORG/physlink/issues) — bug reports and feature requests
- [API Reference](api/index.md) — full technical documentation
- [Changelog](changelog.md) — release history and roadmap

## Feedback

We welcome evaluation feedback from lab managers. Please open a GitHub Discussion with your use case and any questions.
