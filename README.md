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
  <a href="docs/domain-scientists.md"><strong>For Domain Scientists →</strong></a>
</p>

---

Backend-agnostic adapter library for physical simulation ML.

**PhysLink is the interface layer between physics simulators and world model adapters.**

Define spaces once. Validate trajectory data before training starts. Enforce physics invariants. Evaluate via the [world-model-eval-lab](https://github.com/Denis-hamon/world-model-eval-lab) benchmark harness — without rewriting the same boilerplate in every project.

> `DreamerV3Adapter` is a Dreamer-inspired RSSM prototype (encoder → GRU → prior/posterior → actor/critic), architecturally inspired by [DreamerV3](https://github.com/danijar/dreamerv3). It is a research prototype, not a wrapper around the original codebase.

## Install

```bash
pip install physlink

# with WMEL evaluation support:
pip install "physlink[eval]"
```

Works on Google Colab out of the box. No CUDA required for diagnostics and space definitions.

## Quick start

```python
import physlink

# 1. Verify your environment (< 15 s)
physlink.doctor()

# 2. Define spaces from your robot config
obs = physlink.ObservationSpace.from_proprioception(joints=7, include_velocity=True)
act = physlink.ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)

# 3. Validate trajectory data before training
schema = physlink.TrajectorySchema(obs_dims=obs.dims, act_dims=act.dims)
batch = physlink.TrajectoryBatch.from_list(episodes)
report = batch.quality_report(schema)
assert report.overall == "PASS"  # fails fast — don't waste GPU on bad data

# 4. Train the world model adapter
adapter = physlink.DreamerV3Adapter(obs, act)
adapter.fit(batch, steps=10_000)

# 5. Enforce physics invariants
physlink.register_invariant(adapter, "energy", fn=energy_fn, tolerance=0.05)
adapter.compliance_report().plot()

# 6. Evaluate via WMEL benchmark harness
from physlink.adapters.wmel_bridge import DreamerWMELAdapter
bridge = DreamerWMELAdapter(adapter, n_candidates=50)
# bridge.plan(obs, goal, horizon=20)  → action sequence via random-shoot MPC

# 7. Visualize & export
adapter.visualize(batch)   # → triptych GIF: Imagination / Real / Difference
adapter.export("./run-01/")
```

## What PhysLink provides

| | API |
|---|---|
| Environment diagnostic | `physlink.doctor()` |
| Observation / action spaces | `ObservationSpace`, `ActionSpace` |
| Trajectory data quality gate | `TrajectorySchema`, `batch.quality_report()` |
| World model training | `DreamerV3Adapter.fit()` |
| Physics invariant checks | `register_invariant()`, `compliance_report()` |
| Imagination vs. reality | `adapter.visualize()` → triptych GIF |
| WMEL evaluation bridge | `DreamerWMELAdapter` in `physlink[eval]` |

## Why PhysLink

| | Without PhysLink | With PhysLink |
|---|---|---|
| Environment check | Debug silent OOM at step 8 000 | `physlink.doctor()` in < 15 s |
| Data validation | Manual checks scattered across notebooks | `TrajectorySchema` + `quality_report()` |
| Space definitions | Write framework-specific mappings per adapter | `ObservationSpace.from_proprioception()` |
| Session disconnect | Lose 3 h of T4 training | Auto-checkpoint, one-call resume |
| Physics check | Manually verify energy conservation | `register_invariant()` + `compliance_report()` |
| Model diagnosis | Stare at loss curves | Triptych GIF — Imagination / Real / Diff |
| Evaluation | Build evaluation infrastructure from scratch | `DreamerWMELAdapter` + WMEL harness |

## Status

`v0.1.3` — public API stable across minor versions. See [CHANGELOG](CHANGELOG.md) and [ROADMAP](ROADMAP.md).

`test-cpu` CI passes on every push. GPU benchmarks run on release tags.

## For technical reviewers

- [PRODUCT_THESIS.md](PRODUCT_THESIS.md) — why this library exists
- [EXPERIMENT_CARD.md](EXPERIMENT_CARD.md) — what the reference experiment claims and doesn't
- [BACKEND_BOUNDARY.md](BACKEND_BOUNDARY.md) — what PhysLink owns vs what the neural backend owns
- [examples/wmel_integration.py](examples/wmel_integration.py) — end-to-end WMEL walkthrough

The reference dataset at `examples/data/reference_trajectory.jsonl` is reproducible: `python3 examples/check_trajectory_quality.py` regenerates it from `seed=42` and re-runs the quality gate.

## Documentation

Full docs at **[Denis-hamon.github.io/physlink](https://Denis-hamon.github.io/physlink/)**.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome.
