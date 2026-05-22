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

    def test_contains_description_section(self) -> None:
        text = self._text()
        lower = text.lower()
        assert "description" in lower or "describe" in lower, (
            "PR template must include a description section (what the PR does — Task 1)"
        )

    def test_contains_breaking_change_checkbox(self) -> None:
        text = self._text()
        lower = text.lower()
        assert "breaking" in lower, (
            "PR template must include an optional 'Breaking change' checkbox (AC #1 / Task 1)"
        )


class TestIssueTemplatesExist:
    """AC #2: .github/ISSUE_TEMPLATE/ must contain bug_report.md and feature_request.md."""

    def test_issue_template_dir_exists(self) -> None:
        assert ISSUE_TEMPLATE_DIR.is_dir(), (
            f"Expected {ISSUE_TEMPLATE_DIR} to be a directory — GitHub requires this path"
        )

    def test_bug_report_exists(self) -> None:
        assert BUG_REPORT.exists(), (
            f"Expected {BUG_REPORT} to exist — create .github/ISSUE_TEMPLATE/bug_report.md"
        )

    def test_feature_request_exists(self) -> None:
        assert FEATURE_REQUEST.exists(), (
            f"Expected {FEATURE_REQUEST} to exist — create .github/ISSUE_TEMPLATE/feature_request.md"
        )


class TestBugReportContent:
    """AC #2: bug_report.md must have valid YAML front matter and required sections."""

    def _text(self) -> str:
        return BUG_REPORT.read_text(encoding="utf-8")

    def test_has_yaml_front_matter(self) -> None:
        text = self._text()
        assert text.startswith("---"), (
            "bug_report.md must start with YAML front matter (---) for GitHub to recognise it"
        )
        assert "name:" in text, (
            "bug_report.md YAML front matter must include a 'name:' field (Task 2)"
        )

    def test_has_describe_bug_section(self) -> None:
        lower = self._text().lower()
        assert "describe the bug" in lower or "bug" in lower, (
            "bug_report.md must include a 'Describe the bug' section (Task 2)"
        )

    def test_has_to_reproduce_section(self) -> None:
        lower = self._text().lower()
        assert "reproduce" in lower or "to reproduce" in lower, (
            "bug_report.md must include a 'To Reproduce' section with numbered steps (Task 2)"
        )

    def test_has_expected_behavior_section(self) -> None:
        lower = self._text().lower()
        assert "expected" in lower, (
            "bug_report.md must include an 'Expected behavior' section (Task 2)"
        )

    def test_has_environment_section(self) -> None:
        lower = self._text().lower()
        assert "environment" in lower or "python version" in lower or "platform" in lower, (
            "bug_report.md must include an 'Environment' section (physlink version, Python version, GPU — Task 2)"
        )


class TestFeatureRequestContent:
    """AC #2: feature_request.md must have valid YAML front matter and required sections."""

    def _text(self) -> str:
        return FEATURE_REQUEST.read_text(encoding="utf-8")

    def test_has_yaml_front_matter(self) -> None:
        text = self._text()
        assert text.startswith("---"), (
            "feature_request.md must start with YAML front matter (---) for GitHub to recognise it"
        )
        assert "name:" in text, (
            "feature_request.md YAML front matter must include a 'name:' field (Task 3)"
        )

    def test_has_problem_section(self) -> None:
        lower = self._text().lower()
        assert "problem" in lower or "related to" in lower, (
            "feature_request.md must include an 'Is your feature request related to a problem?' section (Task 3)"
        )

    def test_has_solution_section(self) -> None:
        lower = self._text().lower()
        assert "solution" in lower or "describe" in lower, (
            "feature_request.md must include a 'Describe the solution' section (Task 3)"
        )

    def test_has_alternatives_section(self) -> None:
        lower = self._text().lower()
        assert "alternative" in lower, (
            "feature_request.md must include a 'Describe alternatives you've considered' section (Task 3)"
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

    def test_has_yaml_about_field(self) -> None:
        text = self._text()
        assert "about:" in text, (
            "domain_extension.md YAML front matter must include an 'about:' field "
            "so the template description appears on the GitHub 'New Issue' page (AC #3)"
        )

    def test_has_physical_domain_section(self) -> None:
        lower = self._text().lower()
        assert "physical domain" in lower, (
            "domain_extension.md must include a 'Physical domain' section (AC #3 / Task 4)"
        )

    def test_has_invariant_fn_signature(self) -> None:
        text = self._text()
        assert "trajectory: dict" in text or "trajectory" in text, (
            "domain_extension.md must show the invariant fn signature "
            "'fn(trajectory: dict) -> float' expected by register_invariant() (Dev Notes / Task 4)"
        )

    def test_has_compliance_report_reference(self) -> None:
        text = self._text()
        assert "ComplianceReport" in text, (
            "domain_extension.md must reference ComplianceReport in the 'Expected PASS output' section (AC #3 / Task 4)"
        )

    def test_has_reference_literature_section(self) -> None:
        lower = self._text().lower()
        assert "reference" in lower or "literature" in lower, (
            "domain_extension.md must include a 'Reference literature' section (optional but encouraged — Task 4)"
        )
