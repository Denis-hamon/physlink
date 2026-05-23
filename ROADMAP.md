# PhysLink — Roadmap

This document describes the three active development tracks for PhysLink v0.1.x. It is a public-facing signal, not a promise — dates are targets, not commitments.

---

## Track 1 — Interface layer (complete)

**Goal:** stable, backend-agnostic data contracts between physics simulators and world model adapters.

| Component | Status |
|-----------|--------|
| `ObservationSpace` / `ActionSpace` | ✓ shipped (v0.1.0) |
| `TrajectoryBatch` / `TrajectoryBuffer` | ✓ shipped (v0.1.0) |
| `DreamerV3Adapter` (Dreamer-inspired RSSM prototype) | ✓ shipped (v0.1.1) |
| `register_invariant` + `ComplianceReport` | ✓ shipped (v0.1.2) |
| `doctor()` environment diagnostic | ✓ shipped (v0.1.0) |

The public API (`physlink.__all__`) is stable across minor versions of the v0.1.x series.

---

## Track 2 — Data quality gate (in progress)

**Goal:** a typed, reproducible quality contract for trajectory datasets — so bad data fails fast, before a training run starts.

| Component | Status |
|-----------|--------|
| `TrajectorySchema` — schema contract (obs_dims, act_dims, action_bounds) | ✓ shipped (v0.1.3) |
| `TrajectoryBatch.quality_report(schema)` — run all checks, return `TrajectoryQualityReport` | ✓ shipped (v0.1.3) |
| Reference dataset + reproducible quality report | ✓ committed at `examples/` |
| Integration with `adapter.fit()` — reject on schema FAIL | planned |

---

## Track 3 — World model evaluation harness (complete)

**Goal:** measure whether the adapter's world model is actually useful via the
[world-model-eval-lab](https://github.com/Denis-hamon/world-model-eval-lab) (WMEL)
benchmark harness rather than building duplicate evaluation infrastructure.

| Component | Status |
|-----------|--------|
| `DreamerWMELAdapter` bridge — `physlink.adapters.wmel_bridge` | ✓ shipped |
| `examples/wmel_integration.py` — end-to-end walkthrough | ✓ shipped |
| `physlink[eval]` optional dependency group | ✓ shipped |
| WMEL environments (maze_toy, two-room, DMC Acrobot) | via [world-model-eval-lab](https://github.com/Denis-hamon/world-model-eval-lab) |
| CPG (Counterfactual Planning Gap) metric | via world-model-eval-lab v0.14 |

The bridge implements `LeWMAdapterStub` via random-shoot MPC in latent space:
`encode()` (posterior mean), `rollout()` (prior imagination), `score()` (L2 in z-space), `plan()`.

Install: `pip install "physlink[eval]"` then see `examples/wmel_integration.py`.

No claim is made about learning performance — see [EXPERIMENT_CARD.md](EXPERIMENT_CARD.md) for what the current prototype does and does not prove.

---

## Non-goals for v0.1.x

- Reproducing DreamerV3's benchmark scores on DMControl, Atari, or ProcGen
- A managed cloud service or hosted training infrastructure
- Support for multi-agent environments
- Real-time inference latency guarantees
