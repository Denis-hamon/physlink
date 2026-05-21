# PRD: Scenario 01 - Hugo's "Friday Afternoon Test"

**Status:** Draft
**Version:** 1.0
**Target Milestone:** MVP (v0.1.0)

---

## 1. Objectif du Document
Définir les exigences techniques pour valider le Scénario 01 : un chercheur (Hugo) doit pouvoir installer PhysLink, configurer un espace robotique via une API reconnaissable, et lancer une adaptation DreamerV3 sur Colab T4 en moins de 90 minutes.

---

## 2. Exigences Fonctionnelles (Functional Requirements)

### 2.1 FR-01: Zero-Friction Diagnostics (`physlink doctor`)
- **Action** : Doit scanner l'environnement et retourner un statut "Go/No-Go" en moins de 15 secondes.
- **Data Points** : Version Python, Presence de PyTorch, Disponibilité CUDA, Mémoire GPU (VRAM), Estimation du temps de session Colab restant.
- **Output** : Texte formatté (Rich) avec des indicateurs visuels (✓/✗) et une suggestion claire de l'étape suivante.

### 2.2 FR-02: Universal Space API (Core Abstraction)
- **ObservationSpace** : Doit supporter `.from_proprioception(joints, include_velocity, ...)` retournant un espace structuré.
- **ActionSpace** : Doit supporter `.continuous(dims, bounds)` avec validation immédiate des types.
- **Explainability** : Chaque objet doit implémenter `.explain()` retournant un dictionnaire de métadonnées sur les transformations internes (clipping, normalization).

### 2.3 FR-03: DreamerV3 Adapter
- **Initialization** : Reçoit `ObservationSpace` et `ActionSpace`.
- **Fit Method** : `.fit(trajectories, steps)` déclenchant la boucle d'adaptation.
- **Loop UI** : Barre de progression asynchrone affichant `Prediction: OK/ANOMALY` et un ETA crédible.
- **Checkpointing** : Sauvegarde automatique de l'état toutes les 10 minutes ou 1000 steps.

### 2.4 FR-04: Triptyque Validation
- **Renderer** : Fonction `.visualize()` produisant un GIF/Animation composé de 3 volets (Imagination, Real, Difference).
- **Time-to-Science** : Calcul automatique du temps de run vs estimation from-scratch (basé sur la complexité de l'espace).

---

## 3. Exigences Non-Fonctionnelles (Technical Requirements)

### 3.1 Performance Benchmark
- **Target** : Adaptation sur bras 7-DOF (10k steps) < 75 minutes sur Tesla T4.
- **VRAM Constraint** : Doit tenir dans < 8GB de VRAM pour éviter les OOM sur T4.

### 3.2 API Interface
- **Backend Agnostic** : L'interface `physlink.core` ne doit pas dépendre directement de primitives PyTorch dans ses types publics (usage de `numpy`-like ou listes pour la configuration).

---

## 4. Critères d'Acceptation (Acceptance Criteria)

- [ ] **AC-01** : `pip install .` et `import physlink; physlink.doctor()` s'exécutent sans erreur sur un notebook Colab vierge.
- [ ] **AC-02** : La configuration d'un bras 7-DOF prend moins de 15 lignes de code Python (hors imports).
- [ ] **AC-03** : En cas d'erreur de dimension (ex: mismatch actions), `.summary()` lève une exception explicite indiquant l'erreur et la correction.
- [ ] **AC-04** : Le run d'adaptation survit à une déconnexion Colab courte grâce au dernier checkpoint.
- [ ] **AC-05** : Le fichier exporté par `adapter.export()` est un YAML valide contenant la configuration de l'espace et le chemin du checkpoint.

---

**Validé par Mimir.** Prêt pour l'initialisation du build.
