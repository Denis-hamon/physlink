# For Domain Scientists

This page is for you if you need ML models that respect physics — not just models that *look* plausible in simulation, but models that provably conserve mass, energy, momentum, and the constraints your domain imposes.

## Philosophy: Physical Hallucinations

Standard ML models trained on simulation data frequently produce **physical hallucinations** — predictions that are statistically plausible but physically impossible. A model minimising MSE on trajectory data has no reason to conserve mass, honour contact normals, or respect inertia. Its loss function is physics-blind.

The result: joint angles that exceed mechanical stops, velocities that instantaneously teleport, fluid flows that create mass from nothing. These errors are invisible during training but catastrophic on real hardware. The model learns the *shape* of physical trajectories without learning the *laws* that govern them.

PhysLink addresses this by separating representation from validation. You register your domain's physical constraints as plain Python callables; PhysLink enforces them during adaptation and surfaces violations in a structured compliance report.

## Registering a Physical Invariant

Register your domain constraint as a plain Python callable. The function receives a trajectory dictionary and returns a **residual** — a float where `0.0` means perfect compliance.

### mass_conservation Example

```python
from physlink import DreamerV3Adapter, register_invariant

# Assume adapter is already constructed (see getting-started.md)
def mass_conservation(trajectory: dict) -> float:
    """Returns residual: absolute difference between mass_in and mass_out."""
    return abs(trajectory["mass_flow_in"] - trajectory["mass_flow_out"])

register_invariant(
    adapter,
    name="mass_conservation",
    fn=mass_conservation,
    tolerance=0.01,
    mode="hard",
)

report = adapter.compliance_report()
print(report.summary())
```

Expected output:

```
mass_conservation: PASS (max_residual=0.007, threshold=0.01, violations=0/1000)
```

> **Any physical domain works with the same pattern.**
> CFD: energy conservation — robotics: momentum conservation — climate: mass conservation.
> Write your invariant as `fn(trajectory: dict) -> float`, plug it in, and PhysLink enforces it.

## What's Next?

Run the worked example end-to-end in Google Colab — no local install required:

**[Open Domain Scientist Colab →](https://colab.research.google.com/github/Denis-hamon/physlink/blob/main/notebooks/domain-scientist-colab.ipynb)**

The notebook walks through the full Samuel path: configure spaces, attach `mass_conservation`, run adaptation, and inspect the ComplianceReport in an interactive environment.

---

If you're evaluating PhysLink for your lab's infrastructure, see the [Lab Adoption Guide](lab-adoption-guide.md) for a structured 1-day evaluation checklist.
