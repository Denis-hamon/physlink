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
| ML models violate physical laws | `register_invariant` + `ComplianceReport` |
| Hard to debug space mismatches | `.explain()` introspection on every space |
| Slow environment diagnosis | `doctor()` Go/No-Go in < 15 s on Colab T4 |

## Installation

```bash
pip install physlink
# or with GPU support
pip install "physlink[gpu]"
```

---

## Project Documentation Index

> **For AI-assisted development**: this section provides structured context for LLM sessions. Start here to understand the project before generating code.

### Project Overview

| Field | Value |
|-------|-------|
| **Project** | PhysLink |
| **Version** | 0.1.2 |
| **Type** | Python library (monolith, src layout) |
| **Language** | Python 3.10+ |
| **Architecture** | Layered (core / adapters / utils) |
| **Public API** | 7 symbols: `doctor`, `ObservationSpace`, `ActionSpace`, `DreamerV3Adapter`, `register_invariant`, `ComplianceReport`, `PhysLinkError` |
| **Distribution** | PyPI (`pip install physlink`) |
| **License** | MIT |

### Quick Reference

**Core import**:
```python
from physlink import (
    doctor, ObservationSpace, ActionSpace,
    DreamerV3Adapter, register_invariant, ComplianceReport, PhysLinkError
)
```

**Typical usage (7-DOF arm)**:
```python
obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
adapter = DreamerV3Adapter(obs, act)
run = adapter.fit(trajectories, steps=10000)
report = adapter.compliance_report()
```

### Generated Documentation (AI Context)

- [Architecture](architecture.md) — Full architecture, data flow, component deep-dives, design decisions
- [Source Tree Analysis](source-tree-analysis.md) — Annotated directory tree, entry points, critical folders
- [Development Guide](development-guide.md) — Setup, commands, dev rules, adding adapters
- [Deployment Guide](deployment-guide.md) — Release process, CI/CD pipelines, GPU protocol
- [Contribution Guide](contribution-guide.md) — Code standards, PR process, versioning

### Existing Documentation

- [Getting Started](getting-started.md) — User-facing quickstart and Colab notebook
- [Domain Scientists](domain-scientists.md) — Invariant validation walkthrough for CFD/physics researchers
- [Lab Adoption Guide](lab-adoption-guide.md) — Evaluation criteria, institutional trust signals
- [API Reference](api/index.md) — mkdocstrings-generated API reference
- [Changelog](changelog.md) — Version history (Keep a Changelog format)

### Getting Started (Developer)

```bash
# Clone and install
git clone https://github.com/Denis-hamon/physlink.git
cd physlink
pip install -e ".[dev]"
pre-commit install

# Verify environment
python -c "import physlink; physlink.doctor()"

# Run CPU test suite
pytest -m "not gpu" tests/ -v
```

### Key Invariants for AI Agents

1. `core/` has **zero ML imports** at module level — `import physlink` works without PyTorch
2. All exception messages follow **Got/Expected/Fix** format
3. Space construction validates **eagerly** (fail at `__init__`, not at training time)
4. `fit()` is **idempotent** — safe to call multiple times
5. The public API surface is **exactly** the 7 symbols in `physlink.__all__` (stable for v0.1.x)
6. `bool` check must precede `int` check in validators (`isinstance(x, bool)` before `isinstance(x, int)`)
