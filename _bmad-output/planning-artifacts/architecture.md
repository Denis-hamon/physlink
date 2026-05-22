---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-05-21'
inputDocuments:
  - design-artifacts/A-Product-Brief/project-brief.md
  - _bmad-output/implementation-artifacts/E-Development/001-prd-scenario-01.md
  - _bmad-output/implementation-artifacts/E-Development/000-tech-audit.md
  - _bmad-output/deliveries/DD-001-hugos-friday-afternoon-test.yaml
  - _bmad-output/deliveries/DD-002-petras-lab-standard-rollout.yaml
  - _bmad-output/deliveries/DD-003-samuels-dignity-validation.yaml
  - _bmad-output/deliveries/DD-001-handoff-log.md
  - _bmad-output/deliveries/DD-002-handoff-log.md
  - _bmad-output/deliveries/DD-003-handoff-log.md
workflowType: 'architecture'
project_name: 'PhysLink'
user_name: 'Denis'
date: '2026-05-21'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (Scenario 01 PRD — 4 FRs):**

- **FR-01:** `physlink.doctor()` — CLI + API diagnostic. Scan Go/No-Go en < 15 secondes : Python version, PyTorch presence, CUDA availability, VRAM, Colab session estimate. Implication : module `utils/diagnostics.py` isolé, aucune dépendance ML pour ce module. *Doit fonctionner sans que le World Model soit installé (Hugo quitte à la minute 20 sinon).*

- **FR-02:** Universal Space API — `ObservationSpace.from_proprioception()`, `ActionSpace.continuous()`. Pattern Factory masquant la complexité tenseur derrière des termes métier. Implication : `core/spaces.py` backend-agnostique — numpy est la lingua franca acceptable (pas torch, pas JAX). Un test statique AST (`test_core_no_torch_import.py`) vérifie cet invariant à chaque commit.

- **FR-03:** DreamerV3 Adapter — `.fit(trajectories, steps, checkpoint_interval_steps)`. Paramètre `checkpoint_interval_steps: int` (pas en secondes) pour permettre les tests unitaires rapides. Base Adapter classe abstraite dans `core/adapter.py`; implémentation concrète dans `adapters/dreamer.py`. Barre de progression async via `rich` ou `tqdm` compatible Colab.

- **FR-04:** Triptych Validation — `.visualize()` 3 GIF panels synchronisés. Séparé de `compliance_report()` — `visualize()` est dans `utils/visualization.py`, `ComplianceReport` est un objet de données pur dans `core/validation.py`. Jamais couplés dans le même chemin de code.

**Extended API Surface (DD-003):**

- `register_invariant(adapter, name, fn, tolerance, mode)` — accepte un plain Python callable, s'attache à un `DreamerV3Adapter`. mode="hard" rejette; mode="soft" pénalise. `ComplianceReport` est un objet de données pur; `report.plot()` appelle matplotlib uniquement si explicitement demandé. *Placé au niveau zéro de l'API publique (Samuel ne cherche pas dans les sous-modules).*

**Content-Only Deliverables (DD-002):**

- `AdaptationJob` → séparé en **`AdaptationConfig`** (immutable, YAML/JSON-sérialisable) + **`AdaptationRun`** (stateful, temporaire). `TrajectoryBuffer.export(path)` / `.load(path)`.

**Non-Functional Requirements:**

| NFR | Cible |
|-----|-------|
| physlink.doctor() | < 15 secondes |
| pip install physlink | < 60 secondes sur Colab |
| Adaptation loop (7-DOF 10k steps) | < 45 min sur T4 GPU |
| VRAM footprint | < 8 GB sur T4 |
| compliance_report() sur 1000 trajectoires | < 30 secondes (deux seuils : CPU-only CI + T4 GPU) |
| Triptych render | < 10 secondes |
| API stabilité | Deprecation cycle documenté dès v0.1 |

**Scale & Complexity:**

- Primary domain: Python ML infrastructure library (pip package)
- Complexity level: **Medium** — pas de DB, pas d'auth, pas de multi-tenant
- Estimated architectural components: 6 modules core + 1 adapter concret + 2 utils + CLI
- No web server, no persistent state beyond checkpoints on filesystem

### Technical Constraints & Dependencies

- **Python 3.10+** strict
- **PyTorch 2.x** — backend de l'adapter DreamerV3 uniquement; core API reste backend-agnostique
- **numpy** — lingua franca acceptable dans core (pas torch, pas JAX)
- **Google Colab T4** — runtime cible; contrainte VRAM < 8 GB, session < 12h
- **PyPI** — distribution via `pip install physlink`; pyproject.toml avec setuptools
- **Lean dependency graph** : `rich`, `matplotlib`, `numpy`, `pyyaml`, `torch` (adapter seulement)
- **GitHub Actions** — CI/CD; tests de régression sur dimensions, stabilité API, et benchmark NFR (pytest-benchmark, baseline JSON committé)

### Cross-Cutting Concerns Identified

