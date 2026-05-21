# Tech Audit: PhysLink (Greenfield)

**Status:** Target Architecture Defined
**Date:** 2026-05-20
**Project Type:** Python Infrastructure / ML Toolkit

---

## 1. Stack Technique Cible

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Language** | Python 3.10+ | Standard pour le domaine; support des types avancés. |
| **Backend** | PyTorch 2.x | Framework dominant en Embodied AI; support Natif de JIT/Compile. |
| **Distrib** | PyPI / setuptools | Distribution frictionless via `pip install`. |
| **CI/CD** | GitHub Actions | Tests de régression sur les dimensions et stabilité API. |
| **Target Env** | Google Colab (T4) | Contrainte de démo (<90 min, session monitoring). |

---

## 2. Architecture du Codebase

Structure `src/` standard pour éviter les conflits d'importation :

```
/
├── src/
│   └── physlink/
│       ├── __init__.py          # Point d'entrée, exports API
│       ├── core/
│       │   ├── spaces.py        # ObservationSpace, ActionSpace
│       │   ├── adapter.py       # Base Adapter classes
│       │   └── validation.py    # Domain Validation Hooks
│       ├── adapters/
│       │   └── dreamer.py       # DreamerV3 specific implementation
│       ├── utils/
│       │   ├── diagnostics.py   # logic for physlink.doctor()
│       │   └── visualization.py # Layer 0 renderers (GIF/Images)
│       └── cli.py               # Entry point for physlink doctor CLI
├── tests/                       # Unit & Integration tests
├── pyproject.toml               # Build system & dependencies
└── README.md                    # Symlink/Mirror of design-artifacts
```

---

## 3. Décisions Architecturales Critiques (Greenfield)

### 3.1 API Declarative / Factory Pattern
Pour satisfaire le "Moment de reconnaissance" d'Hugo, nous utiliserons massivement le pattern Factory (`ObservationSpace.from_proprioception`). Cela permet de masquer la complexité des tenseurs derrière des termes métier (joints, velocity).

### 3.2 Monitoring de Session Colab
Le challenge technique de `physlink.doctor()` est de capturer le temps restant de la session Colab. 
- **Approche** : Utilisation de `google.colab.runtime` (si disponible) ou estimation basée sur l'uptime système de la VM. Si impossible d'avoir une précision absolue, on affichera un avertissement standard basé sur les limites connues du tier gratuit (12h max).

### 3.3 Introspection & Explainability
Chaque objet core héritera d'une mixin `Explainable` fournissant la méthode `.explain()`. Cette méthode retournera un objet structuré (Rich text ou Markdown) détaillant les transformations (ex: normalisation, clipping).

### 3.4 Sérialisation (Phase 2 Ready)
Les `AdaptationJob` seront gérés via des dataclasses sérialisables en YAML/JSON dès le départ pour assurer la compatibilité future avec des orchestrateurs type SLURM.

---

## 4. Points de Risque

1. **Stabilité Colab T4** : Le run de 75 minutes doit rester stable. Nous devrons implémenter des checkpoints agressifs (toutes les 10-15 min).
2. **Performance DreamerV3** : S'assurer que l'implémentation PyTorch est optimisée pour un seul GPU (usage de `torch.compile` si pertinent).
3. **Dépendances** : Garder un ensemble de dépendances "lean" pour assurer le succès du `physlink doctor` en moins de 30 secondes.

---

**Audit validé.** Prêt pour la rédaction de la première PRD (Scenario 01).
