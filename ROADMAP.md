# PhysLink Roadmap

PhysLink is an early prototype. The [product thesis](PRODUCT_THESIS.md) explains why it starts with
explicit interfaces around physical ML workflows. This roadmap turns that thesis into the next
three evidence-building workstreams.

The roadmap is intentionally short. It is not a promise of a broad platform or a model zoo. Each
workstream should make one claim more testable before the project makes larger claims.

## 1. Trajectory Schema & Data Quality

### Product question

Can PhysLink make the assumptions inside physical trajectory data visible before training starts?

### Why this comes first

World-model workflows fail quietly when observations, actions, sequence boundaries, timestamps,
units, and provenance are implicit. A model adapter is not a strong interface if two users can feed
it materially different trajectories while believing they ran the same experiment.

### Planned surface

- A typed trajectory schema with explicit observation, action, sequence, and metadata fields.
- Validation for shape, bounds, missing values, sequence length, and action/observation alignment.
- Dataset metadata that records provenance, units where available, splits, and transformation steps.
- A data-quality report that separates hard failures from warnings a researcher may choose to accept.

### Evidence to produce

- A small reference dataset or simulator export that exercises the schema.
- Failing examples for malformed data, not only passing examples.
- A reproducible report showing which data checks ran before adaptation.
- Tests for schema round-trips and validation behavior.

### Exit criteria

PhysLink can reject or explain the most important data-contract failures before a training loop
starts, and two users can inspect the same trajectory artifact without inferring its structure from
notebook code.

## 2. World Model Evaluation Harness

### Product question

Can PhysLink help decide what a world-model run is useful for instead of reducing evaluation to
"the loop trained"?

### Why this matters

Short-horizon reconstruction quality is not enough evidence for a physical workflow. A model may
look stable in one metric while drifting over longer rollouts, ignoring action changes, or violating
domain constraints that determine whether its output is useful.

### Planned surface

- Baselines that make a learned model earn its complexity.
- Evaluation slices for short-horizon prediction, long-horizon drift, and action-conditioned
  behavior.
- Constraint reporting that can place physical invariant failures next to ML metrics.
- A reviewable evaluation artifact with metrics, plots, run configuration, and failure examples.

### Evidence to produce

- One end-to-end experiment with a stated hypothesis, setup, baselines, metrics, and limitations.
- Comparable reports for at least one simple baseline and one learned dynamics path.
- Failure cases where an aggregate metric alone would hide a relevant weakness.
- Tests that keep metric computation and report generation deterministic where practical.

### Exit criteria

A reviewer can read an evaluation report and understand what the run supports, what it does not
support, and which observed failures should block a stronger product or scientific claim.

## 3. External Backend Integration Boundary

### Product question

Can PhysLink define a useful adapter boundary without pretending all world-model codebases share the
same training contract?

### Why this comes after data and evaluation

An external backend integration is only meaningful when the data contract and evidence surface are
clear. Otherwise the adapter hides incompatibilities behind a convenient API and makes comparisons
less trustworthy.

### Planned surface

- A backend protocol for the inputs, artifacts, and capabilities PhysLink expects.
- Capability flags for differences such as training, rollout, checkpoint import/export, and
  evaluation support.
- One external integration used to test the boundary against real third-party model code.
- Documentation that separates PhysLink-owned abstractions from backend-owned semantics.

### Evidence to produce

- A contract test suite that adapters must satisfy.
- A compatibility note for the first external backend, including unsupported paths.
- A migration note for the current Dreamer-inspired prototype path if the public boundary changes.
- A minimal example that runs the same validated data and evaluation surfaces through the backend
  boundary where capabilities allow it.

### Exit criteria

PhysLink can integrate one external backend honestly: users can see what is standardized, what
remains backend-specific, and what evidence is comparable across runs.

## What Comes Later

These workstreams deliberately precede wider ambitions such as more domains, richer observations,
planning-oriented decision metrics, and managed execution across larger compute environments.

The order matters:

1. make data assumptions inspectable;
2. make run evidence reviewable;
3. make backend interchangeability testable.

