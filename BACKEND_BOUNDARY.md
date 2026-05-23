# Backend Boundary

This document defines exactly what PhysLink owns, what the backend owns, and what the current prototype status is. It exists to prevent the most common misreading of this repo: "PhysLink = a wrapper around DreamerV3."

---

## What PhysLink owns

These are stable, tested, and versioned under PhysLink's public API:

| Component | Symbol | Responsibility |
|-----------|--------|----------------|
| Space definitions | `ObservationSpace`, `ActionSpace` | Validate obs/act dimensions and dtypes at construction time |
| Data containers | `TrajectoryBatch`, `TrajectoryBuffer` | Backend-agnostic trajectory format; no torch in the public interface |
| Invariant registration | `register_invariant` | Attach physics constraints to any adapter |
| Compliance reporting | `ComplianceReport` | Aggregate violations, residuals, and soft penalties across a training run |
| Diagnostics | `doctor()` | Check GPU, VRAM, CUDA, Python version before training starts |
| Checkpointing | `adapter.checkpoint` | Serialize/restore model weights in `.safetensors` format |
| Visualization | `adapter.triptych()` | Generate imagination/real/difference GIF for qualitative eval |
| Export | `adapter.export()` | Bundle weights + config + compliance report into a single artifact directory |

## What the backend owns

`DreamerV3Adapter` (in `physlink.adapters.dreamer`) contains the neural network implementation. PhysLink does not own the learning algorithm.

| Component | Location | Notes |
|-----------|----------|-------|
| RSSM encoder | `DreamerV3Adapter._encoder` | GRU-based recurrent state model |
| Prior / posterior | `DreamerV3Adapter._prior`, `._posterior` | Latent belief update |
| Actor / Critic networks | `DreamerV3Adapter._actor`, `._critic` | Policy and value heads |
| Loss functions | `DreamerV3Adapter.fit()` internals | Reconstruction + KL + policy + value |
| Gradient computation | `torch.autograd` | Not exposed in PhysLink's public interface |

## DreamerV3Adapter: prototype status

**`DreamerV3Adapter` is architecturally inspired by [DreamerV3](https://github.com/danijar/dreamerv3). It is not a wrapper around the original codebase.**

Concretely:

- It implements a Dreamer-like RSSM loop (encoder → GRU → prior/posterior → actor/critic) from scratch in PyTorch.
- It is not validated on standard DreamerV3 benchmarks (DMControl, Atari, …).
- It does not reproduce DreamerV3's symlog transforms, percentile returns, or the full hyperparameter regime.
- Its purpose is to demonstrate the PhysLink interface contract — not to be a production RL backend.

## What would be required to plug a real external backend

1. **Implement `BaseAdapter`** (`physlink.core.adapter.BaseAdapter`) — the adapter protocol requires `fit(trajectories: TrajectoryBatch, steps: int)`, `checkpoint`, and `compliance_report` properties.
2. **Accept PhysLink space objects** — the adapter must consume `ObservationSpace` and `ActionSpace` at construction time and extract dims/dtypes from `space.explain()`.
3. **Call registered invariants** — at each trajectory batch, evaluate invariants via `self._invariants` and accumulate into a `ComplianceReport`.
4. **Write checkpoints in `.safetensors` format** — PhysLink's export pipeline expects this format.

A clean DreamerV3 (Danijar's) backend, or a Stable-Baselines3 wrapper, should be small enough to audit in a single sitting by implementing `BaseAdapter`.

## Summary

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR SIMULATOR  →  TrajectoryBatch  →  DreamerV3Adapter    │
│                                             ↑               │
│                                        BaseAdapter          │
│                                        (PhysLink owns)      │
│                                             ↑               │
│  ObservationSpace  ActionSpace  Invariants  Doctor          │
│  (PhysLink owns)   (PhysLink)   (PhysLink)  (PhysLink)      │
└─────────────────────────────────────────────────────────────┘
```

The learning algorithm above `BaseAdapter` is replaceable. The interfaces below it are stable.
