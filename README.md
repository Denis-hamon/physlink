# PhysLink

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Denis-hamon/physlink/actions/workflows/ci.yml/badge.svg)](https://github.com/Denis-hamon/physlink/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://Denis-hamon.github.io/physlink/)
[![PyPI](https://img.shields.io/pypi/v/physlink.svg)](https://pypi.org/project/physlink/)
[![Python](https://img.shields.io/pypi/pyversions/physlink.svg)](https://pypi.org/project/physlink/)
[![arXiv](https://img.shields.io/badge/arXiv-coming%20soon-b31b1b.svg)](https://arxiv.org/abs/PLACEHOLDER)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Denis-hamon/physlink/blob/main/notebooks/quickstart.ipynb)

<p align="center">
  <a href="https://colab.research.google.com/github/Denis-hamon/physlink/blob/main/notebooks/quickstart.ipynb"><strong>Quick Start →</strong></a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="docs/lab-adoption-guide.md"><strong>Evaluate for your lab →</strong></a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="https://Denis-hamon.github.io/physlink/domain-scientists/"><strong>For Domain Scientists →</strong></a>
</p>

---

**PhysLink bridges physical simulators and deep RL adapters in one `pip install`.**

Backend-agnostic adapter library for physical simulation ML.

Plug your robot trajectories into a Dreamer-inspired world model adapter without writing boilerplate space definitions, checkpoint logic, or compliance checks. PhysLink handles the plumbing — you keep the science.

> **Note:** `DreamerV3Adapter` implements a Dreamer-like RSSM architecture (encoder -> GRU -> prior/posterior -> actor/critic) and is architecturally inspired by [DreamerV3](https://github.com/danijar/dreamerv3). It is a prototype, not a wrapper around the original DreamerV3 codebase.

Read the [product thesis behind PhysLink](PRODUCT_THESIS.md): why world-model tooling needs explicit interfaces for data, actions, domain constraints, evaluation, and trust. The [roadmap](ROADMAP.md) defines the next three evidence-building workstreams.

## Why PhysLink

| Without PhysLink | With PhysLink |
|-----------------|---------------|
| Hand-write observation/action space mappings per framework | `ObservationSpace.from_proprioception(joints=7)` |
| Debug silent OOM on Colab at step 8 000 | `physlink.doctor()` catches it before you start |
| Lose 3h of T4 training on session disconnect | Auto-checkpoint every N steps, resume on reconnect |
| Manually verify energy conservation after adaptation | `register_invariant` + `compliance_report()` |
| Stare at loss curves to diagnose model drift | Triptych GIF — Imagination / Real / Difference in one call |

## Install

```bash
pip install physlink
```

Works on Google Colab out of the box. No CUDA required for diagnostics and space definitions.

## Quick example

```python
import physlink

# 1. Verify your environment (< 15 s)
physlink.doctor()

# 2. Define spaces from your robot config
obs = physlink.ObservationSpace.from_proprioception(joints=7, include_velocity=True)
act = physlink.ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)

# 3. Adapt
adapter = physlink.DreamerV3Adapter(obs, act)
adapter.fit(trajectories, steps=10_000)

# 4. Validate physics compliance
physlink.register_invariant(adapter, "energy", fn=energy_fn, tolerance=0.05)
report = adapter.compliance_report()
report.plot()

# 5. Visualise
adapter.visualize(trajectories)   # → triptych GIF
adapter.export("./run-01/")
```

## Documentation

Full docs at **[Denis-hamon.github.io/physlink](https://Denis-hamon.github.io/physlink/)** — includes API reference, lab adoption guide, and domain-scientist quickstart.

## Status

`v0.1.x` — public API stable across minor versions (see [CHANGELOG](CHANGELOG.md)).  
`test-cpu` CI passes on every PR. GPU benchmarks run on release tags.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome — use the provided templates.
