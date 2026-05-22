"""CHANGELOG content validation — Story 5.1.

Validates that CHANGELOG.md satisfies the Keep a Changelog format requirements
(UX-DR-07, AC #1, AC #3): ≥ 3 dated releases, correct format, change type labels,
footer comparison links, and docs/changelog.md mirror.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"
DOCS_CHANGELOG = PROJECT_ROOT / "docs" / "changelog.md"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"

RELEASE_HEADER_PATTERN = re.compile(r"^## \[\d+\.\d+\.\d+\] - \d{4}-\d{2}-\d{2}$", re.MULTILINE)
CHANGE_TYPE_PATTERN = re.compile(
    r"^### (Added|Changed|Deprecated|Removed|Fixed|Security)$", re.MULTILINE
)


def _changelog_text() -> str:
    return CHANGELOG.read_text(encoding="utf-8")


def _docs_changelog_text() -> str:
    return DOCS_CHANGELOG.read_text(encoding="utf-8")


def _pyproject_text() -> str:
    return PYPROJECT.read_text(encoding="utf-8")


class TestChangelogExistence:
    """AC #3: CHANGELOG.md must be present — hard NO-GO for institutional adoption (UX-DR-07)."""

    def test_changelog_exists_at_repo_root(self) -> None:
        assert CHANGELOG.exists(), (
            "CHANGELOG.md not found at repository root.\n"
            "  Expected: CHANGELOG.md adjacent to README.md and pyproject.toml\n"
            "  Fix: create CHANGELOG.md at repository root\n"
            "  Impact: absence is a hard NO-GO for institutional adoption (UX-DR-07)"
        )

    def test_changelog_is_not_empty(self) -> None:
        assert CHANGELOG.stat().st_size > 0, (
            "CHANGELOG.md is empty.\n"
            "  Expected: CHANGELOG.md with ≥ 3 dated release entries\n"
            "  Fix: populate CHANGELOG.md following Keep a Changelog format"
        )


class TestChangelogHeader:
    """AC #1: CHANGELOG.md must declare Keep a Changelog format and SemVer adherence."""

    def test_changelog_h1_heading_present(self) -> None:
        assert "# Changelog" in _changelog_text(), (
            "'# Changelog' heading not found in CHANGELOG.md.\n"
            "  Expected: '# Changelog' as the top-level H1 heading\n"
            "  Fix: ensure CHANGELOG.md begins with '# Changelog'"
        )

    def test_keep_a_changelog_reference_present(self) -> None:
        assert "keepachangelog.com" in _changelog_text(), (
            "Keep a Changelog reference not found in CHANGELOG.md.\n"
            "  Expected: 'The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)'\n"
            "  Fix: add format declaration to CHANGELOG.md header"
        )

    def test_semantic_versioning_reference_present(self) -> None:
        assert "semver.org" in _changelog_text(), (
            "Semantic Versioning reference not found in CHANGELOG.md.\n"
            "  Expected: 'this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)'\n"
            "  Fix: add SemVer declaration to CHANGELOG.md header"
        )

    def test_unreleased_section_present(self) -> None:
        assert "## [Unreleased]" in _changelog_text(), (
            "'## [Unreleased]' section not found in CHANGELOG.md.\n"
            "  Expected: '## [Unreleased]' section above versioned releases (for incremental updates)\n"
            "  Fix: add '## [Unreleased]' section at the top of release sections"
        )

    def test_unreleased_appears_before_first_versioned_release(self) -> None:
        text = _changelog_text()
        unreleased_pos = text.find("## [Unreleased]")
        first_release = RELEASE_HEADER_PATTERN.search(text)
        assert unreleased_pos != -1, "## [Unreleased] not found"
        assert first_release is not None, "No versioned release section found"
        assert unreleased_pos < first_release.start(), (
            "'## [Unreleased]' must appear before the first versioned release section.\n"
            "  Fix: move '## [Unreleased]' above '## [0.1.2]'"
        )


