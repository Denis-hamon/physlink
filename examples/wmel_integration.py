#!/usr/bin/env python3
"""PhysLink x WMEL integration example.

Demonstrates how to wrap a trained DreamerV3Adapter with DreamerWMELAdapter
and evaluate it using the world-model-eval-lab (WMEL) benchmark harness.

Prerequisites:
    pip install physlink
    pip install "git+https://github.com/Denis-hamon/world-model-eval-lab.git"
    # or:
    pip install "physlink[eval]"

Usage:
    python examples/wmel_integration.py

Sections:
    1. Train a DreamerV3Adapter on synthetic data (no WMEL required)
    2. Create the bridge (DreamerWMELAdapter)
    3. Run a WMEL benchmark against maze_toy (requires WMEL)
    4. Print the scorecard
"""

from __future__ import annotations

import math
import random
from typing import Any

import physlink

# ── 1. Generate synthetic training data ───────────────────────────────────────

SEED = 42
N_JOINTS = 7
N_EPISODES = 20
STEPS_PER_EPISODE = 50

rng = random.Random(SEED)


def _simulate_episode(episode_id: int) -> list[dict[str, Any]]:
    target = [rng.uniform(-1.2, 1.2) for _ in range(N_JOINTS)]
    pos = [rng.gauss(0.0, 0.05) for _ in range(N_JOINTS)]
    vel = [0.0] * N_JOINTS
    steps = []
    for step in range(STEPS_PER_EPISODE):
        kp, kd = 2.0, 0.3
        action = [
            max(-1.0, min(1.0, kp * (target[j] - pos[j]) - kd * vel[j] + rng.gauss(0.0, 0.02)))
            for j in range(N_JOINTS)
        ]
        acc = [action[j] - 0.5 * vel[j] for j in range(N_JOINTS)]
        vel = [vel[j] + acc[j] * 0.02 for j in range(N_JOINTS)]
        pos = [pos[j] + vel[j] * 0.02 for j in range(N_JOINTS)]
        obs = (
            [pos[j] + rng.gauss(0.0, 0.005) for j in range(N_JOINTS)]
            + [vel[j] + rng.gauss(0.0, 0.010) for j in range(N_JOINTS)]
        )
        err = sum((target[j] - pos[j]) ** 2 for j in range(N_JOINTS)) / N_JOINTS
        steps.append({
            "episode_id": episode_id,
            "step": step,
            "obs": obs,
            "action": action,
            "reward": math.exp(-err),
            "done": step == STEPS_PER_EPISODE - 1,
        })
    return steps


dataset = [step for ep in range(N_EPISODES) for step in _simulate_episode(ep)]
batch = physlink.TrajectoryBatch.from_list(dataset)

# Validate data quality before training
schema = physlink.TrajectorySchema(obs_dims=N_JOINTS * 2, act_dims=N_JOINTS)
report = batch.quality_report(schema)
print(report)
assert report.overall == "PASS", "Training data failed quality gate"

# ── 2. Build and train the adapter ────────────────────────────────────────────

obs_space = physlink.ObservationSpace.from_proprioception(
    joints=N_JOINTS, include_velocity=True
)
act_space = physlink.ActionSpace.continuous(
    dims=N_JOINTS, bounds=[(-1.0, 1.0)] * N_JOINTS
)
adapter = physlink.DreamerV3Adapter(obs_space, act_space)

print("\nTraining DreamerV3Adapter for 500 steps (quick demo)...")
adapter.fit(batch, steps=500)

# ── 3. Wrap for WMEL ──────────────────────────────────────────────────────────

from physlink.adapters.wmel_bridge import DreamerWMELAdapter  # noqa: E402

bridge = DreamerWMELAdapter(adapter, n_candidates=50, device="cpu")
print(f"\nBridge ready: {bridge.name}")

# ── 4. Run a WMEL benchmark ───────────────────────────────────────────────────
#
# The maze_toy environment is a simple 2-D grid included with WMEL.
# Actions: {"up", "down", "left", "right"}
#
# Note: PhysLink's continuous action space doesn't match WMEL's discrete maze
# actions directly — this section shows the wiring pattern. For a real benchmark,
# implement a BenchmarkEnvironment that wraps your physics simulator and returns
# observations compatible with obs_space.dims.

try:
    from wmel import BenchmarkRunner
    from wmel.envs.maze_toy import MazeToyEnvironment

    def env_factory() -> MazeToyEnvironment:
        return MazeToyEnvironment(grid_size=5, seed=SEED)

    runner = BenchmarkRunner(
        env_factory=env_factory,
        policy=bridge,
        horizon=20,
        episodes=30,
        seed=SEED,
    )
    scorecard = runner.run()
    print("\n── WMEL Scorecard ───────────────────────────────────────────────")
    print(scorecard)

except ImportError:
    print(
        "\nwmel not installed — skipping benchmark runner.\n"
        "  Install: pip install "
        "'git+https://github.com/Denis-hamon/world-model-eval-lab.git'"
    )
except Exception as exc:
    # Environment shape mismatch or other runtime issues — show the error but
    # don't crash the demo.
    print(f"\nBenchmark runner raised: {type(exc).__name__}: {exc}")
    print("This is expected if the env's observation shape differs from obs_space.dims=14.")
    print("Implement a BenchmarkEnvironment wrapping your own simulator to run a real eval.")
