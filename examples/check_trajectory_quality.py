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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────────────────────────────────

SEED = 42
N_EPISODES = 10
STEPS_PER_EPISODE = 50
N_JOINTS = 7
OBS_DIMS = N_JOINTS * 2  # joint positions + joint velocities
ACT_DIMS = N_JOINTS      # joint torque commands, normalised to [-1, 1]

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


# ── Quality checks ─────────────────────────────────────────────────────────────

@dataclass
class Check:
    name: str
    status: str  # PASS | WARN | FAIL
    details: str
    count_checked: int = 0
    count_failed: int = 0


def _schema(data: list[dict[str, Any]]) -> Check:
    required = {"obs", "action"}
    bad = [i for i, d in enumerate(data) if not required.issubset(d)]
    if bad:
        return Check("schema_conformance", "FAIL", f"{len(bad)} trajectories missing required keys", len(data), len(bad))
    return Check("schema_conformance", "PASS", f"{len(data)}/{len(data)} trajectories have required keys", len(data))


def _obs_dims(data: list[dict[str, Any]]) -> Check:
    bad = [i for i, d in enumerate(data) if len(d.get("obs", [])) != OBS_DIMS]
    if bad:
        return Check("obs_dimension_consistency", "FAIL", f"{len(bad)} trajectories have wrong obs dim (expected {OBS_DIMS})", len(data), len(bad))
    return Check("obs_dimension_consistency", "PASS", f"All obs vectors are {OBS_DIMS}-dimensional", len(data))


def _act_dims(data: list[dict[str, Any]]) -> Check:
    bad = [i for i, d in enumerate(data) if len(d.get("action", [])) != ACT_DIMS]
    if bad:
        return Check("act_dimension_consistency", "FAIL", f"{len(bad)} trajectories have wrong action dim (expected {ACT_DIMS})", len(data), len(bad))
    return Check("act_dimension_consistency", "PASS", f"All action vectors are {ACT_DIMS}-dimensional", len(data))


def _action_range(data: list[dict[str, Any]]) -> Check:
    total, oob = 0, 0
    for d in data:
        for v in d.get("action", []):
            total += 1
            if v < -1.0 or v > 1.0:
                oob += 1
    if oob:
        return Check("action_range", "FAIL", f"{oob}/{total} action values outside [-1, 1]", total, oob)
    return Check("action_range", "PASS", f"All {total} action values in [-1.0, 1.0]", total)


def _obs_finite(data: list[dict[str, Any]]) -> Check:
    total, bad = 0, 0
    for d in data:
        for v in d.get("obs", []):
            total += 1
            if not math.isfinite(v):
                bad += 1
    if bad:
        return Check("obs_finite", "FAIL", f"{bad}/{total} obs values are NaN or Inf", total, bad)
    return Check("obs_finite", "PASS", f"No NaN or Inf in {total} obs values", total)


def _episode_termination(data: list[dict[str, Any]]) -> Check:
    eps: dict[int, list[dict]] = {}
    for d in data:
        eps.setdefault(d.get("episode_id", 0), []).append(d)
    incomplete = [ep for ep, steps in eps.items() if not steps[-1].get("done", False)]
    if incomplete:
        return Check("episode_termination", "WARN", f"{len(incomplete)} episodes do not end with done=True", len(eps), len(incomplete))
    return Check("episode_termination", "PASS", f"{len(eps)}/{len(eps)} episodes terminate with done=True", len(eps))


def run_checks(data: list[dict[str, Any]]) -> list[Check]:
    return [_schema(data), _obs_dims(data), _act_dims(data), _action_range(data), _obs_finite(data), _episode_termination(data)]


# ── Report assembly ────────────────────────────────────────────────────────────

def build_report(data: list[dict[str, Any]], checks: list[Check], source: str) -> dict[str, Any]:
    eps: dict[int, int] = {}
    for d in data:
        eps[d.get("episode_id", 0)] = eps.get(d.get("episode_id", 0), 0) + 1
    mean_len = sum(eps.values()) / len(eps) if eps else 0
    overall = (
        "FAIL" if any(c.status == "FAIL" for c in checks)
        else "WARN" if any(c.status == "WARN" for c in checks)
        else "PASS"
    )
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": source,
        "summary": {
            "total_steps": len(data),
            "episodes": len(eps),
            "mean_episode_length": round(mean_len, 1),
            "obs_dims": OBS_DIMS,
            "act_dims": ACT_DIMS,
            "seed": SEED,
        },
        "checks": [
            {
                "name": c.name,
                "status": c.status,
                "details": c.details,
                **({"count_checked": c.count_checked, "count_failed": c.count_failed} if c.count_checked else {}),
            }
            for c in checks
        ],
        "overall": overall,
    }


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    print("PhysLink — trajectory quality gate")
    print(f"Generating {N_EPISODES} episodes × {STEPS_PER_EPISODE} steps (seed={SEED})...")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dataset = generate_dataset()

    with JSONL_PATH.open("w", encoding="utf-8") as f:
        for traj in dataset:
            f.write(json.dumps(traj, separators=(",", ":")) + "\n")
    print(f"  Written {len(dataset)} steps → {JSONL_PATH}")

    print("Running quality checks...")
    checks = run_checks(dataset)
    for c in checks:
        icon = "✓" if c.status == "PASS" else ("⚠" if c.status == "WARN" else "✗")
        print(f"  [{icon}] {c.name}: {c.details}")

    source = str(JSONL_PATH.relative_to(Path(__file__).parent))
    report = build_report(dataset, checks, source)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  Report → {REPORT_PATH}")

    overall = report["overall"]
    print(f"\nOverall: {overall}")
    if overall == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
