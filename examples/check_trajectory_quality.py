#!/usr/bin/env python3
"""Generate a reference trajectory dataset and run the quality gate.

Usage:
    python examples/check_trajectory_quality.py

Outputs:
    examples/data/reference_trajectory.jsonl   -- synthetic 7-DOF arm trajectories
    examples/trajectory_quality_report.json    -- quality gate results (PASS/WARN/FAIL)

The synthetic data models a 7-joint robot arm performing reach-and-retract
motions under a PD controller with injected Gaussian noise. Seed is fixed at
42 for full reproducibility.

Exit code 0 = all checks PASS; exit code 1 = any check FAIL.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import physlink

# ── Constants ──────────────────────────────────────────────────────────────────

SEED = 42
N_EPISODES = 10
STEPS_PER_EPISODE = 50
N_JOINTS = 7

DATA_DIR = Path(__file__).parent / "data"
JSONL_PATH = DATA_DIR / "reference_trajectory.jsonl"
REPORT_PATH = Path(__file__).parent / "trajectory_quality_report.json"


# ── Synthetic data generation ─────────────────────────────────────────────────

def _generate_episode(episode_id: int, rng: random.Random) -> list[dict[str, Any]]:
    """Simulate one episode: 7-DOF arm reaching a random target via PD control."""
    target = [rng.uniform(-1.2, 1.2) for _ in range(N_JOINTS)]
    pos = [rng.gauss(0.0, 0.05) for _ in range(N_JOINTS)]
    vel = [0.0] * N_JOINTS
    dt = 0.02  # 50 Hz

    steps = []
    for step in range(STEPS_PER_EPISODE):
        kp, kd = 2.0, 0.3
        action = [
            max(-1.0, min(1.0, kp * (target[j] - pos[j]) - kd * vel[j] + rng.gauss(0.0, 0.02)))
            for j in range(N_JOINTS)
        ]
        acc = [action[j] - 0.5 * vel[j] for j in range(N_JOINTS)]
        vel = [vel[j] + acc[j] * dt for j in range(N_JOINTS)]
        pos = [pos[j] + vel[j] * dt for j in range(N_JOINTS)]
        obs = (
            [pos[j] + rng.gauss(0.0, 0.005) for j in range(N_JOINTS)]
            + [vel[j] + rng.gauss(0.0, 0.010) for j in range(N_JOINTS)]
        )
        err = sum((target[j] - pos[j]) ** 2 for j in range(N_JOINTS)) / N_JOINTS
        steps.append({
            "episode_id": episode_id,
            "step": step,
            "obs": [round(v, 6) for v in obs],
            "action": [round(v, 6) for v in action],
            "reward": round(math.exp(-err), 6),
            "done": step == STEPS_PER_EPISODE - 1,
        })
    return steps


def generate_dataset(seed: int = SEED) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    return [step for ep in range(N_EPISODES) for step in _generate_episode(ep, rng)]


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    obs_space = physlink.ObservationSpace.from_proprioception(
        joints=N_JOINTS, include_velocity=True
    )
    act_space = physlink.ActionSpace.continuous(
        dims=N_JOINTS, bounds=[(-1.0, 1.0)] * N_JOINTS
    )
    schema = physlink.TrajectorySchema(
        obs_dims=obs_space.dims,
        act_dims=act_space.dims,
        action_bounds=(-1.0, 1.0),
    )

    print("PhysLink — trajectory quality gate")
    print(f"Generating {N_EPISODES} episodes × {STEPS_PER_EPISODE} steps (seed={SEED})...")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dataset = generate_dataset()
    batch = physlink.TrajectoryBatch.from_list(dataset)

    with JSONL_PATH.open("w", encoding="utf-8") as f:
        for traj in dataset:
            f.write(json.dumps(traj, separators=(",", ":")) + "\n")
    print(f"  Written {len(dataset)} steps → {JSONL_PATH}")

    print("Running quality checks...")
    report = batch.quality_report(schema)
    print(report)

    base = report.to_dict()
    base["data_source"] = str(JSONL_PATH.relative_to(Path(__file__).parent))
    base["summary"].update({
        "mean_episode_length": float(STEPS_PER_EPISODE),
        "obs_dims": obs_space.dims,
        "act_dims": act_space.dims,
        "seed": SEED,
    })
    # Reorder to match canonical format: schema_version, data_source, summary, checks, overall
    report_dict = {
        "schema_version": base["schema_version"],
        "data_source": base["data_source"],
        "summary": base["summary"],
        "checks": base["checks"],
        "overall": base["overall"],
    }

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)
    print(f"  Report → {REPORT_PATH}")

    print(f"\nOverall: {report.overall}")
    if report.overall == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
