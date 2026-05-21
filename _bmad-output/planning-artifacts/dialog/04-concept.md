# Product Concept: PhysLink (TBD)

**Step:** Step 7a - Capture Product Concept
**Completed:** 2026-05-20

---

## Core Structural Idea: The Unified World Model "Glue"

PhysLink is the structural abstraction layer that separates the **World Model Architecture** (the brain) from the **Domain Environment** (the body/world). It acts as a universal translator for observation, action, and latent spaces.

---

## Implementation Principle: "Write Once, Adapt Anywhere"

By standardizing how data flows between the environment and the model, PhysLink enables researchers to swap architectures or environments with minimal code changes. It moves the complexity from "custom PyTorch plumbing" to "standardized configuration."

---

## Rationale: Why This Approach?

- **Interchangeability**: Enables objective benchmarking (e.g., comparing JEPA vs. DreamerV3 on the same task).
- **Speed to Science**: Reduces engineering overhead from months of boilerplate to days of experimentation.
- **Reproducibility**: Provides a documented, standard foundation for physical modeling that makes results comparable across labs.

---

## Concrete Example

A PhD student defines their robot's sensors and motors once in a PhysLink configuration. They can then run an experiment with **DreamerV3**, switch to **JEPA** for comparison, and finally test a **custom model**—all using the same data pipeline and evaluation harness—within a single afternoon.

---

## Features Stemming from Concept

- **Universal Space API**: Standardized interfaces for `ObservationSpace`, `ActionSpace`, and `LatentSpace`.
- **Architecture Adapters**: Pre-built "shims" for major models (JEPA, DreamerV3, etc.).
- **Evaluation Harness**: Automated metrics for physical consistency and long-horizon prediction.
- **Interchangeable Buffers**: Standardized trajectory storage for easy sharing and re-training.
