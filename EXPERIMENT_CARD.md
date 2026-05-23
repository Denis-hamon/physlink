# Experiment Card — PhysLink v0.1 Reference Run

This document frames what the reference trajectory experiment claims, what it demonstrates, and — explicitly — what it does not prove. The goal is scientific honesty over marketing.

---

## Hypothesis

A thin adapter layer with explicit interfaces for observation spaces, action spaces, physical invariants, and checkpoints reduces the implementation cost of connecting a physics simulator to a world model from ~200 lines of manual boilerplate to ~10 lines of API calls — without sacrificing reproducibility, correctness checks, or debugging visibility.

This is a **software engineering hypothesis**, not an ML performance hypothesis. The claim is about interface design, not about learning algorithm quality.

---

## Dataset

| Property | Value |
|----------|-------|
| Source | Synthetic — 7-DOF robot arm PD controller (seed=42) |
| Episodes | 10 |
| Steps per episode | 50 |
| Total steps | 500 |
| Observation dims | 14 (7 joint positions + 7 joint velocities) |
| Action dims | 7 (normalised joint torques ∈ [-1, 1]) |
| Reward | Gaussian proximity to target joint angles |
| Generator | `examples/check_trajectory_quality.py` |
| Quality report | `examples/trajectory_quality_report.json` |

The dataset is entirely synthetic. It is not recorded from a real robot or a validated physics engine. Its purpose is to provide a typed, reproducible input that exercises the PhysLink interface, not to represent a research benchmark.

---

## Schema checks

Run `python3 examples/check_trajectory_quality.py` to reproduce.

| Check | Status |
|-------|--------|
| Schema conformance (required keys: obs, action) | PASS |
| Observation dimension consistency (14-dim) | PASS |
| Action dimension consistency (7-dim) | PASS |
| Action range (all values ∈ [-1.0, 1.0]) | PASS |
| Observation finiteness (no NaN/Inf) | PASS |
| Episode termination (done=True on last step) | PASS |

---

## Model

`DreamerV3Adapter` — a Dreamer-inspired RSSM prototype implemented in PyTorch.

See [BACKEND_BOUNDARY.md](BACKEND_BOUNDARY.md) for a precise description of what the adapter contains and what it does not.

The adapter is initialised with:

```python
obs = physlink.ObservationSpace.from_proprioception(joints=7, include_velocity=True)
act = physlink.ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
adapter = physlink.DreamerV3Adapter(obs, act)
```

---

## Metrics (interface-level)

These are the metrics this experiment validates:

| Metric | What it measures |
|--------|-----------------|
| Space mismatch errors at init | Zero — ObservationSpace/ActionSpace catch bad dims before training starts |
| Lines of boilerplate required | ~10 API calls vs ~200 manual lines (see README comparison table) |
| Checkpoint round-trip | Weights saved as `.safetensors`, restored deterministically |
| Compliance gate | `register_invariant` + `ComplianceReport.summary()` surface violations |
| Reproducibility | Fixed seed → identical JSONL → identical quality report |

No learning performance metrics (return, prediction error, benchmark score) are reported. The model has not been trained to convergence on a real task.

---

## Known limitations

1. **Synthetic data** — the reference trajectories do not come from a real physics engine (MuJoCo, PyBullet, Isaac Gym, …). Real robot data would have contact dynamics, sensor noise profiles, and temporal correlations that differ from the PD-controller simulation used here.

2. **No performance baseline** — the DreamerV3Adapter has not been compared against a persistence baseline, a linear dynamics model, or the original DreamerV3 on any benchmark. The learning algorithm quality is unvalidated.

3. **Scale** — 500 steps / 10 episodes is far below what a world model requires for meaningful representation learning. A production run would use thousands of episodes.

4. **No GPU benchmark** — `doctor()` checks for GPU availability; the adapter runs on CPU for this reference experiment. GPU-scale training is out of scope for v0.1.

5. **Single backend** — only `DreamerV3Adapter` exists today. The `BaseAdapter` interface is designed to be swappable, but no second backend has been implemented to validate the interface's flexibility.

---

## What this does NOT prove

- That `DreamerV3Adapter` learns a good world model
- That PhysLink achieves better sample efficiency than alternative approaches
- That the RSSM implementation matches DreamerV3's performance on any benchmark
- That the compliance framework catches real physics violations in production data
- That this is ready for lab deployment without further validation

---

## Reproducibility

```bash
# Install
pip install physlink

# Regenerate data + quality report (deterministic, seed=42)
python3 examples/check_trajectory_quality.py

# Run the quickstart notebook
# notebooks/quickstart.ipynb
```

All outputs are deterministic given seed=42. The quality report committed at `examples/trajectory_quality_report.json` should match exactly.
