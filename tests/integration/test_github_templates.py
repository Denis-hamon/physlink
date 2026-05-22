"""GitHub PR and Issue Templates validation — Story 5.3.

Validates that all GitHub templates exist and satisfy the acceptance criteria:
PR template has CHANGELOG and Tests-pass checkboxes, issue templates are present,
domain_extension template guides domain scientists through the invariant contribution path.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PR_TEMPLATE = PROJECT_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
ISSUE_TEMPLATE_DIR = PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE"
BUG_REPORT = ISSUE_TEMPLATE_DIR / "bug_report.md"
FEATURE_REQUEST = ISSUE_TEMPLATE_DIR / "feature_request.md"
DOMAIN_EXTENSION = ISSUE_TEMPLATE_DIR / "domain_extension.md"


class TestPRTemplateExists:
    """AC #1: .github/PULL_REQUEST_TEMPLATE.md must exist."""

    def test_pr_template_file_exists(self) -> None:
        assert PR_TEMPLATE.exists(), (
            f"Expected {PR_TEMPLATE} to exist — create .github/PULL_REQUEST_TEMPLATE.md"
        )


class TestPRTemplateContent:
    """AC #1: PR template must contain advisory CHANGELOG and Tests-pass checkboxes."""

    def _text(self) -> str:
        return PR_TEMPLATE.read_text(encoding="utf-8")

    def test_contains_changelog_checkbox(self) -> None:
        text = self._text()
        assert "- [ ]" in text, "PR template must contain at least one checkbox (- [ ])"
        assert "CHANGELOG" in text, (
            "PR template must include a 'CHANGELOG updated' checkbox (AC #1)"
        )

    def test_contains_tests_pass_checkbox(self) -> None:
        text = self._text()
        lower = text.lower()
        assert "tests" in lower or "test" in lower, (
            "PR template must reference tests (e.g. 'Tests pass') as a checkbox (AC #1)"
        )


class TestIssueTemplatesExist:
    """AC #2: .github/ISSUE_TEMPLATE/ must contain bug_report.md and feature_request.md."""

    def test_bug_report_exists(self) -> None:
        assert BUG_REPORT.exists(), (
            f"Expected {BUG_REPORT} to exist — create .github/ISSUE_TEMPLATE/bug_report.md"
        )

    def test_feature_request_exists(self) -> None:
        assert FEATURE_REQUEST.exists(), (
            f"Expected {FEATURE_REQUEST} to exist — create .github/ISSUE_TEMPLATE/feature_request.md"
        )


class TestDomainExtensionTemplateExists:
    """AC #3: .github/ISSUE_TEMPLATE/domain_extension.md must exist."""

    def test_domain_extension_exists(self) -> None:
        assert DOMAIN_EXTENSION.exists(), (
            f"Expected {DOMAIN_EXTENSION} to exist — create .github/ISSUE_TEMPLATE/domain_extension.md"
        )


class TestDomainExtensionContent:
    """AC #3: domain_extension template must guide domain scientists through invariant contribution."""

    def _text(self) -> str:
        return DOMAIN_EXTENSION.read_text(encoding="utf-8")

    def test_contains_invariant_keyword(self) -> None:
        assert "invariant" in self._text().lower(), (
            "domain_extension.md must contain 'invariant' to guide users through the invariant function section (AC #3)"
        )

    def test_contains_pass_keyword(self) -> None:
        assert "PASS" in self._text(), (
            "domain_extension.md must reference 'PASS' as the expected ComplianceReport outcome (AC #3)"
        )

    def test_has_yaml_front_matter_with_name(self) -> None:
        text = self._text()
        assert text.startswith("---"), (
            "domain_extension.md must start with YAML front matter (---)"
        )
        assert "name:" in text, (
            "domain_extension.md YAML front matter must include a 'name:' field for the template picker (AC #3)"
        )
