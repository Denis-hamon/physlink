---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/implementation-artifacts/E-Development/001-prd-scenario-01.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/deliveries/DD-001-hugos-friday-afternoon-test.yaml
  - _bmad-output/deliveries/DD-002-petras-lab-standard-rollout.yaml
  - _bmad-output/deliveries/DD-003-samuels-dignity-validation.yaml
  - _bmad-output/deliveries/DD-001-handoff-log.md
  - _bmad-output/deliveries/DD-002-handoff-log.md
  - _bmad-output/deliveries/DD-003-handoff-log.md
---

# PhysLink - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for PhysLink, decomposing the requirements from the PRD, UX Design deliveries (DD-001/002/003), and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-01: `physlink.doctor()` — CLI + API diagnostic. Scans Go/No-Go in < 15 seconds: Python version, PyTorch presence, CUDA availability, VRAM, Colab session estimate. Output: structured table with [OK]/[WARN]/[FAIL] text labels (no color-only). GO verdict as callout; NO-GO with one actionable fix per failed check.

FR-02: Universal Space API — `ObservationSpace.from_proprioception(joints, include_velocity, ...)` and `ActionSpace.continuous(dims, bounds)` with immediate type/dimension validation on creation. Each object implements `.explain()` returning a metadata dict (clipping, normalization details).

FR-03: DreamerV3 Adapter — `DreamerV3Adapter(obs_space, act_space)`. `.fit(trajectories, steps, checkpoint_interval_steps)` triggers the adaptation loop with an async progress bar showing step count, ETA, prediction health (OK/ANOMALY), and throughput. Auto-checkpoint every N steps; checkpoint path printed. Toggleable debug hooks panel showing pipeline stage statuses.

FR-04: Triptych Validation — `.visualize(trajectories)` produces a 3-panel GIF (Imagination / Real / Difference). Time-to-Science callout computes elapsed time vs a traditional from-scratch baseline. Separated from `compliance_report()` — never coupled in the same code path.

FR-05: `adapter.export(path)` — produces an artifact list (GIF, YAML config, summary). Valid YAML containing space config and checkpoint path. Share panel copies notebook URL to clipboard.

FR-06: `register_invariant(adapter, name, fn, tolerance, mode)` — attaches a physical invariant check to an adapter. Accepts a plain Python callable `fn(trajectory: dict) -> float` (no subclasses, no decorators). `mode="hard"` rejects trajectories where residual > tolerance; `mode="soft"` penalizes the loss.

FR-07: `adapter.compliance_report()` → `ComplianceReport` pure data object. `report.summary()` → str formatted as `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`. `report.violations()` → list with trajectory index, field values, residual, and "Possible cause:" text. `report.plot(title, show_threshold)` → matplotlib histogram with vertical threshold line (inline Colab). `report.export(path)` → JSON file.

FR-08: `AdaptationConfig` (immutable, YAML/JSON-serializable) and `AdaptationRun` (stateful, temporary). `TrajectoryBuffer.export(path)` / `.load(path)`.

### NonFunctional Requirements

NFR-01: `physlink.doctor()` execution < 15 seconds end-to-end.

NFR-02: `pip install physlink` completes < 60 seconds on Google Colab.

NFR-03: Adaptation loop on 7-DOF arm (10k steps) < 45 minutes on Tesla T4 GPU.

NFR-04: VRAM footprint < 8 GB on T4 (no OOM on quickstart scenario).

NFR-05: `compliance_report()` on 1000 trajectories < 30 seconds (two thresholds: CPU-only CI + T4 GPU).

NFR-06: Triptych render < 10 seconds.

NFR-07: `report.plot()` renders inline in Colab < 5 seconds.

NFR-08: `physlink.core` backend-agnostic — no PyTorch primitives in public type signatures. Enforced by AST test at every commit.

NFR-09: All Colab cells idempotent — safe to re-run without side effects.

NFR-10: Checkpoint recovery works on Colab session disconnect — adaptation survives short disconnection via latest checkpoint.

NFR-11: API stability — deprecation cycle documented from v0.1. Public surface (`physlink.__init__` exports) stable across minor versions.

NFR-12: `physlink.doctor()` output readable without color — uses [OK]/[WARN]/[FAIL] text labels.

NFR-13: Compliance check deterministic — same data produces same result across runs.

### Additional Requirements

- AR-01: Package scaffold using `src/physlink/` layout with `pyproject.toml` (python -m build, PyPA). No package at root to prevent accidental repo-import.

- AR-02: Linting with `ruff --fix` pre-commit (autofix silently). Blocking in CI from v0.2.0. `mypy --strict` on `src/physlink/core/` only; `ignore_missing_imports` on `adapters/` (PyTorch stubs incomplete).

- AR-03: Two CI GitHub Actions jobs: `test-cpu` (gate all PRs, zero GPU) and `test-gpu` (gate releases, Colab T4 maintainer v0.1 / RC community v0.2+, automated after first external contributor merged).

- AR-04: PyPI publication via OIDC Trusted Publisher (`pypa/gh-action-pypi-publish`). Zero credentials to manage, zero expiration.

- AR-05: Checkpoint format: safetensors with embedded JSON metadata (`physlink_version`, `adapter_class`, `timestamp`, `checkpoint_step`). No pickle. `CheckpointVersionError` reads metadata before loading weights.

- AR-06: Exception hierarchy — `PhysLinkError` > `ConfigurationError` / `ValidationError` / `AdapterError` (I/O scope only) and `CheckpointError` > `CheckpointCorruptError` / `CheckpointVersionError(checkpoint_version, current_version)`. All messages use Got/Expected/Fix template.

- AR-07: `TrajectoryBatch` in `core/_types.py`. `fit()` accepts `list[dict] | TrajectoryBatch` with silent conversion. Constructors `from_list()` + `from_numpy()` in v0.2.

- AR-08: `test_core_no_torch_import.py` (AST walk on `core/**/*.py`), `test_core_boundary.py` (no `core/` → `adapters/` imports), `test_api_stability.py`. `pytest-benchmark` with committed JSON baseline for NFR regression.

- AR-09: Documentation with MkDocs Material + `mkdocstrings[python]` + GitHub Pages. Versioning via `mike` from v0.2. Badge on README pointing to GitHub Pages.

