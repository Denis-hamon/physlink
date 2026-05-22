# Domain Scientists Guide

This guide follows **Samuel's DD-003 path**: a CFD/robotics scientist who needs ML models that respect physical laws.

## The Problem: Physical Hallucinations

Standard ML models trained on simulation data frequently produce **physical hallucinations** — predictions that are statistically plausible but physically impossible:

- Joint angles exceeding mechanical limits
- Instantaneous velocity discontinuities (violating inertia)
- Energy non-conservation across trajectories
- Constraint violations (contact normals, friction cones)

These hallucinations are invisible to standard loss functions but catastrophic in real hardware deployment.

## PhysLink's Approach

PhysLink separates the *representation* of physical spaces from the *validation* of physical constraints. You configure your spaces once, attach invariants to them, and receive structured compliance reports.

## Registering Physical Invariants (preview — Epic 4)

> **Note:** `register_invariant` and `ComplianceReport` are available after **Epic 4**.

```python
from physlink.core.spaces import ObservationSpace, ActionSpace
from physlink.compliance import register_invariant  # available after Epic 4

obs_space = ObservationSpace.from_proprioception(joints=7, include_velocity=True)

# Register a physical constraint: joint velocity must satisfy |dq/dt| ≤ v_max
register_invariant(
    space=obs_space,
    name="joint_velocity_bound",
    fn=lambda obs: (obs["velocity"].abs() <= 10.0).all(),
    severity="critical",
)
```

## ComplianceReport Output (preview — Epic 4)

After running your adaptation loop, generate a compliance report:

```python
report = adapter.compliance_report()
print(report.summary())
```

Expected output:

```
ComplianceReport — 1000 trajectories
  ✅  joint_position_bound   : 1000/1000 passed
  ⚠️  joint_velocity_bound   : 987/1000 passed  (13 violations)
  ❌  energy_conservation    : 421/1000 passed  (579 violations — CRITICAL)

Overall compliance: 80.3% — NOT SAFE FOR HARDWARE DEPLOYMENT
```

## Current Capabilities (v0.1)

- `ObservationSpace.from_proprioception()` — define joint state spaces
- `ActionSpace.continuous()` — define bounded continuous action spaces
- `.explain()` — human-readable space introspection

See the [API Reference](api/index.md) for full documentation.

## Evaluation Path

If you're evaluating PhysLink for your lab's infrastructure, see the [Lab Adoption Guide](lab-adoption-guide.md) for a structured 1-day evaluation checklist.