class TestChangelogReleases:
    """AC #1: at least 3 dated release entries in ## [X.Y.Z] - YYYY-MM-DD format."""

    def test_at_least_three_dated_releases(self) -> None:
        releases = RELEASE_HEADER_PATTERN.findall(_changelog_text())
        assert len(releases) >= 3, (
            f"CHANGELOG.md has {len(releases)} dated release(s); expected ≥ 3.\n"
            "  Expected: ## [0.1.0], ## [0.1.1], ## [0.1.2] (minimum)\n"
            "  Fix: add missing release sections in '## [X.Y.Z] - YYYY-MM-DD' format"
        )

    def test_release_v010_present(self) -> None:
        assert "## [0.1.0] - " in _changelog_text(), (
            "'## [0.1.0] - ...' not found in CHANGELOG.md.\n"
            "  Expected: initial v0.1.0 release (Epics 1+2: package scaffold, Space API)\n"
            "  Fix: add '## [0.1.0] - 2026-05-20' release section"
        )

    def test_release_v011_present(self) -> None:
        assert "## [0.1.1] - " in _changelog_text(), (
            "'## [0.1.1] - ...' not found in CHANGELOG.md.\n"
            "  Expected: v0.1.1 release (Epic 3: DreamerV3Adapter, adaptation loop)\n"
            "  Fix: add '## [0.1.1] - 2026-05-21' release section"
        )

    def test_release_v012_present(self) -> None:
        assert "## [0.1.2] - " in _changelog_text(), (
            "'## [0.1.2] - ...' not found in CHANGELOG.md.\n"
            "  Expected: v0.1.2 release (Epic 4: register_invariant, ComplianceReport)\n"
            "  Fix: add '## [0.1.2] - 2026-05-22' release section"
        )

    def test_all_release_dates_use_iso8601_format(self) -> None:
        text = _changelog_text()
        version_date_pairs = re.findall(r"^## \[[\d\.]+\] - (.+)$", text, re.MULTILINE)
        bad = [d for d in version_date_pairs if not re.match(r"^\d{4}-\d{2}-\d{2}$", d.strip())]
        assert not bad, (
            f"Release date(s) not in ISO 8601 YYYY-MM-DD format: {bad}\n"
            "  Fix: use '## [X.Y.Z] - YYYY-MM-DD' header format for all release entries"
        )

    def test_releases_in_descending_version_order(self) -> None:
        text = _changelog_text()
        versions = re.findall(r"^## \[(\d+\.\d+\.\d+)\] - ", text, re.MULTILINE)
        assert versions, "No versioned release headers found in CHANGELOG.md"
        parsed = [tuple(int(x) for x in v.split(".")) for v in versions]
        assert parsed == sorted(parsed, reverse=True), (
            f"Releases not in descending version order: {versions}\n"
            "  Expected: newest first (0.1.2, 0.1.1, 0.1.0)\n"
            "  Fix: reorder release sections so the newest appears at top"
        )


class TestChangelogReleaseContent:
    """AC #1: each release entry must contain a change type label (### Added etc.) and content."""

    def test_each_release_has_at_least_one_change_type_label(self) -> None:
        change_types = CHANGE_TYPE_PATTERN.findall(_changelog_text())
        assert len(change_types) >= 3, (
            f"Expected ≥ 3 change type labels (### Added / Changed / etc.), found {len(change_types)}.\n"
            "  Fix: add '### Added' (or other Keep a Changelog type) under each release section"
        )

    def test_v012_documents_register_invariant(self) -> None:
        assert "register_invariant" in _changelog_text(), (
            "'register_invariant' not found in CHANGELOG.md.\n"
            "  Expected: v0.1.2 documents the register_invariant() API addition (Epic 4)\n"
            "  Fix: add register_invariant entry to ## [0.1.2] release notes"
        )

    def test_v012_documents_compliance_report(self) -> None:
        assert "ComplianceReport" in _changelog_text(), (
            "'ComplianceReport' not found in CHANGELOG.md.\n"
            "  Expected: v0.1.2 documents the ComplianceReport class (Epic 4)\n"
            "  Fix: add ComplianceReport entry to ## [0.1.2] release notes"
        )

    def test_v012_documents_final_api_surface(self) -> None:
        assert "physlink.__all__" in _changelog_text(), (
            "'physlink.__all__' not documented in CHANGELOG.md.\n"
            "  Expected: v0.1.2 documents finalization of the 7-symbol stable public API\n"
            "  Fix: add physlink.__all__ = 7 symbols note to v0.1.2 release notes"
        )

    def test_v011_documents_dreamer_adapter(self) -> None:
        assert "DreamerV3Adapter" in _changelog_text(), (
            "'DreamerV3Adapter' not found in CHANGELOG.md.\n"
            "  Expected: v0.1.1 documents the DreamerV3Adapter addition (Epic 3)\n"
            "  Fix: add DreamerV3Adapter entry to ## [0.1.1] release notes"
        )

    def test_no_breaking_changes_in_v01x_releases(self) -> None:
        text = _changelog_text()
        first_release_match = RELEASE_HEADER_PATTERN.search(text)
        assert first_release_match is not None, "No versioned release found"
        versioned_section = text[first_release_match.start():]
        assert "⚠️ **Breaking:**" not in versioned_section, (
            "Breaking change marker found in v0.1.x release notes.\n"
            "  Got: '⚠️ **Breaking:**' in a versioned release section\n"
            "  Expected: all v0.1.0–v0.1.2 releases are purely additive (no breaking changes)\n"
            "  Fix: remove breaking change marker or move it to [Unreleased] section"
        )

    def test_breaking_change_format_documented_in_unreleased(self) -> None:
        text = _changelog_text()
        unreleased_pos = text.find("## [Unreleased]")
        first_release_match = RELEASE_HEADER_PATTERN.search(text)
        assert unreleased_pos != -1, "## [Unreleased] not found"
        assert first_release_match is not None, "No versioned release found"
        unreleased_block = text[unreleased_pos:first_release_match.start()]
        assert "Breaking" in unreleased_block, (
            "Breaking change format not documented in [Unreleased] block.\n"
            "  Expected: [Unreleased] block contains a comment showing ⚠️ **Breaking:** format\n"
            "  Fix: add a comment in [Unreleased] documenting the breaking change format for contributors"
        )