1. **Backend-agnosticism** — `physlink.core` ne doit pas importer `torch`. Test AST statique appliqué à chaque commit pour garantir l'invariant.

2. **API stability contract** — Surface publique petite, versionnée, contractuelle. Petra juge sur la stabilité visible des namespaces. Tout internal non stable doit être dans `_private` ou `physlink._internal`. Process de review API à définir dès l'architecture.

3. **Explainability mixin** — tous les objets core (`ObservationSpace`, `ActionSpace`, `DreamerV3Adapter`) implémentent `.explain()` retournant un dict de métadonnées.

4. **Séparation config/état runtime** — `AdaptationConfig` (immutable, sérialisable) vs `AdaptationRun` (stateful). Évite un objet mutable lourd pour le checkpoint resume.

5. **Visualisation isolée de la validation** — `ComplianceReport` est un objet de données pur; `visualize()` et `report.plot()` sont des fonctions séparées. Évite d'importer Pillow/matplotlib dans les jobs de test headless.

6. **Colab compatibility** — idempotence des cellules, session monitoring, checkpoint recovery. `checkpoint_interval_steps` injectable pour la testabilité.

7. **Persona-driven API placement** — `register_invariant()` au niveau zéro de l'API publique (Samuel); `physlink.doctor()` sans dépendance ML (Hugo); surface publique minimale et stable (Petra).

8. **Performance benchmarks en CI** — fixture 1000 trajectoires synthétiques (numpy only), deux seuils mesurés : CPU-only (GitHub Actions) + T4 GPU (Colab). `pytest-benchmark` avec baseline JSON committé.

## Starter Template Evaluation

### Primary Technology Domain

Python ML infrastructure library (PyPI package) — pas de web framework.

### ADR-001: Build Tooling & Package Management

**Status:** Accepted — 2026-05-21
**Scope:** Décisions non-dérivables uniquement. Implémentation → fichiers concernés.

#### Décisions

**1. Build: python -m build (PyPA)**
Rationale: Gouvernance ouverte PyPA, auditablement neutre pour adoption institutionnelle.
Rejeté: uv (Astral VC-backed), hatch (opinionated, faible adoption ML).

**2. Linting: ruff --fix en pre-commit, ruff check bloquant en CI dès v0.1.0**
Rationale: Contributeurs = chercheurs ML. Autofix silencieux élimine la friction de linting.
Implémentation (Story 1.4): `ruff check src/` est bloquant en CI depuis v0.1.0 (`.github/workflows/ci.yml`).
Note: La planification initiale différait le blocage CI à v0.2.0 — l'implémentation a choisi de bloquer dès v0.1.0 pour des raisons de qualité. Cette décision est définitive.

**3. Type checking: mypy strict sur core/ uniquement**
Rationale: Stubs PyTorch incomplets rendent mypy strict sur adapters/ inutilement bloquant.
L'invariant backend-agnostique réel est protégé par test AST (voir décision 4).
ADR-002 (milestone v0.3.0) adressera adapters/.

**4. Invariant backend-agnostique — deux couches de vérification**
- mypy strict sur core/ (types purs, CI-blocking)
- AST check sur annotations publiques de adapters/ (no torch/jax dans les signatures)
  → intégré à test_core_no_torch_import.py

Rationale: Les signatures publiques de DreamerV3Adapter doivent utiliser des types
backend-agnostiques (list, np.ndarray) même si les internals utilisent torch.Tensor.
Contrat API visible en IDE sans dépendance framework.

**5. Publication: PyPI OIDC Trusted Publisher**
Rationale: Zéro credential à gérer, zéro expiration. Standard PyPI 2024+.

**6. GPU CI automatisé: après premier external contributor merged**
Rationale: GitHub Sponsors irréaliste pour ML académique. External contributor = signal
communauté mesurable et indépendant du budget.
- v0.1.x: test maintainer sur Colab T4 (voir CONTRIBUTING.md)
- v0.2+: RC 48h communauté avant release finale (voir CONTRIBUTING.md)
- GPU CI auto: après 1er external contributor merged

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Trajectory Data Contract — format d'échange entre utilisateur et adapter
- Exception Hierarchy — contrat d'erreur visible en IDE et en CI
- Module Public API Surface — ce que `import physlink` expose

**Important Decisions (Shape Architecture):**
- Checkpoint & Serialisation — format sur disque, contrat de compatibilité
- Documentation — moteur et déploiement du site

**Deferred Decisions (Post-MVP):**
- ADR-002: mypy strict sur `adapters/` — milestone v0.3.0
- GPU CI automatisé — après premier external contributor merged
- Constructeurs `TrajectoryBatch.from_list()` / `.from_numpy()` — v0.2

### Category 1 — Trajectory Data Contract

**Décision:** `TrajectoryBatch` comme conteneur canonique dans `physlink.core._types`.

**Contrat `fit()`:**
```python
def fit(
    trajectories: Union[list[dict], TrajectoryBatch],
    steps: int,
    checkpoint_interval_steps: int = 1000,
    debug_hooks: bool = False,
    checkpoint_dir: str = "physlink_checkpoints",
) -> AdaptationRun: ...
```

