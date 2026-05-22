# Getting Started

This guide follows **Hugo's DD-001 path**: configure a 7-DOF robotic arm and run your first adaptation loop in a Colab T4 notebook.

## Step 1 — Install PhysLink

```bash
pip install physlink
# or with GPU support
pip install "physlink[gpu]"
```

## Step 2 — Diagnose your environment

Run the built-in diagnostic scan. It checks your Python version, GPU availability, and required dependencies in under 15 seconds:

```python
import physlink

physlink.doctor()
```

Expected output on a healthy Colab T4:

```
✅ Python 3.12.x
✅ NumPy 1.26.x
✅ PyTorch 2.x (CUDA 12.1)
✅ All checks passed — Go!
```

If any check fails, `doctor()` prints actionable remediation steps.

## Step 3 — Configure ObservationSpace

Define the observation space for a 7-DOF arm with joint positions and velocities:

```python
from physlink.core.spaces import ObservationSpace

obs_space = ObservationSpace.from_proprioception(
    joints=7,
    include_velocity=True,
)
print(obs_space.explain())
```

The `.explain()` method prints a human-readable summary of your space configuration — useful for debugging shape mismatches.

## Step 4 — Configure ActionSpace

Define the continuous action space with per-joint torque bounds:

```python
from physlink.core.spaces import ActionSpace

act_space = ActionSpace.continuous(
    dims=7,
    bounds=[(-1.0, 1.0)] * 7,
)
print(act_space.explain())
```

## Step 5 — Run an adaptation loop

> **Note:** `DreamerV3Adapter` implements a Dreamer-inspired RSSM architecture. It is a prototype adapter, not a wrapper around the original DreamerV3 codebase. See [PRODUCT_THESIS.md](../PRODUCT_THESIS.md) for details on what this means for your use case.

```python
from physlink.adapters import DreamerV3Adapter

adapter = DreamerV3Adapter(
    obs_space=obs_space,
    act_space=act_space,
)
adapter.fit(trajectories)  # TrajectoryBatch from your simulation
```

## Next Steps

- See [Domain Scientists](domain-scientists.md) for physical compliance validation
- See the [API Reference](api/index.md) for full documentation
- See the [Lab Adoption Guide](lab-adoption-guide.md) for institutional evaluation