class TestChangelogFooterLinks:
    """AC #1: footer comparison links must be present and consistent."""

    def test_unreleased_footer_link_present(self) -> None:
        assert "[Unreleased]:" in _changelog_text(), (
            "[Unreleased]: footer link not found in CHANGELOG.md.\n"
            "  Expected: '[Unreleased]: https://github.com/.../compare/vX.Y.Z...HEAD'\n"
            "  Fix: add [Unreleased]: footer link at end of CHANGELOG.md"
        )

    def test_v012_footer_link_present(self) -> None:
        assert "[0.1.2]:" in _changelog_text(), (
            "[0.1.2]: footer link not found in CHANGELOG.md.\n"
            "  Fix: add '[0.1.2]: https://github.com/.../compare/v0.1.1...v0.1.2' footer link"
        )

    def test_v011_footer_link_present(self) -> None:
        assert "[0.1.1]:" in _changelog_text(), (
            "[0.1.1]: footer link not found in CHANGELOG.md.\n"
            "  Fix: add '[0.1.1]: https://github.com/.../compare/v0.1.0...v0.1.1' footer link"
        )

    def test_v010_footer_link_present(self) -> None:
        assert "[0.1.0]:" in _changelog_text(), (
            "[0.1.0]: footer link not found in CHANGELOG.md.\n"
            "  Fix: add '[0.1.0]: https://github.com/.../releases/tag/v0.1.0' footer link"
        )

    def test_footer_links_use_consistent_org_placeholder(self) -> None:
        text = _changelog_text()
        footer_start = text.rfind("[Unreleased]:")
        assert footer_start != -1, "[Unreleased]: footer link not found"
        footer_section = text[footer_start:]
        assert "YOUR-ORG" not in footer_section, (
            "CHANGELOG footer still contains the 'YOUR-ORG' template placeholder.\n"
            "  Fix: replace YOUR-ORG with the actual GitHub owner deploying this fork."
        )
        assert re.search(
            r"https://github\.com/[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?/physlink",
            footer_section,
        ), (
            "CHANGELOG footer must contain real 'https://github.com/<owner>/physlink' "
            "comparison links."
        )

    def test_unreleased_footer_link_points_to_head(self) -> None:
        text = _changelog_text()
        match = re.search(r"\[Unreleased\]:\s*(\S+)", text)
        assert match is not None, "[Unreleased]: footer link not found"
        url = match.group(1)
        assert url.endswith("HEAD"), (
            f"[Unreleased]: footer link does not end with 'HEAD': {url!r}\n"
            "  Expected: '[Unreleased]: https://github.com/.../compare/v0.1.2...HEAD'\n"
            "  Fix: update [Unreleased]: URL to end with '...HEAD'"
        )

    def test_v010_footer_link_points_to_tag(self) -> None:
        text = _changelog_text()
        match = re.search(r"\[0\.1\.0\]:\s*(\S+)", text)
        assert match is not None, "[0.1.0]: footer link not found"
        url = match.group(1)
        assert "releases/tag" in url, (
            f"[0.1.0]: footer link does not use releases/tag: {url!r}\n"
            "  Expected: '[0.1.0]: https://github.com/.../releases/tag/v0.1.0'\n"
            "  Fix: initial release should reference a git tag, not a compare URL"
        )


