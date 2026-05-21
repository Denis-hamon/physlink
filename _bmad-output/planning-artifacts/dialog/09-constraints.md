# Constraints & Design Parameters: PhysLink (TBD)

**Step:** Step 10 - Capture Constraints
**Completed:** 2026-05-20

---

## Technical Constraints (Inflexible)

| Parameter | Requirement | Rationale |
|-----------|-------------|-----------|
| **Language** | **Pure Python** | Mandatory for the target PhD audience; zero friction for existing Conda/PyTorch envs. |
| **Backend** | **PyTorch Primary** | Deeply embedded in the Embodied AI community; abstractions must be JAX-ready but PyTorch-first. |
| **Hardware** | **Single GPU (A100/3090/4090)** | Must run on consumer/mid-tier lab hardware. Foundational use cases must finish within 2 hours on a single GPU. |
| **API Stability** | **Stable from v0.1** | Infrastructure trust is fragile. No breaking changes without a documented deprecation cycle. |

---

## Perception & Brand Constraints (Inflexible)

- **Language**: **English only** for all documentation, code, issues, and communication.
- **Scientific Credibility**: **Mandatory arXiv Position Paper** (4-6 pages) published concurrently with the public launch.
- **Code Hygiene**: "Surgical cleanliness" at launch (no TODOs, no redundant files, no unused dependencies).

---

## Strategic Timeline (Fixed Windows)

- **MVP Window (4-6 Months)**: Must have a functional foundation case (e.g., DreamerV3 adapter) and a draft position paper.
- **Target Conferences**: Alignment with **CoRL** (submission June) and **NeurIPS Workshops** (deadlines Sept/Oct).

---

## Flexible Parameters (Liquid)

- **Naming**: Current placeholders (PhysLink, LatentOps) are liquid. Final name needs to be SEO-friendly and available on PyPI.
- **Initial Model**: DreamerV3 is the lead candidate, but JEPA or other emerging models are options depending on timing.
- **Initial Scope**: Can be narrowed to a single domain (e.g., Robotic Manipulation) to ensure depth over breadth.
- **Governance/Licensing**: MIT vs. Apache 2.0 (to be decided before launch).