- `list[dict]` converti silencieusement en `TrajectoryBatch` à l'entrée — zéro friction Hugo
- `TrajectoryBatch` exposé dans l'API publique pour utilisateurs avancés (Samuel, Petra)
- Module `physlink.core._types` — backend-agnostique, numpy uniquement
- Constructeurs `TrajectoryBatch.from_list()` + `.from_numpy()` — v0.2 (après stabilisation du format)

**Hardenings Red Team appliqués:**
- Type annotation `Union[list[dict], TrajectoryBatch]` explicite dans la signature publique
- Test de boundary : `core/` ne peut pas importer `adapters/` (voir `test_core_boundary.py`)
- `BOUNDARY_EXCEPTIONS = []` — liste explicite auditée en review

### Category 2 — Exception Hierarchy

**Décision:** Hiérarchie custom `PhysLinkError` avec messages contextualisés.

```python
# physlink/core/exceptions.py
class PhysLinkError(Exception): ...

class ConfigurationError(PhysLinkError): ...   # mauvais params à l'init
class ValidationError(PhysLinkError): ...      # violations invariants runtime
class AdapterError(PhysLinkError): ...         # I/O géré par physlink (scope borné)

class CheckpointError(PhysLinkError): ...      # base commune checkpoints
class CheckpointCorruptError(CheckpointError): ...   # fichier illisible/corrompu
class CheckpointVersionError(CheckpointError):       # incompatibilité version
    checkpoint_version: str
    current_version: str
```

**Convention messages — toujours inclure:**
1. Ce qui a été reçu
2. Ce qui était attendu
3. `Fix:` — instruction explicite

**Scénario Samuel:** les erreurs `register_invariant` affichent la signature attendue `fn(trajectory: dict) -> float` pour préserver la dignité du domain scientist.

**Hardenings Red Team appliqués:**
- `CheckpointError` hérite de `PhysLinkError` directement (pas de `AdapterError`) — concept transversal
- `CheckpointVersionError` porte `checkpoint_version` + `current_version` comme attributs structurés — recovery automatisé possible
- `AdapterError` scope documenté dans docstring : I/O explicitement géré par physlink uniquement (pas OOM, pas timeout OS)

### Category 3 — Module Public API Surface

**Décision:** Namespace hybride persona-driven.

```python
# physlink/__init__.py
from physlink.utils.diagnostics import doctor                               # Hugo
from physlink.core.spaces import ObservationSpace, ActionSpace              # Hugo / Petra
from physlink.adapters.dreamer import DreamerV3Adapter                      # Hugo / Petra
from physlink.core.validation import register_invariant, ComplianceReport   # Samuel
from physlink.core.exceptions import PhysLinkError                          # tous

__all__ = [
    "doctor",
    "ObservationSpace", "ActionSpace",
    "DreamerV3Adapter",
    "register_invariant", "ComplianceReport",
    "PhysLinkError",
]
```

- Surface publique = exactement les objets touchés au premier contact par chaque persona
- `register_invariant` au niveau zéro — DD-003 spec : Samuel ne cherche pas dans les sous-modules
- Reste accessible dans `physlink.core`, `physlink.adapters` pour usage avancé
- `TrajectoryBatch`, `AdaptationConfig`, `AdaptationRun` dans sous-modules (usage avancé)

### Category 4 — Documentation

**Décision:** MkDocs Material + mkdocstrings[python] + GitHub Pages.

| Composant | Choix | Raison |
|-----------|-------|--------|
| Moteur | MkDocs + Material theme | Setup 15 min, thème ML-standard |
| API auto-gen | mkdocstrings[python] | Génère depuis docstrings existantes |
| Hébergement | GitHub Pages (`mkdocs gh-deploy`) | Zéro infrastructure additionnelle |
| Versioning | mike | Multi-version docs dès v0.2 |
| Signal Petra | Badge "docs" README → GitHub Pages | Suffisant pour v0.1 |

Dépendances doc (dev-only) : `mkdocs-material`, `mkdocstrings[python]`, `mike`.

### Category 5 — Checkpoint & Serialisation

**Décision:** safetensors (Hugging Face) avec métadonnées JSON embarquées.

**Format sur disque:**
```
checkpoint_step_N.safetensors
  ├── tensors: poids du modèle (binaire, zéro pickle)
  └── metadata: {
        "physlink_version": "0.1.3",
        "adapter_class": "DreamerV3Adapter",
        "timestamp": "2026-05-21T22:00:00Z",
        "checkpoint_step": "5000"
      }
```

- `CheckpointVersionError` lit les métadonnées AVANT de charger les poids — détection précoce
- Zéro risque pickle RCE — format binaire sécurisé, pas d'exécution de code arbitraire
- Compatible numpy + torch — backend-agnostique au niveau du format
- Dépendance légère : `pip install safetensors` (~1 Mo)

