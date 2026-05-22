# Test Automation Summary — Story 5.1: CHANGELOG with Three Dated Releases

**Date:** 2026-05-22
**Framework:** pytest 9.0.3 / Python 3.12.1
**Story file:** `_bmad-output/implementation-artifacts/5-1-changelog-with-three-dated-releases.md`

---

## Generated Tests

### Integration Tests — `tests/integration/test_changelog_content.py` (34 nouveaux tests)

**`TestChangelogExistence`** (2 tests — AC #3)
- [x] `test_changelog_exists_at_repo_root` — CHANGELOG.md présent à la racine (hard NO-GO si absent)
- [x] `test_changelog_is_not_empty` — fichier non vide

**`TestChangelogHeader`** (5 tests — AC #1)
- [x] `test_changelog_h1_heading_present` — `# Changelog` en titre H1
- [x] `test_keep_a_changelog_reference_present` — lien vers keepachangelog.com
- [x] `test_semantic_versioning_reference_present` — lien vers semver.org
- [x] `test_unreleased_section_present` — section `## [Unreleased]` présente
- [x] `test_unreleased_appears_before_first_versioned_release` — [Unreleased] avant la première release

**`TestChangelogReleases`** (5 tests — AC #1)
- [x] `test_at_least_three_dated_releases` — ≥ 3 entrées `## [X.Y.Z] - YYYY-MM-DD`
- [x] `test_release_v010_present` — release v0.1.0 présente (Epics 1+2)
- [x] `test_release_v011_present` — release v0.1.1 présente (Epic 3: DreamerV3Adapter)
- [x] `test_release_v012_present` — release v0.1.2 présente (Epic 4: register_invariant)
- [x] `test_all_release_dates_use_iso8601_format` — toutes les dates en format YYYY-MM-DD
- [x] `test_releases_in_descending_version_order` — releases triées newest-first (0.1.2, 0.1.1, 0.1.0)

**`TestChangelogReleaseContent`** (6 tests — AC #1)
- [x] `test_each_release_has_at_least_one_change_type_label` — ≥ 3 labels `### Added/Changed/...`
- [x] `test_v012_documents_register_invariant` — v0.1.2 documente `register_invariant()`
- [x] `test_v012_documents_compliance_report` — v0.1.2 documente `ComplianceReport`
- [x] `test_v012_documents_final_api_surface` — v0.1.2 documente `physlink.__all__` 7 symboles
- [x] `test_v011_documents_dreamer_adapter` — v0.1.1 documente `DreamerV3Adapter`
- [x] `test_no_breaking_changes_in_v01x_releases` — pas de `⚠️ **Breaking:**` dans les releases v0.1.x
- [x] `test_breaking_change_format_documented_in_unreleased` — format breaking change documenté dans [Unreleased]

**`TestChangelogFooterLinks`** (7 tests — AC #1)
- [x] `test_unreleased_footer_link_present` — lien `[Unreleased]:` présent
- [x] `test_v012_footer_link_present` — lien `[0.1.2]:` présent
- [x] `test_v011_footer_link_present` — lien `[0.1.1]:` présent
- [x] `test_v010_footer_link_present` — lien `[0.1.0]:` présent
- [x] `test_footer_links_use_consistent_org_placeholder` — placeholder `YOUR-ORG/physlink` cohérent
- [x] `test_unreleased_footer_link_points_to_head` — lien [Unreleased] pointe vers `...HEAD`
- [x] `test_v010_footer_link_points_to_tag` — lien [0.1.0] pointe vers `releases/tag/v0.1.0`

**`TestDocsChangelogMirror`** (5 tests — Task 6)
- [x] `test_docs_changelog_exists` — `docs/changelog.md` existe
- [x] `test_docs_changelog_has_mirror_note` — note "mirrors CHANGELOG.md" présente
- [x] `test_docs_changelog_has_same_three_releases` — ≥ 3 releases identiques dans docs/changelog.md
- [x] `test_docs_changelog_has_same_footer_links` — liens footer identiques dans les deux fichiers
- [x] `test_docs_changelog_not_placeholder` — texte placeholder "coming in Epic 5" supprimé

**`TestPyprojectVersion`** (2 tests — Task 5)
- [x] `test_pyproject_version_is_0_1_2` — `pyproject.toml` version = `"0.1.2"`
- [x] `test_package_runtime_version_matches_pyproject` — `physlink.__version__` == version pyproject.toml

---

## Gap découvert et corrigé

**Gap** : `src/physlink/__init__.py` contenait `__version__ = "0.1.0"` alors que `pyproject.toml` avait été mis à jour à `0.1.2`. Le bump de version Story 5.1 (Task 5) n'avait pas été répercuté dans `__init__.py`.

**Fix appliqué** : `src/physlink/__init__.py` ligne 3 : `__version__ = "0.1.0"` → `__version__ = "0.1.2"`

**Test qui l'a détecté** : `TestPyprojectVersion::test_package_runtime_version_matches_pyproject`

---

## Coverage

| Acceptance Criteria | Couverture |
|---|---|
| AC #1 — Format Keep a Changelog, ≥ 3 releases, labels, liens | ✅ Complète (22 tests) |
| AC #2 — PR template checkbox (Story 5.3) | Non automatisable à ce stade |
| AC #3 — Présence CHANGELOG.md (hard NO-GO) | ✅ Complète (2 tests) |
| Task 5 — pyproject.toml version 0.1.2 | ✅ Complète (2 tests) |
| Task 6 — docs/changelog.md miroir | ✅ Complète (5 tests) |

---

## Résultats

```
755 passed, 3 skipped — 0 regressions
34 nouveaux tests ajoutés (baseline Story 4.5 : 721 passed)
```
