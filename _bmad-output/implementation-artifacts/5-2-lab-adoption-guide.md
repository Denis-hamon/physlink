# Story 5.2: Lab Adoption Guide

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a lab post-doc setting up PhysLink for multiple researchers,
I want a Lab Adoption Guide at docs/lab-adoption-guide.md with named-run examples, buffer persistence, and a BibTeX citation block,
so that I can onboard my team and properly cite the work in our papers.

## Acceptance Criteria

1. **Given** the file `docs/lab-adoption-guide.md` exists in the repository
   **When** I read it
   **Then** it contains a named-run code example using `AdaptationConfig` and `AdaptationRun` (the types implemented in Story 4.1 — not a fictional `AdaptationJob` type)
   **And** the code example is copy-pasteable and runs without `NameError` or `ImportError`
   **And** it contains `TrajectoryBuffer.export(path)` and `TrajectoryBuffer.load(path)` working examples with copy-pasteable code
   **And** it contains a BibTeX citation block with correct metadata (title, authors, year, URL)
   **And** it contains a link to the published pytest-benchmark results (or a CI badge showing the latest GPU benchmark run) so Petra can verify performance claims without running the GPU test herself

2. **Given** the Lab Adoption Guide is linked from the README
   **When** a researcher clicks "Evaluate for your lab →" from the README action bar
   **Then** they reach this guide (or a page that links directly to it)

## Tasks / Subtasks

