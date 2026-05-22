# Product Thesis: The Missing Interface Between World Models and Physical Domains

PhysLink is a technical product prototype built around one belief:

> World models will not become useful in physical domains through model quality alone. They also
> need explicit interfaces for data, actions, domain constraints, evaluation, and trust.

This thesis lives next to the code on purpose. The repository is not only an implementation
exercise; it is a way to test which interfaces make a physical ML workflow easier to inspect,
evaluate, and hand to another person.

Research on learned dynamics can move quickly inside a lab where data conventions, evaluation
scripts, compute environments, and domain assumptions are already shared. The same model becomes
harder to adopt when those assumptions are implicit. A researcher then spends time rebuilding
observation mappings, action contracts, environment checks, checkpoints, comparison scripts, and
domain validation before they can ask the scientific question they actually care about.

That product gap is the reason PhysLink exists.

## The Product Problem

Physical AI work sits across three different kinds of expertise:

| Perspective | What it needs |
| --- | --- |
| ML research | Models, representations, rollouts, experiments, and honest evaluation |
| Data and software engineering | Schemas, validation, reproducibility, observability, and artifacts that survive handoffs |
| Domain science | Constraints that make a result scientifically or operationally acceptable |

When the interface between those perspectives is missing, each new experiment absorbs the cost:

- A PhD student can lose an afternoon to framework plumbing before they see a first result.
- A lab lead can struggle to compare runs produced by students with subtly different data paths.
- A domain expert can reject a fast learned simulator if it violates a constraint that was never
  represented in the ML workflow.

The failure mode is not only slow onboarding. It is false confidence. A low prediction loss, a
clean visualization, or a working notebook can hide a broken action contract, data drift, a
long-horizon failure, or a domain violation.

## The Thesis

A useful world-model product layer should make five things explicit.

### 1. Data contracts before model convenience

Physical trajectories are not generic tensors. Observations, actions, time, units, bounds, missing
values, and provenance all shape what a model can learn and what an evaluator can trust.

The first job of a product layer is to turn those assumptions into inspectable contracts. In
PhysLink v0.1, that starts narrowly with observation and action spaces. A serious next layer must go
further: typed trajectory schemas, quality checks, dataset metadata, repeatable splits, and failure
reports before training.

### 2. Evaluation beyond a single training signal

For world models, "it trains" is not a decision criterion. Evaluation needs to expose the gap
between a model that reconstructs local dynamics and a model that remains useful under action,
rollout horizon, perturbation, and domain constraints.

That means product surfaces for:

- short-horizon and long-horizon prediction behavior;
- action-conditioned sensitivity, not only passive reconstruction;
- physical or operational constraint violations;
- failure slices, not only aggregate metrics;
- experiment artifacts that another person can inspect and rerun.

### 3. Domain constraints as first-class evidence

In physical domains, a domain expert is not a late-stage reviewer of an ML demo. They define part of
the acceptance criteria. Conservation rules, joint limits, actuator bounds, contact assumptions, and
other invariants should be visible in the workflow.

PhysLink explores this through plain Python invariant hooks and compliance reports. The product
idea is broader than that implementation: domain validity should be recorded as evidence next to ML
metrics, not buried in an ad hoc notebook cell.

### 4. Inspectability as an adoption feature

Abstraction helps only when users can defend it. Researchers need to understand what data entered a
run, what checks passed, what model path executed, what artifacts were produced, and where failure
occurred.

That is why diagnostics, explicit space descriptions, progress feedback, checkpoints, and exportable
reports matter. They are not polish around research code. They reduce the trust cost of trying a new
workflow.

### 5. Accessibility without pretending the hard parts disappeared

The first useful result should fit the reality of an ambitious but resource-constrained researcher:
a laptop, a shared GPU, or a free notebook runtime. Fast entry matters because it determines whether
the tool reaches a real workflow.

But accessibility must not turn into hype. A one-afternoon prototype is not a general standard, a
toy benchmark is not a safety argument, and a Dreamer-inspired adapter is not automatically a
production DreamerV3 integration.

## Why PhysLink Starts Where It Starts

PhysLink v0.1 is deliberately narrow. It is not an attempt to solve world-model infrastructure in
one release. It is a probe into the interface.

The prototype starts with a "Friday afternoon" path:

1. diagnose the environment before an expensive run;
2. define observation and action spaces in an explicit API;
3. run a small world-model adaptation loop with visible progress and checkpoints;
4. attach a domain invariant and inspect a compliance report;
5. export artifacts that can be shared or reviewed.

Those choices come from three user pressures:

- the researcher who needs a first result quickly but refuses black-box plumbing;
- the lab lead who needs runs and data paths that remain comparable across people;
- the domain scientist who will not trade physical validity for ML velocity.

This is why the first surface area is not a large model zoo. It is the connective tissue around
configuration, diagnostics, data flow, validation, and reviewable artifacts.

## What This Prototype Tests

PhysLink currently tests product hypotheses more than it claims ecosystem maturity.

| Hypothesis | Prototype surface |
| --- | --- |
| Fast setup changes willingness to try a physical ML workflow | install path, Colab path, `physlink.doctor()` |
| Explicit contracts reduce silent integration mistakes | `ObservationSpace`, `ActionSpace`, validation errors |
| Domain experts need an entry point into model acceptance | invariant registration and compliance reports |
| Research tooling earns trust through inspectable artifacts | progress, checkpoints, exports, docs, CI |

The intended signal is not "all world models now share one standard." The intended signal is that a
world-model workflow becomes more credible when its hidden assumptions become product surfaces.

## Non-Goals for the Prototype

PhysLink v0.1 does not claim to:

- establish a state-of-the-art model result;
- replace the evaluation judgment of a researcher or domain expert;
- certify physical correctness or deployment safety;
- provide a production wrapper for every external world-model codebase.

Those would require stronger data, evaluation, backend, and domain evidence than the current
prototype contains.

## What Is Still Missing

The thesis is larger than the current implementation. The most important missing work is visible:

- richer trajectory schemas with timestamp, unit, provenance, and data-quality validation;
- an evaluation harness with baselines, long-horizon drift, action-conditioning checks, and failure
  slices;
- real backend integrations and adapter boundaries tested against external model codebases;
- dataset lineage and experiment comparison that survive lab handoffs;
- support for richer physical observations beyond small proprioceptive examples;
- a clearer bridge from predictive quality to planning usefulness and operational risk.

These are not footnotes. They are the next tests of whether the product thesis holds.

## Product Standard

The success metric for a project like this should not be a polished screenshot or a spike in stars.
The stronger signal is co-ownership by real users:

- a researcher can rerun and challenge an evaluation;
- a lab can compare experiments without rebuilding every contract from scratch;
- a domain expert can add a constraint or failure case that changes the acceptance bar;
- an external contributor can improve the workflow because the interfaces are explicit.

PhysLink is an early artifact toward that standard. Its value is in making the interface problem
concrete enough to build, test, criticize, and improve.

