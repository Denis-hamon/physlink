# Platform & Device Strategy: PhysLink (TBD)

**Step:** Step 10a - Define Platform & Device Strategy
**Completed:** 2026-05-20

---

## Primary Distribution: PyPI & GitHub

PhysLink is a **pure Python toolkit**. The primary distribution channel is **PyPI**, with the source code and issue tracking hosted on **GitHub**.

| Component | Goal | Rationale |
|-----------|------|-----------|
| **`pip install`** | Zero-error installation. | First contact must be frictionless for the "Friday Afternoon Test." |
| **`physlink doctor`** | Instant environment diagnostic. | Confirms CUDA, PyTorch, and dependencies are correctly configured in <30 seconds. |

---

## Primary "Device": The Notebook (Jupyter/Colab)

The **Jupyter Notebook** (local) and **Google Colab** (cloud) are the primary interaction models.

- **Colab Compatibility**: The foundational demonstration notebook **must run on the free Colab T4 tier** in under 90 minutes. This ensures global accessibility for labs without high-end local GPU infrastructure.
- **Linear Workflow**: All demonstration notebooks must follow a strict linear execution (no hidden state) to ensure reproducibility.

---

## Visualization Strategy: The "Zero-Friction" Approach

Visualizing world model "imaginations" is critical for research validation. We adopt a two-layered strategy:

1. **Layer 0 (Embedded/Offline)**: Inline rendering in notebooks using standard libraries (matplotlib, imageio). GIFs or image sequences of real vs. imagined trajectories. No external accounts or internet required.
2. **Layer 1 (Optional/Advanced)**: Modular integrations with **Weights & Biases** and **Rerun**. These are only activated if the libraries are present, ensuring no user is blocked by their absence.

---

## Architectural Optionality: Serializability

While cluster support (SLURM) is Phase 2, the core architecture must support **job serialization** from day one.

- **`AdaptationJob`**: Must be definable, saveable (JSON/YAML), and resumable from checkpoints. This allows future scaling to cloud/clusters without refactoring the core API.

---

## Strategic Implications

- **No Dedicated CLI**: Beyond the `doctor` command, avoid custom CLI overhead in the MVP.
- **No Hidden Dependencies**: All Layer 0 visualization must work out-of-the-box.
- **Documentation as Product**: High-quality, reproducible notebooks are the primary "UI" of the toolkit.
