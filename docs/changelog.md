# Changelog

All notable changes to PhysLink are documented here.

This file mirrors `CHANGELOG.md` at the project root (coming in Epic 5 — Story 5.1).

---

## v0.1.0 — 2026-05-22

### Added

**Epic 1 — Installable Package & Zero-Friction Diagnostics**

- `physlink.doctor()` — environment diagnostic scan with Go/No-Go in < 15 s on Colab T4
- `PhysLinkError` — base exception hierarchy for structured error handling
- GitHub Actions CI pipeline (CPU + GPU jobs)
- PyPI publication via OIDC (trusted publisher)
- README badges and dual-path action bar

**Epic 2 — Universal Space API (partial)**

- `TrajectoryBatch` — core type for batched trajectory data
- `ObservationSpace` — proprioception-based observation space with `.explain()`
- `ActionSpace` — continuous action space with bounds and `.explain()`
- MkDocs documentation site with GitHub Pages deployment

### Notes

This is the initial public release. The DreamerV3 adapter (Epic 3) and physical compliance validation (Epic 4) are under active development.
