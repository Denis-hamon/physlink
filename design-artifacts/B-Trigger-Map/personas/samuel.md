# Persona: Samuel (The Domain Scientist)

**Role:** Expert in Physics/Biology (non-ML specialist)
**Mantra:** "If it violates the laws of physics, it's not a simulation, it's a hallucination."

## Context
Samuel knows his domain (e.g., CFD) perfectly but is an amateur in ML. He needs neural simulators to speed up his hypothesis testing from days to minutes.

## Driving Forces
- **Positive**: Scientific autonomy; no longer depending on a separate ML engineer for every script.
- **Negative**: Extreme skepticism of ML models that violate domain invariants (e.g., conservation of mass).

## Design Requirement
**Universal Space API & Domain Validation Hooks.** Must be able to register physical constraints that the model *must* respect or warn against.