- AR-10: `physlink.__init__` exports: `doctor`, `ObservationSpace`, `ActionSpace`, `DreamerV3Adapter`, `register_invariant`, `ComplianceReport`, `PhysLinkError`. These 7 symbols only at top level.

- AR-11: Google-style docstrings on all public functions. Args/Raises/Example sections mandatory. Type annotations with `X | Y` syntax (Python 3.10+) and `from __future__ import annotations` in `core/`.

### UX Design Requirements

UX-DR-01: GitHub README — MIT license badge, CI badge, arXiv badge (live status via shields.io). "Open in Colab" button in first viewport. Dual-path action bar: "Quick Start →" (Hugo path) + "Evaluate for your lab →" (Petra path). Both entries visible above fold on 1440px.

UX-DR-02: README — "For Domain Scientists" link visible in first viewport on 1440px. Navigates to `docs/domain-scientists.md`. (BLOCKER: README discoverability 3.2 Q1 unresolved — must be above fold for Samuel's scenario to succeed.)

UX-DR-03: `physlink.doctor()` — GO verdict displayed as a distinct callout. NO-GO verdict shows one actionable fix per failed check. CPU-only runtime → NO-GO with GPU upgrade instruction. Low VRAM (< 4 GB) → WARN with memory optimization suggestion.

UX-DR-04: `adapter.fit()` progress bar — streams step count, ETA, prediction health (OK/ANOMALY), throughput. Debug hooks panel toggleable alongside the main progress bar. Shows pipeline stage statuses.

UX-DR-05: Checkpoint UI — auto-save every N steps with printed path. On session disconnect, recovery path (checkpoint file + resume instructions) visible in cell output.

UX-DR-06: Triptych GIF — 3 synchronized panels (Imagination / Real / Difference). "Friday afternoon window" callout: elapsed time vs traditional from-scratch baseline. Export produces GIF + YAML + summary. Share panel copies notebook URL.

UX-DR-07: `CHANGELOG.md` — Keep a Changelog format (`## [X.Y.Z] - YYYY-MM-DD`). ≥ 3 dated releases at launch. Breaking changes use `⚠️ **Breaking:**` with `> **Migration:**` note. Maintained incrementally per PR (not batch-updated at release). CHANGELOG absent → hard NO-GO for Petra.

UX-DR-08: Lab Adoption Guide (`docs/lab-adoption-guide.md`) — `AdaptationJob` named-run code example, `TrajectoryBuffer.export(path)` / `.load(path)` examples, BibTeX citation block.

UX-DR-09: GitHub templates — PR template with "CHANGELOG updated" checkbox + "Tests pass" checkbox. At minimum bug + feature issue templates. `domain_extension.md` issue template strongly recommended (unblocks Samuel's community return path).

UX-DR-10: Domain Scientists landing page (`docs/domain-scientists.md`) — Philosophy section naming "physical hallucinations" explicitly. `register_invariant()` API with `mass_conservation` worked example showing fn definition, call, and PASS output. CTA button to Domain Scientist Colab notebook.

UX-DR-11: Domain Scientist Colab notebook (8 cells) — Cell 3 has prominent `⚠️ "Edit this cell"` instruction (ONLY cell Samuel edits). Cell 5 outputs `mass_conservation: PASS (violations=0/N)`. Cell 6 renders compliance histogram inline. Cell 8 "What's next?" with link to `domain_extension.md` GitHub issue template.

UX-DR-12: Error messages from `register_invariant()` must show expected fn signature `fn(trajectory: dict) -> float` in the Got/Expected/Fix format. Samuel's dignity preserved — no stack traces as the primary error output.

### FR Coverage Map

FR-01 `physlink.doctor()` → Epic 1 — Installable Package & Zero-Friction Diagnostics
FR-02 Universal Space API → Epic 2 — Universal Space API
FR-03 DreamerV3 Adapter → Epic 3 — DreamerV3 Adaptation Loop
FR-04 Triptych Visualization → Epic 3 — DreamerV3 Adaptation Loop
FR-05 `adapter.export()` + share → Epic 3 — DreamerV3 Adaptation Loop
FR-06 `register_invariant()` → Epic 4 — Physical Compliance Validation API
FR-07 `ComplianceReport` → Epic 4 — Physical Compliance Validation API
FR-08 `AdaptationConfig/Run`, `TrajectoryBuffer` → Epic 4 — Physical Compliance Validation API
AR-01–08 (foundation/tooling) → Epic 1 + 2
AR-09 MkDocs → Epic 2
AR-10/11 exports + benchmarks → Epic 1 + 2
UX-DR-01 README badges + CTA → Epic 1
UX-DR-02 README domain link (BLOCKER) → Epic 6
UX-DR-03 doctor() GO/NO-GO UI → Epic 1
UX-DR-04/05/06 Adapter UX → Epic 3
UX-DR-07/08/09 CHANGELOG + Guide + Templates → Epic 5
UX-DR-10/11 domain-scientists.md + Colab → Epic 6
UX-DR-12 error messages Samuel → Epic 4

## Epic List

### Epic 1: Installable Package & Zero-Friction Diagnostics
A researcher can `pip install physlink`, run `physlink.doctor()`, and get a Go/No-Go verdict in < 15 seconds from a blank Colab T4. The package is on PyPI, CI is running, and the README links to Colab.
**FRs covered:** FR-01
**ARs covered:** AR-01, AR-02, AR-03, AR-04, AR-06, AR-08
**UX-DRs covered:** UX-DR-01, UX-DR-03

### Epic 2: Universal Space API — Environment Configuration
A researcher can configure a 7-DOF robotic arm in < 15 lines of code with immediate type validation and `.explain()` for debugging normalization and clipping.
**FRs covered:** FR-02
**ARs covered:** AR-07, AR-08, AR-09, AR-10, AR-11

### Epic 3: DreamerV3 Adaptation Loop — Hugo's Complete Scenario
A researcher can run a DreamerV3 adaptation on their robot in < 45 min on T4, with progress bar, debug hooks, auto-checkpoint surviving Colab disconnections, and a shareable triptych GIF.
**FRs covered:** FR-03, FR-04, FR-05
**ARs covered:** AR-05
**UX-DRs covered:** UX-DR-04, UX-DR-05, UX-DR-06

### Epic 4: Physical Compliance Validation API
A domain scientist can attach physical invariant checks to their adapter and get a compliance report proving their trajectories never violate the laws of physics.
**FRs covered:** FR-06, FR-07, FR-08
**UX-DRs covered:** UX-DR-12

### Epic 5: Institutional Trust Infrastructure
A lab post-doc can complete a full institutional evaluation in < 1 working day: MIT license, active CHANGELOG, arXiv citation, Lab Adoption Guide with BibTeX, and GitHub templates for domain extension contributions.
**FRs covered:** (content-only — no code FRs)
**UX-DRs covered:** UX-DR-07, UX-DR-08, UX-DR-09

### Epic 6: Domain Scientist Onboarding — Samuel's Full Path
A domain scientist (CFD/mechanics/climate) can find the "For Domain Scientists" entry point from the README in < 10 seconds, read the philosophy naming "physical hallucinations", and validate their data on the Colab notebook to get `PASS (violations=0/N)`.
**FRs covered:** (extends FR-06/FR-07 with UX)
**UX-DRs covered:** UX-DR-02, UX-DR-10, UX-DR-11

**Dependency order:** Epic 1 → Epic 2 → Epic 3 → Epic 4 → Epic 6 (Epic 5 parallelizable with 3 or 4)

---

## Epic 1: Installable Package & Zero-Friction Diagnostics

**Goal:** A researcher can `pip install physlink`, run `physlink.doctor()`, and get a Go/No-Go verdict in < 15 seconds from a blank Colab T4. The package is on PyPI, CI is running, and the README links to Colab.

### Story 1.1: Package Scaffold and Development Toolchain

As a developer,
I want a properly structured Python package with linting and type checking configured,
So that I can develop and publish physlink with guaranteed code quality from day one.

**Acceptance Criteria:**

**Given** a fresh checkout of the repository
**When** I run `python -m build` from the project root
**Then** a wheel and sdist are produced in `dist/` without errors
**And** `import physlink` from the repository root fails (src/ layout enforced — no accidental repo-import)
**And** `ruff check src/` passes with zero warnings
**And** `mypy --strict src/physlink/core/` passes with zero type errors
**And** a pre-commit hook runs `ruff --fix` silently on staged files before commit

### Story 1.2: Exception Hierarchy Foundation

As a developer,
I want a complete exception hierarchy in core/exceptions.py with structured attributes and diagnostic messages,
So that all PhysLink errors are catchable at the right granularity with machine-readable context for programmatic recovery.

**Acceptance Criteria:**

**Given** `from physlink.core.exceptions import *` is executed
**When** I inspect the exception classes
**Then** `ConfigurationError`, `ValidationError`, `AdapterError` are direct subclasses of `PhysLinkError`
**And** `CheckpointError` is a direct subclass of `PhysLinkError` (not nested under `AdapterError`)
**And** `CheckpointCorruptError` and `CheckpointVersionError` are subclasses of `CheckpointError`
**And** `CheckpointVersionError` has attributes `checkpoint_version: str` and `current_version: str`
**And** `PhysLinkError` is exported from `physlink.__init__`

**Given** any PhysLink operation raises an error
**When** the error message is printed
**Then** the message follows the Got/Expected/Fix template: `Got: <value>\n  Expected: <description>\n  Fix: <actionable instruction>`

### Story 1.3: physlink.doctor() Diagnostic Scan

As a researcher,
I want to run physlink.doctor() and get a Go/No-Go verdict in under 15 seconds,
So that I know immediately whether my environment is ready for DreamerV3 adaptation before spending time on setup.

**Acceptance Criteria:**

**Given** a Colab T4 session with GPU enabled
**When** I run `physlink.doctor()`
**Then** all checks complete end-to-end in < 15 seconds (NFR-01)
**And** output displays a structured table with rows for: Python version, PyTorch presence, CUDA availability, VRAM, Colab session estimate
**And** each row shows `[OK]`, `[WARN]`, or `[FAIL]` as text labels (no color-only signaling — NFR-12)
**And** a GO verdict is displayed as a distinct callout block (UX-DR-03)

**Given** a CPU-only Colab runtime (no GPU)
**When** I run `physlink.doctor()`
**Then** a NO-GO verdict is displayed
**And** exactly one actionable fix is shown: a GPU upgrade instruction

**Given** a GPU runtime with less than 4 GB VRAM available
**When** I run `physlink.doctor()`
**Then** the VRAM row shows `[WARN]`
**And** one memory optimization suggestion is displayed alongside the WARN

### Story 1.4: GitHub Actions CI Pipeline

As a developer,
I want two GitHub Actions jobs (test-cpu and test-gpu) configured,
So that all PRs are validated on CPU and releases are validated on T4 GPU before publication.

**Acceptance Criteria:**

**Given** a new pull request is opened against main
**When** GitHub Actions runs
**Then** the `test-cpu` job executes automatically (zero GPU dependency)
**And** the job runs the full pytest suite and gates the PR on pass/fail
**And** `test_core_no_torch_import.py` runs: walks AST of all `core/**/*.py` files and fails if any torch import is found (NFR-08)
**And** `test_core_boundary.py` runs: verifies no `core/` module imports from `adapters/`
**And** `test_api_stability.py` runs: at this stage it verifies only the symbols that exist after Epic 1 (`doctor`, `PhysLinkError`) — the test is designed as a placeholder to be updated incrementally by each subsequent epic (Story 2.6 adds 4 symbols, Story 4.5 finalizes all 7)

**Given** a release tag is pushed
**When** GitHub Actions runs
**Then** the `test-gpu` job executes (maintainer-triggered in v0.1)
**And** `pytest-benchmark` runs against the committed JSON baseline and fails if a benchmark regresses beyond threshold
**And** the committed JSON baseline file includes a hardware annotation (`"hardware": "T4 GPU"`) so future maintainers know the baseline was not generated on A100 or other hardware

### Story 1.5: PyPI Publication via OIDC

As a maintainer,
I want to publish physlink to PyPI using OIDC Trusted Publisher without storing any credentials,
So that releases can be made securely without token rotation or secrets management overhead.

**Acceptance Criteria:**

**Given** a version tag is pushed and the CI release workflow triggers
**When** `pypa/gh-action-pypi-publish` runs with OIDC Trusted Publisher configuration
**Then** the package is published to PyPI without any stored API tokens or GitHub secrets
**And** zero credentials require rotation or expiration management

**Given** a blank Google Colab T4 instance
**When** I run `pip install physlink`
**Then** installation completes in < 60 seconds (NFR-02)
**And** `import physlink` succeeds
**And** `physlink.__all__` exposes at minimum `doctor` and `PhysLinkError` (the symbols available after Epic 1)
**Note:** Full 7-symbol verification (`doctor`, `ObservationSpace`, `ActionSpace`, `DreamerV3Adapter`, `register_invariant`, `ComplianceReport`, `PhysLinkError`) is deferred to Story 4.5 once all epics are complete

**Given** a release is published to PyPI
**When** the release CI workflow runs
**Then** the quickstart Colab notebook URL is tested: the notebook must reference `physlink=={released_version}` explicitly (not `pip install physlink` without a pin)
**And** a smoke test verifies that the pinned notebook cells execute without `AttributeError` or `ImportError` against the released version

### Story 1.6: README Badges and Dual-Path Action Bar

As a researcher or lab evaluator visiting the GitHub repository,
I want to see project credibility signals and a clear entry point to Colab in the first viewport,
So that I can assess the project and start my relevant path without scrolling.

**Acceptance Criteria:**

**Given** the GitHub README is rendered on a 1440px desktop browser
**When** a researcher visits the repository page
**Then** MIT license badge, CI status badge, and arXiv badge (via shields.io live status) are all visible above the fold
**And** an "Open in Colab" button is visible in the first viewport
**And** a "Quick Start →" action bar entry is visible above fold (Hugo's path — links to quickstart Colab)
**And** an "Evaluate for your lab →" action bar entry is visible above fold simultaneously (Petra's path)
**And** if the arXiv paper has not yet been submitted, the arXiv badge shows a placeholder URL (not a broken link or 404)

**⚠️ External dependency:** arXiv submission is a hard prerequisite for Petra's evaluation path (her checklist: license → arXiv → maintenance → CHANGELOG). If arXiv is not submitted before public launch, Petra's scenario fails at step 2. This must be tracked as a launch blocker outside the codebase.

---

## Epic 2: Universal Space API — Environment Configuration

**Goal:** A researcher can configure a 7-DOF robotic arm in < 15 lines of code with immediate type validation and `.explain()` for debugging normalization and clipping.

### Story 2.1: TrajectoryBatch Core Type

As a developer,
I want a TrajectoryBatch type in core/_types.py that fit() accepts transparently,
So that downstream stories can use a stable, typed trajectory contract without introducing torch dependencies into core/.

**Acceptance Criteria:**

**Given** `from physlink.core._types import TrajectoryBatch` is executed
**When** I inspect the class
**Then** `TrajectoryBatch` has a `from_list(data: list[dict])` constructor that converts silently
**And** `fit()` accepts both `list[dict]` and `TrajectoryBatch` with silent conversion (no user-facing type error for either)
**And** no torch primitives appear in the public type signature of `TrajectoryBatch`
**And** `test_core_no_torch_import.py` passes on `core/_types.py` (AST check — no torch import)

### Story 2.2: ObservationSpace Construction and Validation

As a researcher,
I want to construct an ObservationSpace with joint count and velocity flag in one line,
So that my observation configuration is validated immediately at creation time — not silently at training time.

**Acceptance Criteria:**

**Given** I call `ObservationSpace.from_proprioception(joints=7, include_velocity=True)`
**When** the object is constructed
**Then** it succeeds without error for valid inputs
**And** the object stores the dimension count, velocity flag, and any normalization/clipping bounds

**Given** I call `ObservationSpace.from_proprioception(joints=0)` (invalid — zero joints)
**When** the object is constructed
**Then** a `ValidationError` is raised immediately (not deferred to fit())
**And** the error message follows the Got/Expected/Fix template with the invalid value shown

**Given** I call `ObservationSpace.from_proprioception(joints="seven")` (wrong type)
**When** the object is constructed
**Then** a `ValidationError` is raised immediately
**And** the error message shows Got/Expected/Fix with the actual type received

### Story 2.3: ActionSpace Construction and Validation

As a researcher,
I want to construct an ActionSpace with dimension count and bounds in one call,
So that my action configuration is validated at creation with dimension/bound consistency enforced before any training starts.

**Acceptance Criteria:**

**Given** I call `ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)`
**When** the object is constructed
**Then** it succeeds without error
**And** the object stores dims, bounds, and any clipping metadata

**Given** I call `ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 3)` (bounds length mismatch)
**When** the object is constructed
**Then** a `ValidationError` is raised immediately
**And** the error message follows Got/Expected/Fix: Got 3 bounds, Expected 7 (matching dims), Fix: provide one (min, max) tuple per dimension

**Given** I call `ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)` and then again in the same Colab cell
**When** the cell is re-run
**Then** the same object is constructed without side effects (NFR-09 — idempotent)

### Story 2.4: Space .explain() Introspection

As a researcher debugging normalization or clipping behavior,
I want to call .explain() on any Space object and receive a structured metadata dict,
So that I can verify my configuration without reading source code or guessing at defaults.

**Acceptance Criteria:**

**Given** an `ObservationSpace` constructed with `from_proprioception(joints=7, include_velocity=True)`
**When** I call `obs_space.explain()`
**Then** the return value is a `dict` (not a string, not None)
**And** the dict contains keys describing: dimension count, velocity inclusion, normalization details, clipping bounds (or None if not set)

**Given** an `ActionSpace` constructed with `continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)`
**When** I call `act_space.explain()`
**Then** the return value is a `dict` with keys describing: dims, bounds per dimension, clipping behavior
**And** the dict is JSON-serializable (no torch tensors or non-serializable objects)

### Story 2.5: MkDocs Documentation Site

As a researcher evaluating PhysLink,
I want to browse API documentation on GitHub Pages with versioned docs,
So that I can find accurate reference documentation for the version I installed.

**Acceptance Criteria:**

**Given** the repository is set up with MkDocs Material + mkdocstrings[python]
**When** `mkdocs build` is run in CI
**Then** the documentation site builds without errors
**And** `ObservationSpace`, `ActionSpace`, `doctor`, and all 7 `physlink.__init__` exports appear in the API reference
**And** a GitHub Pages deployment action publishes the docs on merge to main
**And** the README badge links to the GitHub Pages URL

### Story 2.6: Google-Style Docstrings and Public API Finalization

As a developer or contributor,
I want all public functions to have Google-style docstrings with Args, Raises, and Example sections,
So that the API reference is complete and all 7 public symbols are importable from physlink directly.

**Acceptance Criteria:**

**Given** all public functions in `physlink.core/` and `physlink.utils/`
**When** I inspect their docstrings
**Then** every public function has a Google-style docstring with Args, Raises (if applicable), and Example sections
**And** all type annotations use `X | Y` syntax (Python 3.10+) with `from __future__ import annotations` in core/

**Given** `import physlink` after Epic 2 is complete
**When** I access `physlink.__all__`
**Then** it contains at minimum: `doctor`, `ObservationSpace`, `ActionSpace`, `PhysLinkError`
**And** `test_api_stability.py` verifies these 4 symbols exist and no unintended symbols are exported yet
**And** the test is designed to be updated incrementally as each epic adds its symbols (DreamerV3Adapter in Epic 3, register_invariant + ComplianceReport in Epic 4)

**Given** `physlink` reaches v0.1 and a public function behavior needs to change in a future minor version
**When** a deprecation is introduced
**Then** a `DeprecationWarning` is emitted for at least one minor version before removal
**And** the CHANGELOG entry for that version documents the deprecation timeline explicitly (NFR-11)

---

## Epic 3: DreamerV3 Adaptation Loop — Hugo's Complete Scenario

**Goal:** A researcher can run a DreamerV3 adaptation on their robot in < 45 min on T4, with progress bar, debug hooks, auto-checkpoint surviving Colab disconnections, and a shareable triptych GIF.

### Story 3.1: DreamerV3Adapter Construction

As a researcher,
I want to instantiate DreamerV3Adapter with my configured ObservationSpace and ActionSpace,
So that the adapter validates compatibility between my spaces and the DreamerV3 model before any training begins.

**Acceptance Criteria:**

**Given** valid `ObservationSpace` and `ActionSpace` objects from Epic 2
**When** I call `DreamerV3Adapter(obs_space, act_space)`
**Then** the adapter is constructed without error
**And** no training or model loading occurs at construction time (construction is cheap)

**Given** an `ObservationSpace` with incompatible dimensions for DreamerV3
**When** I call `DreamerV3Adapter(obs_space, act_space)`
**Then** a `ConfigurationError` is raised immediately
**And** the error message follows Got/Expected/Fix with the incompatible dimension values

**Given** `DreamerV3Adapter` is imported
**When** I inspect `physlink.__init__`
**Then** `DreamerV3Adapter` is one of the 7 exported symbols (no direct adapter submodule import needed)

### Story 3.2: Adaptation Loop with Progress Bar

As a researcher,
I want adapter.fit() to run the DreamerV3 adaptation loop on a T4 and display a live progress bar,
So that I can monitor step count, ETA, prediction health, and throughput during a 10k-step adaptation run.

**Acceptance Criteria:**

**Given** a `DreamerV3Adapter` with valid spaces and a trajectory dataset
**When** I call `adapter.fit(trajectories, steps=10000, checkpoint_interval_steps=1000)`
**Then** a live progress bar streams to Colab output showing: step count, ETA, prediction health (OK or ANOMALY), throughput (steps/sec)
**And** the displayed ETA is within 30% of the actual remaining time (no systematically misleading estimates)
**And** the adaptation loop completes 10k steps in < 45 minutes on a T4 GPU (NFR-03)
**And** VRAM usage stays below 8 GB throughout (NFR-04)

**Given** `fit()` is called and then re-called in the same Colab cell (cell re-run)
**When** the adaptation starts again
**Then** no side effects from the previous run corrupt the new run (NFR-09 — idempotent)

**Given** `fit()` accepts `list[dict]` trajectory input
**When** called with either `list[dict]` or `TrajectoryBatch`
**Then** both are accepted with silent conversion (AR-07)

### Story 3.3: Debug Hooks Panel

As a researcher investigating prediction quality issues,
I want to toggle a debug hooks panel alongside the progress bar,
So that I can see pipeline stage statuses without interrupting the adaptation loop.

**Acceptance Criteria:**

**Given** I call `adapter.fit(trajectories, steps=10000, checkpoint_interval_steps=1000, debug_hooks=True)`
**When** the adaptation starts
**Then** the debug hooks panel is shown alongside the progress bar (toggle mechanism: `debug_hooks=True` parameter on `fit()`)
**And** it shows pipeline stage statuses for at minimum: data loading, world model update, actor update, critic update
**And** each stage shows OK or a diagnostic status (not raw stack traces)
**And** the main progress bar (step count, ETA, health, throughput) continues to stream alongside the panel

**Given** `adapter.fit()` is called without `debug_hooks=True` (default is False)
**When** the adaptation runs
**Then** no debug panel is shown (opt-in, not default)
**And** the progress bar is unaffected by the absence of hooks

### Story 3.4: Safetensors Checkpoint Auto-Save and Recovery

As a researcher running a long adaptation on Colab,
I want checkpoints saved automatically every N steps with the path printed to cell output,
So that if the Colab session disconnects I can resume from the latest checkpoint without losing my progress.

**Acceptance Criteria:**

**Given** `adapter.fit(trajectories, steps=10000, checkpoint_interval_steps=1000)` is running
**When** step 1000 is reached
**Then** a checkpoint file is written at the printed path in safetensors format (no pickle)
**And** the checkpoint filename includes the step number (e.g., `checkpoint_step_1000.safetensors`)
**And** the safetensors metadata contains: `physlink_version`, `adapter_class`, `timestamp`, `checkpoint_step`
**And** the checkpoint path is printed to Colab cell output (visible in output even after session restore)

**Given** a checkpoint file written by a previous adaptation run
**When** I load it with a `DreamerV3Adapter`
**Then** `CheckpointVersionError` is raised (before loading weights) if `physlink_version` in metadata is incompatible
**And** `CheckpointVersionError` carries attributes `checkpoint_version` and `current_version` for programmatic handling
**And** `CheckpointCorruptError` is raised if the safetensors file is malformed or metadata is missing

**Given** a Colab session disconnects mid-adaptation and the user resumes
**When** they load the latest checkpoint and call `fit()` again from that step
**Then** adaptation continues correctly from the checkpoint step (NFR-10)

**Given** a checkpoint was written by physlink v0.1.0 and loaded with physlink v0.1.1 (which added new metadata keys)
**When** the checkpoint is loaded
**Then** unknown metadata keys from the newer version are ignored silently (forward-compatible loading)
**And** `CheckpointVersionError` is raised ONLY when the `physlink_version` in metadata is genuinely incompatible (breaking change), not merely because metadata has extra keys

### Story 3.5: Triptych GIF Visualization

As a researcher who just completed an adaptation,
I want to call adapter.visualize(trajectories) and receive a 3-panel GIF,
So that I can visually compare Imagination vs Real vs Difference and share a "Friday afternoon window" summary with my team.

**Acceptance Criteria:**

**Given** a `DreamerV3Adapter` that has completed `fit()`
**When** I call `adapter.visualize(trajectories)`
**Then** a GIF is produced with exactly 3 synchronized panels: Imagination, Real, Difference
**And** the GIF is produced in < 10 seconds (NFR-06)
**And** a "Friday afternoon window" callout is displayed showing: elapsed adaptation time vs traditional from-scratch baseline
**And** the from-scratch baseline is a documented reference value per task type (e.g., "72h for 7-DOF arm from random init"), stored in the codebase and not silently hardcoded without documentation

**Given** `adapter.visualize()` is called
**When** the GIF is generated
**Then** `compliance_report()` is NOT called or triggered in any way (FR-04 — triptych and compliance are never coupled in the same code path)

**Given** `adapter.visualize()` is called in a Colab cell and then the cell is re-run
**When** it runs again
**Then** a new GIF is produced without corrupting or depending on prior state (NFR-09)

### Story 3.6: Export and Share Panel

As a researcher who validated their adaptation with a triptych,
I want to call adapter.export(path) and get a complete artifact bundle with a shareable Colab URL,
So that I can send my results to collaborators or archive them reproducibly.

**Acceptance Criteria:**

**Given** a `DreamerV3Adapter` after `fit()` and `visualize()` have been called
**When** I call `adapter.export(path="./physlink_export/")`
**Then** the directory at `path` contains: a GIF file, a YAML config file, a summary file
**And** the YAML config is valid YAML containing: space config (obs/act dimensions and bounds), checkpoint path

**Given** `adapter.export()` completes
**When** I inspect the YAML file
**Then** it is parseable by PyYAML without errors
**And** it contains at minimum: `obs_space`, `act_space`, and `checkpoint_path` keys

**Given** the export is complete in a Colab environment
**When** I trigger the share panel
**Then** the current notebook URL is copied to the clipboard (UX-DR-06)

**Given** the share panel is triggered outside a Colab environment (e.g., local Jupyter or script)
**When** it executes
**Then** a message is printed stating the URL cannot be copied automatically outside Colab (no silent failure or exception)

---

## Epic 4: Physical Compliance Validation API

**Goal:** A domain scientist can attach physical invariant checks to their adapter and get a compliance report proving their trajectories never violate the laws of physics.

### Story 4.1: AdaptationConfig and AdaptationRun

As a researcher running named adaptation experiments,
I want an immutable AdaptationConfig and a stateful AdaptationRun to separate configuration from execution state,
So that I can version my configuration in YAML/JSON and track run state without mixing the two concerns.

**Acceptance Criteria:**

**Given** I construct an `AdaptationConfig` with valid parameters (obs_space, act_space, steps, checkpoint_interval)
**When** I attempt to mutate a field after construction
**Then** a `TypeError` or `AttributeError` is raised (config is immutable)

**Given** an `AdaptationConfig` object
**When** I serialize it to YAML and reload it
**Then** the deserialized config is equal to the original (round-trip stable, no torch objects in serialized form)

**Given** an `AdaptationRun` is created from an `AdaptationConfig`
**When** the run progresses through steps
**Then** the run object tracks stateful data (step count, checkpoint paths, run metadata) separately from the immutable config
**And** the config within the run remains unchanged

### Story 4.2: TrajectoryBuffer Export and Load

As a researcher managing trajectory datasets across Colab sessions,
I want TrajectoryBuffer.export(path) and .load(path) to persist my trajectory data reliably,
So that I can save a session's collected trajectories and reload them in a future Colab session without data loss.

**Acceptance Criteria:**

**Given** a `TrajectoryBuffer` populated with trajectory data
**When** I call `TrajectoryBuffer.export(path="./trajectories.pkl")` (or appropriate format)
**Then** a file is written at the specified path containing all trajectory data
**And** the export does not modify the buffer's in-memory state

**Given** an exported `TrajectoryBuffer` file on disk
**When** I call `TrajectoryBuffer.load(path="./trajectories.pkl")`
**Then** the loaded buffer contains the same trajectories as the original (round-trip fidelity)
**And** the loaded buffer is immediately usable as input to `adapter.fit()`

**Given** a `TrajectoryBuffer` export/load cycle is run in a fresh Colab cell
**When** the cell is re-run
**Then** the same result is produced without side effects (NFR-09)

### Story 4.3: register_invariant() API

As a domain scientist (CFD, mechanics, climate),
I want to attach a physical invariant check to my adapter using a plain Python callable,
So that I can encode my domain knowledge without learning any PhysLink abstractions or subclassing anything.

**Acceptance Criteria:**

**Given** I define a plain Python function `def mass_conservation(trajectory: dict) -> float: ...`
**When** I call `register_invariant(adapter, name="mass_conservation", fn=mass_conservation, tolerance=0.01, mode="hard")`
**Then** the invariant is attached to the adapter without error
**And** no subclassing, decorators, or inheritance is required

**Given** `mode="hard"` is set
**When** `adapter.fit()` processes a trajectory where `fn(trajectory) > tolerance`
**Then** that trajectory is rejected from the training batch
**And** a diagnostic message is logged (not a raw stack trace)

**Given** `mode="soft"` is set
**When** `adapter.fit()` processes a trajectory where `fn(trajectory) > tolerance`
**Then** the trajectory is included but its residual penalizes the loss function

**Given** I pass a function with the wrong signature (e.g., `def check_pressure(pressure, volume) -> bool`)
**When** `register_invariant()` is called
**Then** a `ValidationError` is raised immediately (not deferred to fit())
**And** the error message shows the function name and parameters in human-readable form: `Got: check_pressure(pressure, volume) -> bool` (not a memory address repr)
**And** the message shows: Expected `fn(trajectory: dict) -> float`, Fix: a correction instruction (UX-DR-12 — no stack trace as primary output)

**Given** I call `register_invariant(..., mode="medium")` (invalid mode value)
**When** `register_invariant()` is called
**Then** a `ConfigurationError` is raised immediately
**And** the error message follows Got/Expected/Fix: Got `"medium"`, Expected one of `["hard", "soft"]`, Fix: use `mode="hard"` to reject violations or `mode="soft"` to penalize them

### Story 4.4: ComplianceReport Summary and Violations

As a domain scientist who ran an adaptation with invariant checks,
I want adapter.compliance_report() to return a pure data object with human-readable summary and violation details,
So that I can verify my trajectories never violated physics without parsing raw logs.

**Acceptance Criteria:**

**Given** invariants have been registered and `adapter.fit()` has been called
**When** I call `adapter.compliance_report()`
**Then** the return value is a `ComplianceReport` pure data object (no side effects on call)
**And** `ComplianceReport` is exported from `physlink.__init__`

**Given** a `ComplianceReport` object
**When** I call `report.summary()`
**Then** the return is a string in the exact format: `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`
**And** the same data produces the same summary on repeated calls (NFR-13 — deterministic)

**Given** a `ComplianceReport` with at least one violation
**When** I call `report.violations()`
**Then** the return is a list where each entry contains: trajectory index, field values, residual value, and a "Possible cause:" text string
**And** no Python stack trace appears as part of the violation output

**Given** a `ComplianceReport` with zero violations
**When** I call `report.summary()`
**Then** the string contains `violations=0/N` and `PASS`

### Story 4.5: ComplianceReport Plot and Export

As a domain scientist reviewing compliance results,
I want report.plot() to render a histogram inline in Colab and report.export() to save a JSON file,
So that I have both a visual proof and a machine-readable record of my invariant validation.

**Acceptance Criteria:**

**Given** a `ComplianceReport` object in a Colab environment
**When** I call `report.plot(title="Mass Conservation Check", show_threshold=True)`
**Then** a matplotlib histogram is rendered inline in the Colab output in < 5 seconds (NFR-07)
**And** a vertical threshold line is drawn and clearly labeled on the histogram
**And** the same plot is produced on repeated calls (NFR-13 — deterministic)

**Given** a `ComplianceReport` object
**When** I call `report.export(path="./compliance_report.json")`
**Then** a valid JSON file is written at the specified path
**And** the JSON contains at minimum: invariant name, PASS/FAIL status, max_residual, threshold, violation count, and violation details
**And** the file is parseable by Python's `json.load()` without errors

**Given** `compliance_report()` is called on 1000 trajectories in a CPU-only environment
**When** the report is generated
**Then** it completes in < 30 seconds (NFR-05)

**Given** Epic 4 is complete and all 7 public symbols are implemented
**When** I access `physlink.__all__`
**Then** it contains exactly and only: `doctor`, `ObservationSpace`, `ActionSpace`, `DreamerV3Adapter`, `register_invariant`, `ComplianceReport`, `PhysLinkError`
**And** `test_api_stability.py` is updated to verify the full 7-symbol list (final API stability gate)

---

## Epic 5: Institutional Trust Infrastructure

**Goal:** A lab post-doc can complete a full institutional evaluation in < 1 working day: MIT license, active CHANGELOG, arXiv citation, Lab Adoption Guide with BibTeX, and GitHub templates for domain extension contributions.

### Story 5.1: CHANGELOG with Three Dated Releases

As a lab post-doc evaluating PhysLink for institutional adoption,
I want to find a CHANGELOG.md maintained in Keep a Changelog format with at least 3 dated releases,
So that I can assess project maturity and process discipline — a CHANGELOG absent is a hard NO-GO for my evaluation.

**Acceptance Criteria:**

**Given** the repository root contains a `CHANGELOG.md`
**When** I open the file
**Then** it follows Keep a Changelog format: each release section uses `## [X.Y.Z] - YYYY-MM-DD`
**And** at least 3 dated release entries exist at launch
**And** each release entry contains at minimum: a summary of the main change, a change type label (Added / Changed / Deprecated / Removed / Fixed / Security), and a migration path for any breaking changes
**And** breaking changes are marked with `⚠️ **Breaking:**` followed by a `> **Migration:**` note block

**Given** a PR is opened that changes public API behavior
**When** the PR is reviewed
**Then** the PR template "CHANGELOG updated" checkbox must be checked before merging (enforced by PR template — Story 5.3)
**And** CHANGELOG is updated incrementally with that PR (not batch-updated at release time)

**Given** `CHANGELOG.md` is absent from the repository
**When** Petra evaluates the project
**Then** this constitutes a hard NO-GO for institutional adoption (UX-DR-07 requirement)

### Story 5.2: Lab Adoption Guide

As a lab post-doc setting up PhysLink for multiple researchers,
I want a Lab Adoption Guide at docs/lab-adoption-guide.md with named-run examples, buffer persistence, and a BibTeX citation block,
So that I can onboard my team and properly cite the work in our papers.

**Acceptance Criteria:**

**Given** the file `docs/lab-adoption-guide.md` exists in the repository
**When** I read it
**Then** it contains a named-run code example using `AdaptationConfig` and `AdaptationRun` (the types implemented in Story 4.1 — not a fictional `AdaptationJob` type)
**And** the code example is copy-pasteable and runs without `NameError` or `ImportError`
**And** it contains `TrajectoryBuffer.export(path)` and `TrajectoryBuffer.load(path)` working examples with copy-pasteable code
**And** it contains a BibTeX citation block with correct metadata (title, authors, year, URL)
**And** it contains a link to the published pytest-benchmark results (or a CI badge showing the latest GPU benchmark run) so Petra can verify performance claims without running the GPU test herself

**Given** the Lab Adoption Guide is linked from the README
**When** a researcher clicks "Evaluate for your lab →" from the README action bar
**Then** they reach this guide (or a page that links directly to it)

### Story 5.3: GitHub PR and Issue Templates

As a contributor or domain scientist wanting to extend PhysLink,
I want GitHub PR and issue templates that guide me through the contribution process,
So that I can submit a domain extension without missing required steps like CHANGELOG updates.

**Acceptance Criteria:**

**Given** the repository contains `.github/PULL_REQUEST_TEMPLATE.md`
**When** a contributor opens a PR
**Then** the PR body is pre-filled with a template containing: a "CHANGELOG updated" checkbox and a "Tests pass" checkbox
**And** these checkboxes are advisory (honor system) in v0.1 — a CI check enforcing CHANGELOG updates is a v0.2 follow-up, not a blocker for this story

**Given** the repository contains `.github/ISSUE_TEMPLATE/` directory
**When** a contributor opens a new issue
**Then** at minimum two templates are available: a bug report template and a feature request template

**Given** the repository contains `.github/ISSUE_TEMPLATE/domain_extension.md`
**When** a domain scientist (Samuel's community return path) opens a domain extension issue
**Then** the template guides them through describing their physical domain, invariant function, and expected PASS output
**And** this template is listed as an option on the GitHub "New Issue" page

---

## Epic 6: Domain Scientist Onboarding — Samuel's Full Path

**Goal:** A domain scientist (CFD/mechanics/climate) can find the "For Domain Scientists" entry point from the README in < 10 seconds, read the philosophy naming "physical hallucinations", and validate their data on the Colab notebook to get `PASS (violations=0/N)`.

### Story 6.1: README "For Domain Scientists" Link

As a domain scientist (CFD, mechanics, climate) discovering PhysLink via arXiv or a colleague,
I want to find a "For Domain Scientists" link in the README within 10 seconds of landing,
So that I reach the relevant documentation without having to parse a README written for ML researchers.

**⚠️ BLOCKER:** This story depends on resolving design question 3.2 Q1 (README discoverability). If `readme-links-domain-scientists-link` is below fold on 1440px, Samuel's entire scenario fails at this step. The link placement decision must have a named owner and a resolution deadline before development begins — this story cannot be marked "done" until the design decision is recorded. As a fallback minimum, a "For Domain Scientists" link must appear somewhere in the README even if the above-fold placement is unresolved.

**Acceptance Criteria:**

**Given** the GitHub README is rendered on a 1440px desktop browser
**When** Samuel (a domain scientist, not an ML researcher) visits the repository
**Then** a "For Domain Scientists" link is visible in the first viewport without scrolling
**And** clicking it navigates to `docs/domain-scientists.md`

**Given** Samuel spends 10 seconds on the README page
**When** he scans without scrolling
**Then** the "For Domain Scientists" link is findable within that time (above-fold placement enforced)

### Story 6.2: Domain Scientists Landing Page

As a domain scientist worried that ML tools will ignore the laws of physics,
I want to read a documentation page that names "physical hallucinations" explicitly and shows me how to register my own invariant check,
So that I understand PhysLink respects domain knowledge and I can validate my own data.

**Acceptance Criteria:**

**Given** I navigate to `docs/domain-scientists.md`
**When** I read the Philosophy section
**Then** the term "physical hallucinations" appears explicitly by name (UX-DR-10 — not paraphrased)
**And** the section explains why physics-blind ML models hallucinate physically impossible trajectories

**Given** I continue reading the page
**When** I reach the API section
**Then** a complete `mass_conservation` worked example is shown: the function definition, the `register_invariant()` call, and the `PASS` output in the exact format `"mass_conservation: PASS (max_residual=X, threshold=Y, violations=0/N)"`
**And** the example is explicitly labeled as illustrative — a note states that any physical domain works (CFD: energy conservation, robotics: momentum conservation, climate: mass conservation) with the same pattern

**Given** I finish reading the page
**When** I look for next steps
**Then** a CTA button or prominent link points to the Domain Scientist Colab notebook (Story 6.3)

### Story 6.3: Domain Scientist Colab Notebook (8 Cells)

As a domain scientist who has read the landing page,
I want an 8-cell Colab notebook where I only need to edit one cell to validate my own trajectory data,
So that I get a PASS or FAIL result without needing to understand the DreamerV3 internals.

**Acceptance Criteria:**

**Given** I open the Domain Scientist Colab notebook
**When** Cell 1 (`pip install physlink`) executes
**Then** if installation fails (e.g., version not yet on PyPI), a clear error message is shown: "physlink could not be installed — check the version number or PyPI availability" (no silent cascade of ModuleNotFoundError in later cells)

**Given** Cell 1 installs successfully and I read Cell 3
**When** I open the notebook for the first time
**Then** a prominent `⚠️ "Edit this cell"` instruction is visible (the ONLY cell Samuel edits)
**And** the cell contains an example trajectory variable that I replace with my own data
**And** no other cell contains an instruction to edit it

**Given** I have replaced Cell 3's example data with my CFD trajectories and run all cells in order
**When** Cell 5 executes
**Then** the output displays `mass_conservation: PASS (violations=0/N)` (Samuel's moment of truth — UX-DR-11)
**And** the PASS format matches exactly: `"name: PASS (max_residual=X, threshold=Y, violations=Z/N)"`

**Given** Cell 6 executes
**When** the compliance histogram renders
**Then** the matplotlib histogram appears inline in the Colab output with the threshold line labeled
**And** rendering completes in < 5 seconds (NFR-07)

**Given** I reach Cell 8 ("What's next?")
**When** I read the cell output
**Then** a link to the `domain_extension.md` GitHub issue template is prominently shown (Samuel's community return path — UX-DR-11)
**And** the link is clickable and navigates to the correct GitHub issue template

**Given** any cell in the notebook is re-run
**When** it executes again
**Then** no side effects from the previous run corrupt the result (NFR-09 — all cells idempotent)
