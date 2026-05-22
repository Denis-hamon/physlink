"""README domain scientist link validation — Story 6.1.

Validates that README.md contains the 'For Domain Scientists' link entry
in the action bar (above-fold) pointing to docs/domain-scientists.md.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
README = PROJECT_ROOT / "README.md"


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


class TestDomainScientistLinkPresent:
    """Validates 'For Domain Scientists' link is in README (AC #1, #2)."""

    def test_link_text_present(self) -> None:
        assert "For Domain Scientists" in _readme_text(), (
            "'For Domain Scientists' not found in README.md.\n"
            "  Fix: add the third action bar entry pointing to docs/domain-scientists.md"
        )

    def test_link_target_present(self) -> None:
        assert "docs/domain-scientists.md" in _readme_text(), (
            "'docs/domain-scientists.md' link target not found in README.md.\n"
            "  Fix: ensure the action bar entry href is 'docs/domain-scientists.md'"
        )

    def test_target_file_exists(self) -> None:
        target = PROJECT_ROOT / "docs" / "domain-scientists.md"
        assert target.exists(), (
            "docs/domain-scientists.md does not exist on disk.\n"
            "  Fix: create the file or verify its path"
        )

    def test_link_inside_action_bar(self) -> None:
        text = _readme_text()
        action_bar_start = text.find('<p align="center">')
        action_bar_end = text.find("</p>", action_bar_start)
        assert action_bar_start != -1, (
            "No '<p align=\"center\">' action bar found in README.md.\n"
            "  Fix: ensure the action bar block exists"
        )
        action_bar_block = text[action_bar_start:action_bar_end]
        assert "For Domain Scientists" in action_bar_block, (
            "'For Domain Scientists' is not inside the '<p align=\"center\">' action bar.\n"
            "  Fix: add the third entry within the existing action bar block"
        )

    def test_link_appears_before_description(self) -> None:
        text = _readme_text()
        link_pos = text.find("For Domain Scientists")
        description_pos = text.find("Backend-agnostic adapter library")
        assert link_pos != -1, (
            "'For Domain Scientists' not found in README.md."
        )
        assert description_pos != -1, (
            "Description line 'Backend-agnostic adapter library' not found in README.md."
        )
        assert link_pos < description_pos, (
            "'For Domain Scientists' link appears after the description line.\n"
            "  Fix: ensure the action bar is above the description (above-fold placement)"
        )


class TestDomainScientistLinkFormat:
    """Validates exact HTML structure of the 'For Domain Scientists' action bar entry."""

    def _action_bar_block(self) -> str:
        text = _readme_text()
        start = text.find('<p align="center">')
        end = text.find("</p>", start)
        assert start != -1, "Action bar '<p align=\"center\">' not found in README.md"
        return text[start:end]

    def test_link_has_arrow_character(self) -> None:
        text = _readme_text()
        assert "For Domain Scientists →" in text, (
            "'For Domain Scientists →' (with arrow →) not found in README.md.\n"
            "  Fix: the action bar entry must use 'For Domain Scientists →' "
            "to match the UX convention of the other entries"
        )

    def test_link_uses_strong_formatting(self) -> None:
        block = self._action_bar_block()
        assert "<strong>For Domain Scientists" in block, (
            "Action bar entry is missing '<strong>' formatting around 'For Domain Scientists'.\n"
            "  Fix: wrap the link text in <strong>…</strong> "
            "like the other action bar entries"
        )

    def test_separator_between_evaluate_and_domain_scientists(self) -> None:
        block = self._action_bar_block()
        evaluate_pos = block.find("Evaluate for your lab")
        domain_pos = block.find("For Domain Scientists")
        assert evaluate_pos != -1 and domain_pos != -1, (
            "Both 'Evaluate for your lab' and 'For Domain Scientists' must be in the action bar"
        )
        between = block[evaluate_pos:domain_pos]
        assert "|" in between, (
            "No '|' separator found between 'Evaluate for your lab' and "
            "'For Domain Scientists' in the action bar.\n"
            "  Fix: add '&nbsp;&nbsp;|&nbsp;&nbsp;' between the second and third entries"
        )
