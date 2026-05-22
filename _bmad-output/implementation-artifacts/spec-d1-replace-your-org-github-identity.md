---
title: 'D-1: Replace YOUR-ORG — Configure GitHub Identity'
type: 'chore'
created: '2026-05-22'
status: 'done'
route: 'one-shot'
---

## Intent

**Problem:** The codebase contained `YOUR-ORG` placeholders across 11 files (README, mkdocs.yml, CHANGELOG, docs, notebook), making every public-facing URL non-functional. The git remote was also unconfigured, blocking any push to GitHub.

**Approach:** Find-and-replace `YOUR-ORG` → `Denis-hamon` across all user-facing files, configure `git remote origin` to `https://github.com/Denis-hamon/physlink.git`, and patch 4 secondary issues caught by adversarial review (`<owner>` placeholders, stale TODO, BibTeX author name).

## Suggested Review Order

1. [README.md](../../../README.md) — badges and Colab buttons now point to real URLs
2. [mkdocs.yml](../../../mkdocs.yml) — `site_url`, `repo_url`, `repo_name` updated
3. [CHANGELOG.md](../../../CHANGELOG.md) — footer comparison links updated
4. [CONTRIBUTING.md](../../../CONTRIBUTING.md) — clone URL, PyPI owner, stale TODO removed
5. [docs/lab-adoption-guide.md](../../../docs/lab-adoption-guide.md) — BibTeX author fixed (`Hamon, Denis`)
6. [docs/domain-scientists.md](../../../docs/domain-scientists.md) — Colab CTA link updated
7. [docs/deployment-guide.md](../../../docs/deployment-guide.md) — GPU clone URL updated
8. [docs/index.md](../../../docs/index.md) — Colab links updated
9. [docs/development-guide.md](../../../docs/development-guide.md) — repo links updated
10. [docs/changelog.md](../../../docs/changelog.md) — mirror of CHANGELOG
11. [notebooks/domain-scientist-colab.ipynb](../../../notebooks/domain-scientist-colab.ipynb) — Cell 7 community link updated
