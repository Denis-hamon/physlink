# Test Automation Summary — Story 6.1: README "For Domain Scientists" Link

**Date:** 2026-05-22
**Framework:** pytest 9.0.3 / Python 3.12.1
**Story file:** `_bmad-output/implementation-artifacts/6-1-readme-for-domain-scientists-link.md`

## Generated Tests

### Integration Tests

- [x] `tests/integration/test_readme_domain_scientist_link.py` — 8 tests (5 originaux + 3 lacunes comblées)

#### Class `TestDomainScientistLinkPresent` (AC #1, #2 — présence & above-fold)

| Test | Description |
|------|-------------|
| `test_link_text_present` | "For Domain Scientists" présent dans le README |
| `test_link_target_present` | href `docs/domain-scientists.md` présent dans le README |
| `test_target_file_exists` | `docs/domain-scientists.md` existe sur disque |
| `test_link_inside_action_bar` | Lien dans le bloc `<p align="center">` (action bar) |
| `test_link_appears_before_description` | Lien avant `Backend-agnostic adapter library…` (above-fold confirmé) |

#### Class `TestDomainScientistLinkFormat` (structure HTML exacte — lacunes auto-appliquées)

| Test | Description | Lacune comblée |
|------|-------------|----------------|
| `test_link_has_arrow_character` | Texte complet `For Domain Scientists →` (avec `→`) | Flèche spécifiée dans la story mais non testée |
| `test_link_uses_strong_formatting` | Balise `<strong>For Domain Scientists` présente dans l'action bar | Cohérence avec les autres entrées (Dev Notes spec) |
| `test_separator_between_evaluate_and_domain_scientists` | Séparateur `|` entre les entrées 2 et 3 de l'action bar | Séparateur 1-2 testé ailleurs, 2-3 non testé |

## Coverage

| Acceptance Criteria | Tests couvrant |
|--------------------|----------------|
| AC #1: Lien visible premier viewport, navigue vers `docs/domain-scientists.md` | 5 tests (présence + above-fold + existence fichier + href) |
| AC #2: Trouvable en 10s, placement above-fold | 2 tests (`test_link_inside_action_bar`, `test_link_appears_before_description`) |
| Structure HTML cohérente avec les autres entrées de l'action bar | 3 tests (flèche, strong, séparateur) |

- Tests d'intégration story 6.1 : **8 / 8 passés**
- Suite d'intégration complète : **262 passés, 2 skippés, 0 échecs**
- `ruff check src/` : ✅ passe
- `mypy --strict src/physlink/core/` : ✅ passe

## Lacunes auto-appliquées

3 tests ajoutés pour combler les lacunes identifiées par l'analyse QA :

1. **`test_link_has_arrow_character`** — La story spécifie `For Domain Scientists →` avec la flèche Unicode. Les 5 tests originaux ne vérifiaient que "For Domain Scientists" sans la flèche. Un échec détecterait une régression où la flèche serait supprimée.

2. **`test_link_uses_strong_formatting`** — Les Dev Notes spécifient `<strong>For Domain Scientists →</strong>` pour correspondre aux autres entrées de l'action bar. Aucun test précédent ne validait cette structure HTML.

3. **`test_separator_between_evaluate_and_domain_scientists`** — `test_readme_content.py` vérifie le séparateur `|` entre Quick Start et Evaluate (entrées 1-2), mais pas entre Evaluate et For Domain Scientists (entrées 2-3). Ce test ferme cette lacune.

## Commandes pour exécuter les tests

```bash
# Tests story 6.1 uniquement
pytest tests/integration/test_readme_domain_scientist_link.py -v

# Suite complète (hors tests de stabilité API lents)
pytest tests/ --ignore=tests/integration/test_api_stability.py
```