Rejeté: `torch.save` (pickle RCE, opaque au version mismatch), JSON + npy (verbeux, overhead conversion).

### Decision Impact Analysis

**Séquence d'implémentation recommandée:**
1. `physlink/core/exceptions.py` — hiérarchie, pas de dépendance
2. `physlink/core/_types.py` — `TrajectoryBatch`, pas de dépendance
3. `physlink/core/spaces.py` — `ObservationSpace`, `ActionSpace`
4. `physlink/core/adapter.py` — classe abstraite `BaseAdapter`
5. `physlink/adapters/dreamer.py` — `DreamerV3Adapter` avec safetensors
6. `physlink/core/validation.py` — `register_invariant`, `ComplianceReport`
7. `physlink/utils/diagnostics.py` — `doctor()` isolé, zéro dépendance ML
8. `physlink/__init__.py` — exports persona-driven
9. `mkdocs.yml` + doc site

**Dépendances croisées critiques:**
- `DreamerV3Adapter` dépend de `TrajectoryBatch` (core._types) et `CheckpointError` (core.exceptions)
- `register_invariant` dépend de `DreamerV3Adapter` (DD-003: s'attache à un adapter existant)
- `physlink.__init__` dépend de tout — à implémenter en dernier
- `doctor()` est intentionnellement isolé — aucune dépendance ML, testable sans GPU

## Implementation Patterns & Consistency Rules

### Points de conflit identifiés

7 zones où des agents IA pourraient produire du code incompatible :

| Zone | Exemple de conflit | Règle |
|------|-------------------|-------|
| 1. Naming Python | `obs_space` vs `observation_space` | Noms complets, zéro abréviation |
| 2. Structure src/ | `physlink/` vs `src/physlink/` | `src/` layout strict |
| 3. Tests | co-localisés vs `tests/` racine | `tests/` à la racine, mirroir src/ |
| 4. Docstrings | Google vs NumPy vs reST | Google style (mkdocstrings) |
| 5. Type annotations | `Union[X,Y]` vs `X \| Y` | `X \| Y` (Python 3.10+) |
| 6. Error messages | f-string libre vs structuré | Template Got/Expected/Fix obligatoire |
| 7. Fixtures pytest | conftest par module vs racine | Un seul `tests/conftest.py` |

### Naming Patterns

**Convention universelle :** snake_case pour tout sauf les classes.

```python
# ✅ Correct
class ObservationSpace: ...
def register_invariant(adapter, name, fn, tolerance, mode): ...
trajectory_batch: TrajectoryBatch
checkpoint_interval_steps: int

# ❌ Interdit
class observationSpace: ...   # camelCase
def reg_inv(...): ...          # abréviation
obs_sp: ObsSpace               # double abréviation
```

Règles :
- Classes : PascalCase
- Fonctions, variables, paramètres : snake_case
- Constantes de module : UPPER_SNAKE_CASE
- Modules : snake_case (jamais de tiret)
- Attributs privés : `_nom` (un underscore), jamais `__nom` (dunder réservé Python)

### Structure Patterns

**Layout `src/` strict :**

```
physlink/                      # racine repo
├── src/
│   └── physlink/              # package installable
│       ├── __init__.py        # exports persona-driven uniquement
│       ├── core/
│       │   ├── __init__.py
│       │   ├── _types.py      # TrajectoryBatch
│       │   ├── adapter.py     # BaseAdapter (abstraite)
│       │   ├── exceptions.py  # hiérarchie PhysLinkError
│       │   ├── spaces.py      # ObservationSpace, ActionSpace
│       │   └── validation.py  # register_invariant, ComplianceReport
│       ├── adapters/
│       │   ├── __init__.py
│       │   └── dreamer.py     # DreamerV3Adapter
│       └── utils/
│           ├── __init__.py
│           ├── diagnostics.py # doctor() — zéro dépendance ML
│           └── visualization.py
├── tests/
│   ├── conftest.py            # fixtures partagées (numpy-only)
│   ├── unit/
│   │   ├── core/              # miroir de src/physlink/core/
│   │   ├── adapters/
│   │   └── utils/
│   ├── integration/
│   └── perf/                  # pytest-benchmark, baseline JSON committé
├── docs/
│   └── (mkdocs sources)
├── pyproject.toml
└── mkdocs.yml
```

Règles :
- `src/` layout — jamais de package à la racine (évite import-from-repo accidentel)
- Tests dans `tests/`, jamais co-localisés avec le code source
- `tests/unit/` reflète exactement `src/physlink/` (un fichier de test par module)
- Fixtures GPU marquées `@pytest.mark.gpu` — jamais exécutées en CPU CI

### Docstring Patterns

**Format : Google style** (compatible mkdocstrings[python]).

```python
def register_invariant(
    adapter: DreamerV3Adapter,
    name: str,
    fn: Callable[[dict], float],
    tolerance: float,
    mode: Literal["hard", "soft"] = "soft",
) -> None:
    """Attach a physical invariant check to an adapter.

    Args:
        adapter: The adapter instance to augment.
        name: Human-readable invariant name (shown in ComplianceReport).
        fn: Callable accepting a trajectory dict and returning a residual float.
            Signature: fn(trajectory: dict) -> float
        tolerance: Maximum acceptable residual before violation is flagged.
        mode: "hard" rejects trajectories; "soft" penalizes the loss.

    Raises:
        ConfigurationError: If fn signature does not match expected protocol.
        ConfigurationError: If tolerance is negative.

    Example:
        >>> def mass_conservation(traj):
        ...     return abs(traj["mass_in"] - traj["mass_out"])
        >>> register_invariant(adapter, "mass", mass_conservation, tolerance=1e-3)
    """
```

Règles :
- Section `Args:` obligatoire pour tout paramètre non-évident
- Section `Raises:` obligatoire si la fonction peut lever une `PhysLinkError`
- Section `Example:` obligatoire pour toute fonction de l'API publique
- Pas de reST (`:param:`, `:type:`), pas de NumPy (tirets sous les sections)

### Type Annotation Patterns

**Python 3.10+ union syntax partout :**

```python
# ✅ Correct (Python 3.10+)
from __future__ import annotations  # obligatoire dans core/ pour forward refs

def fit(
    trajectories: list[dict] | TrajectoryBatch,
    steps: int,
    checkpoint_interval_steps: int = 1000,
    debug_hooks: bool = False,
    checkpoint_dir: str = "physlink_checkpoints",
) -> AdaptationRun: ...

# ❌ Interdit
from typing import Union, List, Optional  # legacy typing — banned in core/
def fit(trajectories: Union[List[dict], TrajectoryBatch], ...) -> AdaptationRun: ...
```

Règles :
- `from __future__ import annotations` dans tous les fichiers `core/`
- `X | Y` au lieu de `Union[X, Y]`
- `X | None` au lieu de `Optional[X]`
- `list[X]` au lieu de `List[X]`, `dict[K, V]` au lieu de `Dict[K, V]`
- Annotations publiques adapters/ : types backend-agnostiques uniquement (`list`, `np.ndarray`) — jamais `torch.Tensor` en signature publique

### Error Message Patterns

**Template obligatoire : Got / Expected / Fix**

```python
# ✅ Correct
raise ConfigurationError(
    f"register_invariant: invalid fn signature.\n"
    f"  Got:      {fn} with signature {inspect.signature(fn)}\n"
    f"  Expected: fn(trajectory: dict) -> float\n"
    f"  Fix:      ensure your function accepts a single dict argument and returns a float."
)

raise CheckpointVersionError(
    f"Checkpoint version mismatch.\n"
    f"  Got:      checkpoint saved with physlink=={error.checkpoint_version}\n"
    f"  Expected: physlink=={error.current_version}\n"
    f"  Fix:      re-run adapter.fit() to generate a fresh checkpoint.",
    checkpoint_version="0.1.0",
    current_version="0.2.0",
)

# ❌ Interdit
raise ConfigurationError("bad fn")          # aucun contexte
raise ConfigurationError(f"fn={fn} error")  # pas de Fix:
```

### Testing Patterns

**Fixtures :**

```python
# tests/conftest.py — fixture partagée CPU CI
@pytest.fixture
def synthetic_trajectories() -> list[dict]:
    """1000 trajectories numpy-only — no GPU required."""
    rng = np.random.default_rng(42)
    return [{"obs": rng.random(7), "action": rng.random(3)} for _ in range(1000)]

# Marquage GPU obligatoire
@pytest.mark.gpu
def test_fit_t4_performance(synthetic_trajectories):
    ...
```

Règles :
- `tests/conftest.py` unique — jamais de conftest.py dans les sous-dossiers
- Fixtures synthétiques numpy-only pour CPU CI (zéro dépendance GPU)
- `@pytest.mark.gpu` pour tout test nécessitant CUDA — exclues du job `test-cpu`
- Tests AST (boundary + no-torch-import) dans `tests/integration/test_core_no_torch_import.py` et `tests/integration/test_core_boundary.py`

### Enforcement Guidelines

**Tous les agents DOIVENT :**
- Utiliser le layout `src/physlink/` — jamais de package à la racine
- Nommer les paramètres en entier (zéro abréviation)
- Écrire les messages d'erreur avec le template Got/Expected/Fix
- Annoter avec la syntaxe `X | Y` Python 3.10+
- Docstrings Google style sur toutes les fonctions publiques
- Marquer `@pytest.mark.gpu` sur tout test CUDA

**Vérification automatique :**
- `test_core_no_torch_import.py` — AST walk sur `src/physlink/core/**/*.py`
- `test_core_boundary.py` — aucun import de `core/` vers `adapters/`
- `ruff --fix` pre-commit — enforce naming et style
- `mypy --strict` sur `src/physlink/core/` — enforce annotations

## Project Structure & Boundaries

### Complete Project Directory Structure

```
physlink/
├── README.md
├── CHANGELOG.md                          # Keep a Changelog format (DD-002)
├── CONTRIBUTING.md                       # GPU CI protocol, RC process
├── LICENSE                               # MIT
├── pyproject.toml                        # python-m-build, ruff, mypy config
├── mkdocs.yml                            # MkDocs Material config
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                        # test-cpu (gate PRs) + test-gpu (gate releases)
│   │   └── publish.yml                   # PyPI OIDC Trusted Publisher
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md                 # Template rapport de bug (Story 5.3)
│   │   ├── feature_request.md            # Template demande de feature (Story 5.3)
│   │   └── domain_extension.md           # DD-002: template PR communauté (Samuel DD-003)
│   └── PULL_REQUEST_TEMPLATE.md          # checklist CHANGELOG + invariants
│
├── src/
│   └── physlink/
│       ├── __init__.py                   # exports persona-driven (7 symboles)
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── _types.py                 # FR-02/03: TrajectoryBatch, AdaptationConfig, AdaptationRun
│       │   ├── adapter.py                # FR-03: BaseAdapter (abstraite)
│       │   ├── exceptions.py             # PhysLinkError + hiérarchie complète
│       │   ├── spaces.py                 # FR-02: ObservationSpace, ActionSpace
│       │   └── validation.py             # FR-04/DD-003: register_invariant, ComplianceReport
│       │
│       ├── adapters/
│       │   ├── __init__.py
│       │   └── dreamer.py                # FR-03: DreamerV3Adapter + safetensors
│       │
│       └── utils/
│           ├── __init__.py
│           ├── diagnostics.py            # FR-01: doctor() — zéro dépendance ML
│           └── visualization.py          # FR-04: triptych GIF renderer
│
├── tests/
│   ├── conftest.py                       # fixtures numpy-only (1000 traj synthétiques)
│   ├── unit/
│   │   ├── core/
│   │   │   ├── test_types.py             # TrajectoryBatch, conversion list[dict]
│   │   │   ├── test_exceptions.py        # hiérarchie, attributs structurés
│   │   │   ├── test_spaces.py            # ObservationSpace, ActionSpace, explain()
│   │   │   └── test_validation.py        # register_invariant, ComplianceReport
│   │   ├── adapters/
│   │   │   └── test_dreamer_cpu.py       # DreamerV3Adapter sans GPU (mock)
│   │   └── utils/
│   │       ├── test_diagnostics.py       # doctor() — zéro GPU requis
│   │       └── test_visualization.py     # triptych render (frames mock)
│   ├── integration/
│   │   ├── test_core_no_torch_import.py  # AST walk core/ — invariant backend-agnostique
│   │   ├── test_core_boundary.py         # core/ ne peut pas importer adapters/
│   │   ├── test_api_stability.py         # surface publique __init__ stable
│   │   ├── test_ci_pipeline_config.py    # CI workflow YAML structure
│   │   ├── test_publish_workflow_config.py  # PyPI publish workflow
│   │   ├── test_docs_infrastructure.py   # MkDocs config, mkdocs.yml
│   │   ├── test_docstring_completeness.py  # public API docstring coverage
│   │   ├── test_toolchain_compliance.py  # ruff/mypy config in pyproject.toml
│   │   ├── test_readme_content.py        # README badges + action bar (Epic 1.6)
│   │   ├── test_changelog_content.py     # CHANGELOG.md format, 3 releases (Epic 5.1)
│   │   ├── test_lab_adoption_guide.py    # Lab Adoption Guide content (Epic 5.2)
│   │   ├── test_github_templates.py      # PR + issue templates (Epic 5.3)
│   │   ├── test_readme_domain_scientist_link.py  # "For Domain Scientists →" link (Epic 6.1)
│   │   ├── test_domain_scientists_page.py  # domain-scientists.md content (Epic 6.2)
│   │   └── test_domain_scientist_notebook.py  # Colab notebook structure (Epic 6.3)
│   └── perf/
│       ├── baselines/
│       │   └── benchmark_baseline.json   # committé — référence NFR
│       └── test_nfr_benchmarks.py        # compliance_report() <30s, doctor() <15s
│
├── notebooks/
│   ├── quickstart.ipynb                  # DD-001: Hugo path — Quick Start (Epic 1.6)
│   └── domain-scientist-colab.ipynb      # DD-003: Samuel path — 8-cell compliance validation (Epic 6.3)
│
└── docs/
    ├── index.md
    ├── getting-started.md                # DD-001: 5-step Colab path Hugo
    ├── domain-scientists.md              # DD-003: Samuel, physical hallucinations
    ├── api/
    │   └── (auto-généré par mkdocstrings)
    ├── changelog.md                      # DD-002: mirror CHANGELOG.md
    └── lab-adoption-guide.md             # DD-002: Petra
```

### Requirements to Structure Mapping

| FR / DD | Fichier principal | Fichier test |
|---------|-----------------|-------------|
| FR-01 `physlink.doctor()` | `utils/diagnostics.py` | `tests/unit/utils/test_diagnostics.py` |
| FR-02 Universal Space API | `core/spaces.py` | `tests/unit/core/test_spaces.py` |
| FR-03 DreamerV3 Adapter | `adapters/dreamer.py` + `core/adapter.py` | `tests/unit/adapters/test_dreamer_cpu.py` |
| FR-04 Triptych | `utils/visualization.py` + `core/validation.py` | `tests/unit/utils/test_visualization.py` |
| DD-003 `register_invariant` | `core/validation.py` | `tests/unit/core/test_validation.py` |
| DD-002 `AdaptationConfig/Run` | `core/_types.py` | `tests/unit/core/test_types.py` |
| Invariant AST backend | — | `tests/integration/test_core_no_torch_import.py` |
| Boundary core→adapters | — | `tests/integration/test_core_boundary.py` |
| NFR benchmarks | — | `tests/perf/test_nfr_benchmarks.py` |
| DD-002 Institutional trust (CHANGELOG, Lab Guide, GitHub templates) | `CHANGELOG.md`, `docs/lab-adoption-guide.md`, `.github/` | `tests/integration/test_changelog_content.py`, `test_lab_adoption_guide.py`, `test_github_templates.py` |
| DD-003 Domain scientist entry point (README link) | `README.md` | `tests/integration/test_readme_domain_scientist_link.py` |
| DD-003 Domain scientist landing page | `docs/domain-scientists.md` | `tests/integration/test_domain_scientists_page.py` |
| DD-003 Samuel Colab notebook | `notebooks/domain-scientist-colab.ipynb` | `tests/integration/test_domain_scientist_notebook.py` |

### Architectural Boundaries

```
physlink.core/     →  physlink.core/        ✅ OK — intra-core
physlink.core/     →  physlink.adapters/    ❌ INTERDIT (test_core_boundary.py — AST walk, catches even TYPE_CHECKING imports)
physlink.adapters/ →  physlink.core/        ✅ OK
physlink.utils/    →  physlink.core/        ✅ OK
physlink.utils/    →  physlink.adapters/    ❌ INTERDIT (utils indépendants)
physlink/__init__  →  tous                  ✅ OK (entry point)
utils/diagnostics  →  (rien)               ✅ Zéro dépendance ML — FR-01
```

**Règle critique `doctor()`:** `utils/diagnostics.py` ne peut importer aucun module physlink hormis `core.exceptions`. Hugo quitte si `physlink.doctor()` plante parce que PyTorch n'est pas installé.

**Règle `core/ → adapters/` — Pattern canonique (Protocol) :**

`test_core_boundary.py` utilise un AST walk qui capture **tous** les imports de `adapters/` dans `core/`, y compris les imports sous `if TYPE_CHECKING:`. Une tentative de contournement via `TYPE_CHECKING` échoue.

Solution canonique : définir un **Protocol** dans `core/` qui duck-type l'interface minimale requise de l'adapter.

```python
# ✅ Correct — dans core/validation.py
from typing import Any, Protocol

class _HasInvariants(Protocol):
    """Protocol for adapters that accept registered invariants."""
    _invariants: list[Any]

def register_invariant(adapter: _HasInvariants, ...) -> None:
    # Aucun import de adapters/ requis — duck-typing via Protocol
    adapter._invariants.append(...)
```

```python
# ❌ Interdit — même dans TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from physlink.adapters.dreamer import DreamerV3Adapter  # Caught by AST walk
```

Ce pattern (`_HasInvariants` Protocol dans `core/validation.py`) est l'exemple canonique établi en Story 4.3. Toute future interaction `core/ → adapters/` doit suivre ce modèle.

### Integration Points

**Flux de données Hugo (DD-001) :**
```
physlink.doctor()               → utils/diagnostics.py      [FR-01]
ObservationSpace.from_*()       → core/spaces.py             [FR-02]
DreamerV3Adapter.fit()          → adapters/dreamer.py        [FR-03]
  ↳ TrajectoryBatch             → core/_types.py
  ↳ checkpoint_step_N.safetensors → filesystem
ComplianceReport + visualize()  → core/validation.py         [FR-04]
                                   utils/visualization.py
```

**Flux Samuel (DD-003) :**
```
register_invariant(adapter, name, fn, tolerance, mode)
  → core/validation.py
  → attache fn à adapter (adapters/dreamer.py)
  → ComplianceReport (objet de données pur)
  → report.plot() si matplotlib disponible (appel explicite)
```

**CI/CD :**
```
PR ouvert → test-cpu (GitHub Actions, zéro GPU)
  → ruff --fix (pre-commit)
  → mypy --strict core/
  → test_core_no_torch_import.py
  → test_core_boundary.py
  → tests/unit/ + tests/integration/
  → tests/perf/ (CPU seuils uniquement)

Release candidate → test-gpu (Colab T4, maintainer v0.1 / RC communauté v0.2+)
  → tests/unit/adapters/ @pytest.mark.gpu
  → tests/perf/ (T4 seuils)

Publish → pypa/gh-action-pypi-publish (OIDC Trusted Publisher)
```

## Architecture Validation Results

### Coherence Validation ✅

| Vérification | Résultat |
|-------------|---------|
| python -m build + src/ layout + pyproject.toml | ✅ |
| ruff + mypy strict core/ (pas adapters/) | ✅ |
| safetensors + torch backend | ✅ numpy+torch-agnostique |
| MkDocs + Google docstrings + mkdocstrings | ✅ |
| PyPI OIDC + GitHub Actions publish.yml | ✅ |
| TrajectoryBatch core/_types.py + backend-agnostique | ✅ |
| Union X\|Y Python 3.10+ + `from __future__ import annotations` | ✅ |
| Got/Expected/Fix + CheckpointVersionError attributs structurés | ✅ |
| tests/ conftest unique + @pytest.mark.gpu | ✅ |

### Requirements Coverage Validation ✅

| FR / NFR | Support architectural | Fichier | Test |
|---------|--------------------|---------|------|
| FR-01 `doctor()` | ✅ | `utils/diagnostics.py` | `test_diagnostics.py` |
| FR-02 Universal Space API | ✅ | `core/spaces.py` | `test_spaces.py` |
| FR-03 DreamerV3Adapter | ✅ | `adapters/dreamer.py` | `test_dreamer_cpu.py` |
| FR-04 Triptych | ✅ | `utils/visualization.py` | `test_visualization.py` |
| DD-003 `register_invariant` | ✅ | `core/validation.py` | `test_validation.py` |
| DD-002 `AdaptationConfig/Run` | ✅ | `core/_types.py` | `test_types.py` |
| NFR `doctor()` < 15s | ✅ | `diagnostics.py` isolé + perf benchmark | |
| NFR `pip install` < 60s | ✅ | Lean deps (safetensors, rich, numpy, pyyaml) | |
| NFR compliance < 30s | ✅ | `tests/perf/` deux seuils CPU + T4 | |
| NFR VRAM < 8GB | ⚠️ Runtime uniquement | CONTRIBUTING.md test maintainer | |
| NFR API stabilité | ✅ | `test_api_stability.py` + CHANGELOG | |

### Gap Analysis Results

**Gaps importants (déférés, non bloquants) :**
- `ExplainableMixin` — `.explain()` cross-cutting concern → `core/_mixins.py` à créer
- `TrajectoryBuffer.export(path)` / `.load(path)` (DD-002) → ✅ IMPLEMENTED in `core/_types.py` (Story 4.2); post-v0.1 refactor to `utils/io.py` remains optional
- `AdaptationConfig` schéma YAML — format de sérialisation non spécifié → décision à l'implémentation

**Gaps mineurs :**
- `rich` vs `tqdm` pour progress bar FR-03 → décision à l'implémentation
- NFR VRAM < 8GB / < 45 min T4 → contraintes runtime non testables en CI, documentées dans CONTRIBUTING.md

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status : READY FOR IMPLEMENTATION**
**Confidence Level : High — 16/16 checklist items, 0 critical gaps**

**Points forts :**
- Invariant backend-agnostique doublement protégé (mypy strict core/ + AST check adapters/ signatures)
- Hiérarchie d'exceptions avec attributs machine-readable (`CheckpointVersionError.checkpoint_version`)
- Surface API persona-driven — Hugo, Petra, Samuel trouvent chacun ce qu'ils cherchent au niveau zéro
- Checkpoint safetensors — détection précoce version mismatch avant chargement poids
- CI à deux niveaux — GPU testing évolutif sans bloquer contributions v0.1

**Axes d'amélioration post-v0.1 :**
- `ExplainableMixin` dans `core/_mixins.py`
- `TrajectoryBuffer` I/O refactor from `core/_types.py` to `utils/io.py` (currently in `core/_types.py` — functional, refactor optional)
- mypy strict sur `adapters/` — ADR-002 milestone v0.3.0
- GPU CI automatisé après premier external contributor merged

### Implementation Handoff

**Séquence recommandée pour les agents IA :**
1. `src/physlink/core/exceptions.py` — aucune dépendance
2. `src/physlink/core/_types.py` — `TrajectoryBatch`, `AdaptationConfig`, `AdaptationRun`
3. `src/physlink/core/spaces.py` — `ObservationSpace`, `ActionSpace`
4. `src/physlink/core/adapter.py` — `BaseAdapter` (abstraite)
5. `src/physlink/adapters/dreamer.py` — `DreamerV3Adapter` + safetensors
6. `src/physlink/core/validation.py` — `register_invariant`, `ComplianceReport`
7. `src/physlink/utils/diagnostics.py` — `doctor()` (zéro import ML)
8. `src/physlink/utils/visualization.py` — triptych GIF renderer
9. `src/physlink/__init__.py` — exports persona-driven (en dernier)
10. `tests/` — miroir de la structure src/ + tests AST + benchmarks perf
11. `mkdocs.yml` + `docs/` — site de documentation

**Référence pour toute question architecturale :** ce document (`_bmad-output/planning-artifacts/architecture.md`).
