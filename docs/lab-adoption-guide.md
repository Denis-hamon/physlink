# Lab Adoption Guide

## Introduction

This guide follows **Petra's DD-002 path**: a lab manager evaluating PhysLink for institutional
adoption. By the end of this guide you will have run a named adaptation, persisted trajectories
across sessions, and have everything you need to cite the work in your papers.

---

## Prerequisites

Install PhysLink (version 0.1.2 or later):

```bash
pip install "physlink>=0.1.2"
```

Verify the environment:

```python
import physlink
physlink.doctor()  # Should print "Go" — takes < 15 s on a Colab T4
```

---

## Named Adaptation Run

Use `AdaptationConfig` to define a reproducible, named configuration, and inspect the
`AdaptationRun` returned by `adapter.fit()`.

```python
from physlink import ObservationSpace, ActionSpace, DreamerV3Adapter
from physlink.core._types import AdaptationConfig, AdaptationRun

# 1. Configure spaces for a 7-DOF arm
obs_space = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
act_space = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)

# 2. Define a named, reproducible configuration
config = AdaptationConfig(
    obs_space=obs_space,
    act_space=act_space,
    steps=10_000,
    checkpoint_interval_steps=1000,
    checkpoint_dir="./lab_checkpoints",
)

# Optionally persist the config for reproducibility
config.to_yaml("./lab_config.yaml")

# 3. Run adaptation — fit() returns a tracked AdaptationRun
trajectories = []  # replace with your actual rollout data: list[dict] with "obs" and "action" keys
adapter = DreamerV3Adapter(config.obs_space, config.act_space)
run: AdaptationRun = adapter.fit(
    trajectories,
    steps=config.steps,
    checkpoint_interval_steps=config.checkpoint_interval_steps,
)

# 4. Inspect run metadata
print(f"Completed {run.current_step} steps in {run.elapsed_seconds:.1f}s")
print(f"Checkpoints: {run.checkpoint_paths}")
```

> **Note:** `AdaptationConfig` is a frozen dataclass (immutable). `AdaptationRun` is mutable and
> returned by `adapter.fit()` — it records progress, checkpoints, and timing.

---

## Trajectory Persistence

`TrajectoryBuffer` lets you save rollout data to disk and reload it in a new runtime (e.g., after a
Colab session timeout).

```python
from physlink.core._types import TrajectoryBuffer

# --- Session 1: collect and persist ---
trajectories = []  # replace with your actual rollout data: list[dict] with "obs" and "action" keys
buffer = TrajectoryBuffer(data=trajectories)
buffer.export(path="./lab_trajectories.pkl")

# --- Session 2 (new Colab runtime): reload and continue ---
buffer = TrajectoryBuffer.load(path="./lab_trajectories.pkl")
# Pass the buffer directly to fit() — it is accepted as-is
run = adapter.fit(buffer, steps=5_000)
```

`len(buffer)` returns the number of trajectories. `buffer.to_batch()` converts to a
`TrajectoryBatch` if you need direct batch access.

---

## Trajectory Quality Gate

Before adaptation, make the row contract explicit and keep a report with the experiment record.
`TrajectorySchema` derives vector dimensions and action bounds from the spaces you already chose.
Sequence context remains visible even when a quick prototype does not make it blocking yet.

```python
from physlink.core._types import TrajectoryBatch, TrajectorySchema

trajectories = [
    {
        "obs": [0.1] * 14,
        "action": [0.0] * 7,
        "sequence_id": "episode-001",
        "step": 0,
        "metadata": {"source": "sim-export", "units": "SI"},
    }
]

schema = TrajectorySchema.from_spaces(
    obs_space,
    act_space,
    metadata_keys=("source", "units"),
)
batch = TrajectoryBatch.from_list(trajectories)
report = batch.quality_report(schema)

print(report.summary())  # PASS/FAIL plus error and warning counts
report.raise_for_errors()  # stop before fit() on shape, bounds, or missing-value errors
run = adapter.fit(batch, steps=5_000)
```

The report separates blocking errors from warnings. Missing `sequence_id`, `step`, or requested
metadata keys stay inspectable in a prototype report; set `require_sequence_fields=True` when
sequence context must block a run.

---

## Performance Claims

Petra cannot run the T4 GPU tests herself. Two resources verify the published numbers without
GPU access:

1. **Committed baseline JSON** (always present in the repository):
   `tests/perf/baselines/benchmark_baseline.json`
   — annotated with `"hardware": "T4 GPU"` and the NFR thresholds
   (`doctor()` < 15 s, `compliance_report()` < 30 s).

2. **GitHub Actions CI badge** (live status):

   [![GPU Benchmarks](https://github.com/Denis-hamon/physlink/actions/workflows/test-gpu.yml/badge.svg)](https://github.com/Denis-hamon/physlink/actions/workflows/test-gpu.yml)

   Click the badge to see the latest release-validation run on T4 hardware.

---

## Citing PhysLink

If you use PhysLink in your research, please cite it using the following BibTeX entry:

```bibtex
@software{physlink2026,
  title   = {{PhysLink}: Backend-Agnostic Adapter Library for Physical Simulation {ML}},
  author  = {Hamon, Denis},
  year    = {2026},
  url     = {https://github.com/Denis-hamon/physlink},
  version = {0.1.2}
}
```

---

## License & Support

PhysLink is released under the **MIT License** — no restrictions on academic or commercial use.

- [GitHub Issues](https://github.com/Denis-hamon/physlink/issues) — bug reports and feature requests
- [API Reference](api/index.md) — full technical documentation
- [Changelog](changelog.md) — release history
