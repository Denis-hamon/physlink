"""README content validation — Story 1.6.

Validates that README.md satisfies the badge and dual-path action bar requirements
(UX-DR-01) without rendering in a browser or making network requests.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
README = PROJECT_ROOT / "README.md"


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


class TestReadmeStructure:
    """Structural README requirements: heading and one-line description (AC #1)."""

    def test_physlink_heading_present(self) -> None:
        assert "# PhysLink" in _readme_text(), (
            "PhysLink heading not found in README.md.\n"
            "  Expected: '# PhysLink' as the top-level H1 heading\n"
            "  Fix: ensure README.md begins with '# PhysLink'"
        )

    def test_description_line_present(self) -> None:
        assert "Backend-agnostic adapter library for physical simulation ML." in _readme_text(), (
            "Project description line not found in README.md.\n"
            "  Expected: 'Backend-agnostic adapter library for physical simulation ML.'\n"
            "  Fix: add the one-line description after the dual-path action bar"
        )


class TestReadmeBadgesExist:
    """AC #1: MIT, CI, arXiv badges must all be present in README."""

    def test_mit_badge_present(self) -> None:
        assert "shields.io/badge/License-MIT" in _readme_text(), (
            "MIT license badge not found in README.md.\n"
            "  Expected: shields.io/badge/License-MIT badge\n"
            "  Fix: add [![License: MIT](...shields.io/badge/License-MIT...)] to README"
        )

    def test_mit_badge_links_to_opensource_org(self) -> None:
        assert "opensource.org/licenses/MIT" in _readme_text(), (
            "MIT badge link target not found in README.md.\n"
            "  Expected: MIT badge links to opensource.org/licenses/MIT\n"
            "  Fix: use [![License: MIT](...)](https://opensource.org/licenses/MIT) format"
        )

    def test_ci_badge_present(self) -> None:
        assert "workflows/ci.yml/badge.svg" in _readme_text(), (
            "CI status badge not found in README.md.\n"
            "  Expected: GitHub Actions ci.yml badge\n"
            "  Fix: add CI badge pointing to .github/workflows/ci.yml to README"
        )

    def test_arxiv_badge_present(self) -> None:
        assert "shields.io/badge/arXiv" in _readme_text(), (
            "arXiv badge not found in README.md.\n"
            "  Expected: shields.io/badge/arXiv badge (placeholder or real)\n"
            "  Fix: add arXiv badge to README (use 'coming soon' placeholder if not submitted)"
        )


class TestReadmeColabButton:
    """AC #1: Open in Colab button must be present and link to quickstart.ipynb."""

    def test_open_in_colab_button_present(self) -> None:
        assert "colab.research.google.com" in _readme_text(), (
            "Open in Colab button not found in README.md.\n"
            "  Expected: colab.research.google.com URL\n"
            "  Fix: add [![Open In Colab](...colab-badge.svg)](...) to README"
        )

    def test_colab_badge_image_present(self) -> None:
        assert "colab-badge.svg" in _readme_text(), (
            "Colab badge image not found in README.md.\n"
            "  Expected: colab-badge.svg image in Open In Colab button\n"
            "  Fix: use [![Open In Colab](https://colab.research.google.com/"
            "assets/colab-badge.svg)](...) format"
        )

    def test_colab_links_to_quickstart_notebook(self) -> None:
        assert "quickstart.ipynb" in _readme_text(), (
            "quickstart.ipynb not referenced in README.md.\n"
            "  Expected: Colab button links to notebooks/quickstart.ipynb\n"
            "  Fix: Colab URL should include 'quickstart.ipynb' path"
        )


class TestReadmeDualPathActionBar:
    """AC #1: Both Quick Start and Evaluate for your lab must appear above fold."""

    def test_quick_start_link_present(self) -> None:
        assert "Quick Start" in _readme_text(), (
            "Quick Start action bar entry not found in README.md.\n"
            "  Expected: 'Quick Start →' link (Hugo's path)\n"
            "  Fix: add Quick Start link to README dual-path action bar"
        )

    def test_evaluate_for_lab_link_present(self) -> None:
        assert "Evaluate for your lab" in _readme_text(), (
            "'Evaluate for your lab' action bar entry not found in README.md.\n"
            "  Expected: 'Evaluate for your lab →' link (Petra's path)\n"
            "  Fix: add 'Evaluate for your lab' link to README dual-path action bar"
        )

    def test_lab_adoption_guide_linked(self) -> None:
        assert "lab-adoption-guide" in _readme_text(), (
            "Lab adoption guide not linked in README.md.\n"
            "  Expected: 'Evaluate for your lab →' links to docs/lab-adoption-guide.md\n"
            "  Fix: Petra's action bar link should point to docs/lab-adoption-guide.md"
        )

    def test_action_bar_separator_present(self) -> None:
        text = _readme_text()
        quick_pos = text.find("Quick Start")
        evaluate_pos = text.find("Evaluate for your lab")
        assert quick_pos != -1 and evaluate_pos != -1, (
            "Action bar entries not found — cannot verify separator"
        )
        start = min(quick_pos, evaluate_pos)
        end = max(quick_pos, evaluate_pos) + len("Evaluate for your lab")
        assert "|" in text[start:end], (
            "Dual-path action bar separator '|' not found between "
            "Quick Start and Evaluate entries.\n"
            "  Expected: both entries separated by '|' on the same line\n"
            "  Fix: add '|' (or '&nbsp;&nbsp;|&nbsp;&nbsp;') between the two action bar links"
        )


class TestReadmeArxivPlaceholder:
    """AC #2: arXiv badge must use a placeholder, not a real unsubmitted DOI."""

    def test_arxiv_placeholder_url_or_coming_soon(self) -> None:
        text = _readme_text()
        has_placeholder = "arxiv.org/abs/PLACEHOLDER" in text
        has_coming_soon = "coming%20soon" in text or "coming soon" in text.lower()
        assert has_placeholder or has_coming_soon, (
            "arXiv badge does not use a placeholder in README.md.\n"
            "  Expected: 'arxiv.org/abs/PLACEHOLDER' URL or 'coming soon' badge text\n"
            "  Fix: use placeholder arXiv badge until the paper is submitted to arXiv"
        )

    def test_no_false_live_arxiv_doi(self) -> None:
        text = _readme_text()
        live_arxiv = re.search(r"arxiv\.org/abs/\d{4}\.\d{4,5}", text)
        assert live_arxiv is None, (
            f"A real arXiv DOI pattern was found in README.md: "
            f"{live_arxiv.group() if live_arxiv else ''}\n"
            "  Got: a real-looking arXiv ID (digits like 2301.XXXXX)\n"
            "  Expected: placeholder 'PLACEHOLDER' text or 'coming soon' badge\n"
            "  Fix: do not add a real arXiv DOI until the paper is actually submitted and approved"
        )