class TestDocsChangelogMirror:
    """Task 6: docs/changelog.md must mirror root CHANGELOG.md."""

    def test_docs_changelog_exists(self) -> None:
        assert DOCS_CHANGELOG.exists(), (
            "docs/changelog.md not found.\n"
            "  Expected: docs/changelog.md mirroring root CHANGELOG.md\n"
            "  Fix: update the docs/changelog.md placeholder with full CHANGELOG.md content"
        )

    def test_docs_changelog_has_mirror_note(self) -> None:
        text = _docs_changelog_text()
        has_mirror = "mirrors" in text.lower() or "mirror" in text.lower()
        has_changelog_ref = "CHANGELOG.md" in text
        assert has_mirror and has_changelog_ref, (
            "docs/changelog.md does not contain a mirror note referencing CHANGELOG.md.\n"
            "  Expected: note stating 'This page mirrors CHANGELOG.md at the project root'\n"
            "  Fix: add mirror note to top of docs/changelog.md"
        )

    def test_docs_changelog_has_same_three_releases(self) -> None:
        releases = RELEASE_HEADER_PATTERN.findall(_docs_changelog_text())
        assert len(releases) >= 3, (
            f"docs/changelog.md has {len(releases)} dated release(s); expected ≥ 3.\n"
            "  Expected: mirror of all 3 releases from root CHANGELOG.md\n"
            "  Fix: update docs/changelog.md to fully mirror root CHANGELOG.md"
        )

    def test_docs_changelog_has_same_footer_links(self) -> None:
        root_links = set(re.findall(r"^\[[\w\.]+\]:\s*\S+", _changelog_text(), re.MULTILINE))
        docs_links = set(re.findall(r"^\[[\w\.]+\]:\s*\S+", _docs_changelog_text(), re.MULTILINE))
        missing = root_links - docs_links
        assert not missing, (
            "docs/changelog.md is missing footer links present in root CHANGELOG.md:\n"
            + "\n".join(f"  {link}" for link in sorted(missing))
            + "\n  Fix: copy footer comparison links from CHANGELOG.md to docs/changelog.md"
        )

    def test_docs_changelog_not_placeholder(self) -> None:
        text = _docs_changelog_text()
        assert "coming in Epic 5" not in text, (
            "docs/changelog.md still contains placeholder 'coming in Epic 5' text.\n"
            "  Expected: full mirrored content replacing the placeholder\n"
            "  Fix: replace placeholder with complete CHANGELOG.md mirror"
        )


class TestPyprojectVersion:
    """Task 5: pyproject.toml version must be bumped to 0.1.2 after Story 5.1."""

    def test_pyproject_version_is_0_1_2(self) -> None:
        match = re.search(r'^version\s*=\s*"([^"]+)"', _pyproject_text(), re.MULTILINE)
        assert match is not None, (
            "version field not found in pyproject.toml.\n"
            "  Fix: ensure 'version = \"0.1.2\"' is set in the [project] section"
        )
        version = match.group(1)
        assert version == "0.1.2", (
            f"pyproject.toml version is {version!r}; expected '0.1.2'.\n"
            "  Fix: update to 'version = \"0.1.2\"' (v0.1.1 = Epic 3, v0.1.2 = Epic 4)"
        )

    def test_package_runtime_version_matches_pyproject(self) -> None:
        import physlink

        match = re.search(r'^version\s*=\s*"([^"]+)"', _pyproject_text(), re.MULTILINE)
        assert match is not None, "version not found in pyproject.toml"
        pyproject_version = match.group(1)
        assert physlink.__version__ == pyproject_version, (
            f"physlink.__version__ ({physlink.__version__!r}) does not match "
            f"pyproject.toml version ({pyproject_version!r}).\n"
            "  Fix: ensure physlink.__version__ is derived from importlib.metadata"
        )