- [x] Task 1: Replace stale content in `docs/lab-adoption-guide.md` with the complete guide (AC: #1)
  - [x] Add introduction section (Petra's evaluation path, what this guide covers)
  - [x] Add prerequisites section (`pip install physlink`, version 0.1.2+)
  - [x] Add "Named Adaptation Run" section with `AdaptationConfig` + `AdaptationRun` copy-pasteable example
  - [x] Add "Trajectory Persistence" section with `TrajectoryBuffer.export(path)` / `.load(path)` copy-pasteable example
  - [x] Add "Citing PhysLink" section with BibTeX block (title, authors, year, URL using `YOUR-ORG/physlink` placeholder)
  - [x] Add "Performance Claims" section with link to `tests/perf/baselines/benchmark_baseline.json` AND shields.io CI badge reference

- [x] Task 2: Verify AC #2 — README link already routes to this guide (AC: #2)
  - [x] Confirm `README.md` line 13: `"Evaluate for your lab →"` already links to `docs/lab-adoption-guide.md`
  - [x] No README change required — link is already in place

- [x] Task 3: Add integration tests validating guide content (AC: #1)
  - [x] Create `tests/integration/test_lab_adoption_guide.py`
  - [x] Test: file exists at `docs/lab-adoption-guide.md`
  - [x] Test: guide contains `AdaptationConfig` (not `AdaptationJob`) in code blocks
  - [x] Test: guide contains `AdaptationRun` in code blocks
  - [x] Test: guide contains `TrajectoryBuffer.export` and `TrajectoryBuffer.load`
  - [x] Test: guide contains a `@software` or `@misc` BibTeX entry
  - [x] Test: guide contains a benchmark performance link or badge reference

## Dev Notes

### THIS IS AN UPDATE STORY — docs/lab-adoption-guide.md Already Exists

`docs/lab-adoption-guide.md` already exists but contains stale placeholder content from the pre-Epic-4 era (evaluation checklist referencing `register_invariant` as "coming after Epic 4"). **Read the current file first, then replace it entirely** with the new comprehensive guide. Do NOT treat it as a new file.

Do NOT create:
- Python source files or tests outside `tests/integration/`
- Changes to `README.md` (link already exists at line 13)
- Changes to `mkdocs.yml` (already has `Lab Adoption Guide: lab-adoption-guide.md` in nav)

### Critical Type Naming Warning — AdaptationConfig/Run, NOT AdaptationJob

UX-DR-08 mentions `AdaptationJob` by name, but this type was **split** during architecture design (see architecture.md). The actual implementation (Story 4.1) uses two separate types:

- **`AdaptationConfig`** — `@dataclass(frozen=True)`, immutable, YAML-serializable
- **`AdaptationRun`** — `@dataclass`, stateful, returned by `adapter.fit()`

The AC explicitly forbids `AdaptationJob`: "not a fictional `AdaptationJob` type". Any code example using `AdaptationJob` will cause `ImportError` — this is the primary disaster risk for this story.

### Exact Import Path — Not in physlink.__all__

`AdaptationConfig`, `AdaptationRun`, and `TrajectoryBuffer` are NOT in `physlink.__all__` (only the 7 public symbols are: doctor, ObservationSpace, ActionSpace, DreamerV3Adapter, register_invariant, ComplianceReport, PhysLinkError). They are in `physlink.core._types`:

```python
from physlink import ObservationSpace, ActionSpace, DreamerV3Adapter
from physlink.core._types import AdaptationConfig, AdaptationRun, TrajectoryBuffer
```

If the code examples use `from physlink import AdaptationConfig`, that is an `ImportError` — tests will catch this.

### Verified API Surface (read from src/physlink/core/_types.py)

**AdaptationConfig** — `@dataclass(frozen=True)`:
```python
AdaptationConfig(
    obs_space: ObservationSpace,
    act_space: ActionSpace,
    steps: int,
    checkpoint_interval_steps: int = 1000,        # default
    checkpoint_dir: str = "physlink_checkpoints",  # default
)
# Serialization methods: .to_dict(), .from_dict(d), .to_yaml(path), .from_yaml(path)
```

**AdaptationRun** — `@dataclass` (mutable):
```python
# Returned by adapter.fit()
run.config           # AdaptationConfig — the config that produced this run
run.current_step     # int — steps completed
run.checkpoint_paths # list[str] — paths to saved checkpoint files
run.started_at       # str — ISO-format UTC timestamp
run.elapsed_seconds  # float — wall-clock seconds
```

**TrajectoryBuffer** — `@dataclass`:
```python
TrajectoryBuffer(data=[{"obs": ..., "action": ...}, ...])  # constructor
buffer.export(path="./trajectories.pkl")                    # pickle to disk
TrajectoryBuffer.load(path="./trajectories.pkl")            # classmethod
buffer.to_batch()   # -> TrajectoryBatch, usable directly in adapter.fit()
len(buffer)         # number of trajectories
```

**fit() signature** (returns AdaptationRun):
```python
adapter.fit(
    trajectories,                    # list[dict] | TrajectoryBatch
    steps=config.steps,
    checkpoint_interval_steps=config.checkpoint_interval_steps,
) -> AdaptationRun
```

### Copy-Pasteable Code Examples for the Guide

**Named Adaptation Run (Task 1, AC #1 first bullet):**
```python
from physlink import ObservationSpace, ActionSpace, DreamerV3Adapter
from physlink.core._types import AdaptationConfig, AdaptationRun

# 1. Configure spaces for a 7-DOF arm
obs_space = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
act_space = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)

# 2. Define a named, reproducible configuration
config = AdaptationConfig(
    obs_space=obs_space,
    act_space=act_space,
    steps=10_000,
    checkpoint_interval_steps=1000,
    checkpoint_dir="./lab_checkpoints",
)

# Optionally persist the config for reproducibility
config.to_yaml("./lab_config.yaml")

# 3. Run adaptation — fit() returns a tracked AdaptationRun
adapter = DreamerV3Adapter(config.obs_space, config.act_space)
run: AdaptationRun = adapter.fit(
    trajectories,
    steps=config.steps,
    checkpoint_interval_steps=config.checkpoint_interval_steps,
)

# 4. Inspect run metadata
print(f"Completed {run.current_step} steps in {run.elapsed_seconds:.1f}s")
print(f"Checkpoints: {run.checkpoint_paths}")
```

**Trajectory Persistence (Task 1, AC #1 third bullet):**
```python
from physlink.core._types import TrajectoryBuffer

# --- Session 1: collect and persist ---
# trajectories is a list[dict] from your simulation/rollout
buffer = TrajectoryBuffer(data=trajectories)
buffer.export(path="./lab_trajectories.pkl")

# --- Session 2 (new Colab runtime): reload and continue ---
buffer = TrajectoryBuffer.load(path="./lab_trajectories.pkl")
# Pass the buffer directly to fit() — it's accepted as-is
run = adapter.fit(buffer, steps=5_000)
```

### BibTeX Citation Block

Use this template (consistent with `YOUR-ORG/physlink` placeholder from README.md and CHANGELOG.md):

```bibtex
@software{physlink2026,
  title   = {{PhysLink}: Backend-Agnostic Adapter Library for Physical Simulation {ML}},
  author  = {YOUR-ORG},
  year    = {2026},
  url     = {https://github.com/YOUR-ORG/physlink},
  version = {0.1.2}
}
```

### Benchmark Performance Link

Petra cannot run the T4 GPU tests herself. Two resources to reference in the guide:

1. **Committed baseline JSON** (always present in the repo):
   `tests/perf/baselines/benchmark_baseline.json` — contains hardware annotation `"hardware": "T4 GPU"` and NFR thresholds (doctor() < 15s, compliance_report() < 30s)

2. **GitHub Actions CI badge** (shields.io, already in README):
   The `test-gpu` workflow badge shows the latest release validation run result.

Include **both** — the JSON for offline verification, the badge for live status.

### Files to Create / Modify

| File | Action | AC |
|------|--------|-----|
| `docs/lab-adoption-guide.md` | **UPDATE** (replace stale content entirely) | #1 |
| `tests/integration/test_lab_adoption_guide.py` | **CREATE** (new, following Story 5.1 pattern) | #1 |

No changes to `README.md`, `mkdocs.yml`, `pyproject.toml`, or any `src/` files.

### README Link Already Present

AC #2 is already satisfied by existing code. Verify before marking done:
```
README.md line 13: <a href="docs/lab-adoption-guide.md"><strong>Evaluate for your lab →</strong></a>
```
No README update is needed. Just confirm and tick the task.

### No Python Source Changes Required

Epic 5 is content-only. `AdaptationConfig`, `AdaptationRun`, and `TrajectoryBuffer` are already fully implemented from Epic 4. This story only produces documentation and tests that validate documentation content.

### Commit Message Pattern

Following all prior stories in the codebase:
```
docs(story-5.2): Lab Adoption Guide
```

### Previous Story Intelligence (Story 5.1)

- Story 5.1 created `tests/integration/test_changelog_content.py` with 34 integration tests despite initially claiming "No Tests Required" — this became a MEDIUM issue in the review. For 5.2, the tests are explicitly planned upfront (Task 3) to avoid this.
- Story 5.1 also discovered it had missed `src/physlink/__init__.py` and `tests/integration/test_changelog_content.py` from the File List — ensure File List is complete before marking done.
- Test baseline at end of Story 5.1: **755 passed, 3 skipped**. Story 5.2 adds integration tests for the guide (≈5–8 new tests expected).
- `ruff check src/` and `mypy --strict src/physlink/core/` must still pass — Story 5.2 does not touch Python source, zero risk.

### Project Structure Notes

- `docs/lab-adoption-guide.md` — at `docs/` (not `src/`, not root) — this is the MkDocs sources directory
- `tests/integration/test_lab_adoption_guide.py` — integration tests, not unit/ — validates documentation content by reading the file, not Python import tests
- `mkdocs.yml` already has the file in `nav:` — no nav update needed
- `docs/` is NOT the site-built output (`site/` is the built output); edit `docs/lab-adoption-guide.md`, not anything under `site/`

### References

- [Source: epics.md#Story 5.2] — Acceptance criteria, user story, AdaptationJob vs AdaptationConfig warning
- [Source: epics.md#UX-DR-08] — Lab Adoption Guide: named-run example, TrajectoryBuffer, BibTeX
- [Source: architecture.md#Category 4 — Documentation] — MkDocs Material, lab-adoption-guide.md in directory structure
- [Source: architecture.md#Complete Project Directory Structure] — `docs/lab-adoption-guide.md` listed explicitly
- [Source: src/physlink/core/_types.py] — Verified AdaptationConfig, AdaptationRun, TrajectoryBuffer API (read at story creation time)
- [Source: README.md line 13] — "Evaluate for your lab →" link already points to docs/lab-adoption-guide.md
- [Source: mkdocs.yml] — `Lab Adoption Guide: lab-adoption-guide.md` already in nav
- [Source: docs/lab-adoption-guide.md] — Current stale content (v0.1 checklist pre-Epic-4); replace entirely
- [Source: 5-1-changelog-with-three-dated-releases.md#Dev Agent Record] — Test baseline 755 passed, 3 skipped; commit pattern `docs(story-5.X)`
- [Source: architecture.md#ADR-001, point 6] — GPU CI protocol, benchmark_baseline.json hardware annotation

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Iteration 1: test `test_does_not_contain_adaptation_job` a échoué car la note d'avertissement dans
  le guide contenait le mot "AdaptationJob". Suppression de cette mention de la documentation
  publique — le message n'a de valeur que pour les développeurs, pas pour les utilisateurs finaux.
- Review (2026-05-22): 4 issues auto-fixés par le reviewer AI :
  [HIGH] `trajectories` non défini dans les blocs Python (NameError — violation AC #1) → ajout
  de `trajectories = []` placeholder dans les deux blocs concernés.
  [MEDIUM] Test redondant `test_contains_benchmark_baseline_reference` supprimé (logique OR
  couverte entièrement par les deux tests suivants).
  [MEDIUM] Compte de tests corrigé dans le Dev Agent Record : 27 tests / 9 classes (pas 11/5).
  [LOW] Ajout du heading `## Introduction` (task 1 subtask explicite).

### Completion Notes List

- **Task 1**: `docs/lab-adoption-guide.md` entièrement reécrit. Contenu précédent (checklist
  pre-Epic-4 avec `register_invariant` marqué "coming after Epic 4") remplacé par un guide complet
  en 5 sections : Introduction/Prérequis, Named Adaptation Run, Trajectory Persistence, Performance
  Claims, Citing PhysLink. Exemples de code copy-pastéables vérifiés contre l'API réelle
  (`AdaptationConfig`, `AdaptationRun`, `TrajectoryBuffer`). Import path correct :
  `from physlink.core._types import ...`.
- **Task 2**: Lien README vérifié — `"Evaluate for your lab →"` pointe déjà vers
  `docs/lab-adoption-guide.md` (ligne 13). Aucune modification requise.
- **Task 3**: `tests/integration/test_lab_adoption_guide.py` créé avec 27 tests répartis en 9
  classes. Tous les tests passent. Suite complète : 783 passés, 2 ignorés, 0 régression.

### File List

- `docs/lab-adoption-guide.md` — UPDATED (contenu stale remplacé entièrement ; `## Introduction` ajouté ; `trajectories` placeholder défini dans 2 blocs de code)
- `tests/integration/test_lab_adoption_guide.py` — CREATED (27 tests d'intégration ; test redondant `test_contains_benchmark_baseline_reference` supprimé)

## Change Log

- 2026-05-22: Story 5.2 — Lab Adoption Guide. Remplacement du contenu stale de
  `docs/lab-adoption-guide.md` (checklist pré-Epic-4) par un guide complet avec exemples
  copy-pastéables `AdaptationConfig`/`AdaptationRun`/`TrajectoryBuffer`, bloc BibTeX, et liens
  vers le baseline de benchmark. Création de `tests/integration/test_lab_adoption_guide.py`
  (27 tests). Commit: `docs(story-5.2): Lab Adoption Guide`
- 2026-05-22: Review AI — 4 issues auto-fixés : `trajectories` placeholder défini dans les
  blocs de code (HIGH — NameError AC violation), test redondant supprimé (MEDIUM), compte de
  tests corrigé (MEDIUM), heading `## Introduction` ajouté (LOW). Story → done.
