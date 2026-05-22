"""Domain Scientist Colab notebook content validation — Story 6.3.

Validates that notebooks/domain-scientist-colab.ipynb satisfies the acceptance
criteria: 8-cell structure, installation error guard, single '⚠️ Edit this cell'
marker in Cell 3 only, register_invariant + compliance_report in Cell 5,
report.plot() in Cell 6, and domain_extension.md GitHub link in Cell 8.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
NOTEBOOK = PROJECT_ROOT / "notebooks" / "domain-scientist-colab.ipynb"


def _nb() -> dict:
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def cell_source(cell: dict) -> str:
    src = cell["source"]
    return "".join(src) if isinstance(src, list) else src


class TestNotebookStructure:
    """notebooks/domain-scientist-colab.ipynb must exist and have exactly 8 cells."""

    def test_notebook_exists(self) -> None:
        assert NOTEBOOK.exists(), (
            f"Missing: {NOTEBOOK}\n"
            "  Fix: create notebooks/domain-scientist-colab.ipynb"
        )

    def test_valid_json(self) -> None:
        try:
            _nb()
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"Notebook is not valid JSON: {exc}\n"
                "  Fix: ensure notebooks/domain-scientist-colab.ipynb is valid JSON"
            ) from exc

    def test_exactly_8_cells(self) -> None:
        nb = _nb()
        assert len(nb["cells"]) == 8, (
            f"Got: {len(nb['cells'])} cells\n"
            "  Expected: exactly 8 cells\n"
            "  Fix: add or remove cells to reach 8 total"
        )

    def test_nbformat_4(self) -> None:
        nb = _nb()
        assert nb.get("nbformat") == 4, (
            f"Got nbformat={nb.get('nbformat')}\n"
            "  Fix: set nbformat to 4 in notebook metadata"
        )

    def test_nbformat_minor_5(self) -> None:
        nb = _nb()
        assert nb.get("nbformat_minor") == 5, (
            f"Got nbformat_minor={nb.get('nbformat_minor')}\n"
            "  Fix: set nbformat_minor to 5 in notebook metadata"
        )

    def test_colab_provenance_metadata(self) -> None:
        nb = _nb()
        assert "colab" in nb.get("metadata", {}), (
            "metadata.colab not found in notebook\n"
            "  Fix: add 'colab': {'provenance': []} to notebook metadata"
        )

    def test_python3_kernel(self) -> None:
        nb = _nb()
        kernelspec = nb.get("metadata", {}).get("kernelspec", {})
        assert kernelspec.get("name") == "python3", (
            f"Got kernelspec.name={kernelspec.get('name')!r}\n"
            "  Fix: set kernelspec.name to 'python3' in notebook metadata"
        )


class TestCell1InstallWithErrorGuard:
    """AC #1: Cell 1 must pip install physlink with explicit error guard."""

    def test_cell1_is_code_cell(self) -> None:
        cell = _nb()["cells"][0]
        assert cell["cell_type"] == "code", (
            f"Cell 1 (index 0) type is {cell['cell_type']!r}\n"
            "  Fix: Cell 1 must be a code cell"
        )

    def test_cell1_has_pip_install(self) -> None:
        src = cell_source(_nb()["cells"][0])
        assert "physlink" in src and ("pip" in src or "install" in src), (
            "Cell 1 (index 0) must install physlink via pip\n"
            "  Fix: use subprocess.run([sys.executable, '-m', 'pip', 'install', 'physlink==...']) in Cell 1"
        )

    def test_cell1_has_error_guard(self) -> None:
        src = cell_source(_nb()["cells"][0])
        assert "RuntimeError" in src or "returncode" in src, (
            "Cell 1 must include an error guard (returncode check + RuntimeError)\n"
            "  Fix: use subprocess.run() and check returncode != 0, raise RuntimeError on failure"
        )

    def test_cell1_no_silent_failure(self) -> None:
        """The !pip install magic command silently ignores failures — must not be used."""
        src = cell_source(_nb()["cells"][0])
        assert "!pip install" not in src, (
            "Cell 1 uses '!pip install' which silently ignores failures\n"
            "  Fix: use subprocess.run() to capture exit code and raise RuntimeError on failure"
        )

    def test_cell1_physlink_could_not_be_installed_message(self) -> None:
        src = cell_source(_nb()["cells"][0])
        assert "physlink could not be installed" in src, (
            "Cell 1 must include exact error message: "
            "'physlink could not be installed — check the version number or PyPI availability'\n"
            "  Fix: add the exact message to the RuntimeError in Cell 1"
        )


class TestCell2Imports:
    """Cell 2 must import the 4 required physlink symbols."""

    def test_cell2_is_code_cell(self) -> None:
        cell = _nb()["cells"][1]
        assert cell["cell_type"] == "code", (
            f"Cell 2 (index 1) type is {cell['cell_type']!r}\n"
            "  Fix: Cell 2 must be a code cell"
        )

    def test_cell2_imports_observationspace(self) -> None:
        src = cell_source(_nb()["cells"][1])
        assert "ObservationSpace" in src, (
            "Cell 2 must import ObservationSpace from physlink\n"
            "  Fix: add ObservationSpace to the import in Cell 2"
        )

    def test_cell2_imports_actionspace(self) -> None:
        src = cell_source(_nb()["cells"][1])
        assert "ActionSpace" in src, (
            "Cell 2 must import ActionSpace from physlink\n"
            "  Fix: add ActionSpace to the import in Cell 2"
        )

    def test_cell2_imports_dreamerv3adapter(self) -> None:
        src = cell_source(_nb()["cells"][1])
        assert "DreamerV3Adapter" in src, (
            "Cell 2 must import DreamerV3Adapter from physlink\n"
            "  Fix: add DreamerV3Adapter to the import in Cell 2"
        )

    def test_cell2_imports_register_invariant(self) -> None:
        src = cell_source(_nb()["cells"][1])
        assert "register_invariant" in src, (
            "Cell 2 must import register_invariant from physlink\n"
            "  Fix: add register_invariant to the import in Cell 2"
        )


class TestCell3EditInstruction:
    """AC #2: Cell 3 must have the '⚠️ Edit this cell' marker — and only Cell 3."""

    def test_cell3_is_code_cell(self) -> None:
        cell = _nb()["cells"][2]
        assert cell["cell_type"] == "code", (
            f"Cell 3 (index 2) type is {cell['cell_type']!r}\n"
            "  Fix: Cell 3 must be a code cell"
        )

    def test_cell3_has_warning_emoji(self) -> None:
        src = cell_source(_nb()["cells"][2])
        assert "⚠️" in src, (
            "Cell 3 (index 2) must contain the '⚠️' warning emoji\n"
            "  Fix: first line of Cell 3 must be '# ⚠️ Edit this cell — this is the ONLY cell you need to modify'"
        )

    def test_cell3_has_edit_marker(self) -> None:
        src = cell_source(_nb()["cells"][2])
        assert "Edit this cell" in src, (
            "Cell 3 (index 2) must contain 'Edit this cell'\n"
            "  Fix: add '# ⚠️ Edit this cell' comment as the first line of Cell 3"
        )

    def test_edit_marker_only_in_cell3(self) -> None:
        cells = _nb()["cells"]
        edit_cells = [
            i for i, c in enumerate(cells)
            if "edit this cell" in cell_source(c).lower()
        ]
        assert edit_cells == [2], (
            f"'Edit this cell' found in cells at indices: {edit_cells}\n"
            "  Expected: only cell at index 2\n"
            "  Fix: remove 'Edit this cell' from all cells except index 2"
        )

    def test_cell3_has_your_trajectories(self) -> None:
        src = cell_source(_nb()["cells"][2])
        assert "your_trajectories" in src, (
            "Cell 3 must define the 'your_trajectories' variable\n"
            "  Fix: add 'your_trajectories = [...]' in Cell 3"
        )

    def test_cell3_uses_fixed_seed(self) -> None:
        src = cell_source(_nb()["cells"][2])
        assert "default_rng(42)" in src or "seed(42)" in src or "seed = 42" in src or "rng(42)" in src, (
            "Cell 3 must use a fixed random seed for idempotent example data\n"
            "  Fix: use numpy.random.default_rng(42) for reproducible trajectories"
        )


class TestCell4SpaceSetup:
    """Cell 4 must set up ObservationSpace and ActionSpace (stateless setup)."""

    def test_cell4_is_code_cell(self) -> None:
        cell = _nb()["cells"][3]
        assert cell["cell_type"] == "code", (
            f"Cell 4 (index 3) type is {cell['cell_type']!r}\n"
            "  Fix: Cell 4 must be a code cell"
        )

    def test_cell4_has_from_proprioception(self) -> None:
        src = cell_source(_nb()["cells"][3])
        assert "from_proprioception" in src, (
            "Cell 4 must call ObservationSpace.from_proprioception()\n"
            "  Fix: add 'ObservationSpace.from_proprioception(joints=7, include_velocity=True)' to Cell 4"
        )

    def test_cell4_has_actionspace_continuous(self) -> None:
        src = cell_source(_nb()["cells"][3])
        assert "ActionSpace.continuous" in src, (
            "Cell 4 must call ActionSpace.continuous()\n"
            "  Fix: add 'ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)' to Cell 4"
        )


class TestCell5ComplianceValidation:
    """AC #3: Cell 5 must register invariant, fit adapter, and print compliance report."""

    def test_cell5_is_code_cell(self) -> None:
        cell = _nb()["cells"][4]
        assert cell["cell_type"] == "code", (
            f"Cell 5 (index 4) type is {cell['cell_type']!r}\n"
            "  Fix: Cell 5 must be a code cell"
        )

    def test_cell5_has_register_invariant(self) -> None:
        src = cell_source(_nb()["cells"][4])
        assert "register_invariant(" in src, (
            "Cell 5 must call register_invariant()\n"
            "  Fix: add register_invariant() call to Cell 5"
        )

    def test_cell5_has_compliance_report(self) -> None:
        src = cell_source(_nb()["cells"][4])
        assert "compliance_report()" in src, (
            "Cell 5 must call adapter.compliance_report()\n"
            "  Fix: add 'report = adapter.compliance_report()' to Cell 5"
        )

    def test_cell5_has_print_summary(self) -> None:
        src = cell_source(_nb()["cells"][4])
        assert "print(report.summary())" in src, (
            "Cell 5 must call print(report.summary())\n"
            "  Fix: add 'print(report.summary())' to Cell 5"
        )

    def test_cell5_has_mass_conservation(self) -> None:
        src = cell_source(_nb()["cells"][4])
        assert "mass_conservation" in src, (
            "Cell 5 must define or reference 'mass_conservation'\n"
            "  Fix: add mass_conservation function definition to Cell 5"
        )

    def test_cell5_creates_fresh_adapter(self) -> None:
        src = cell_source(_nb()["cells"][4])
        assert "DreamerV3Adapter" in src, (
            "Cell 5 must create a fresh adapter = DreamerV3Adapter(...) for idempotence\n"
            "  Fix: add 'adapter = DreamerV3Adapter(obs_space, act_space)' in Cell 5"
        )

    def test_cell5_calls_fit(self) -> None:
        src = cell_source(_nb()["cells"][4])
        assert "adapter.fit(" in src, (
            "Cell 5 must call adapter.fit(your_trajectories, ...)\n"
            "  Fix: add 'adapter.fit(your_trajectories, steps=100, ...)' to Cell 5"
        )


class TestCell6Histogram:
    """AC #4: Cell 6 must call report.plot() for inline histogram."""

    def test_cell6_is_code_cell(self) -> None:
        cell = _nb()["cells"][5]
        assert cell["cell_type"] == "code", (
            f"Cell 6 (index 5) type is {cell['cell_type']!r}\n"
            "  Fix: Cell 6 must be a code cell"
        )

    def test_cell6_has_report_plot(self) -> None:
        src = cell_source(_nb()["cells"][5])
        assert "report.plot(" in src, (
            "Cell 6 must call report.plot()\n"
            "  Fix: add 'report.plot(title=\"Mass Conservation Check\", show_threshold=True)' to Cell 6"
        )

    def test_cell6_has_show_threshold(self) -> None:
        src = cell_source(_nb()["cells"][5])
        assert "show_threshold=True" in src, (
            "Cell 6's report.plot() must include show_threshold=True\n"
            "  Fix: add show_threshold=True to the report.plot() call in Cell 6"
        )


class TestCell7Export:
    """Cell 7 must call adapter.export()."""

    def test_cell7_is_code_cell(self) -> None:
        cell = _nb()["cells"][6]
        assert cell["cell_type"] == "code", (
            f"Cell 7 (index 6) type is {cell['cell_type']!r}\n"
            "  Fix: Cell 7 must be a code cell"
        )

    def test_cell7_has_adapter_export(self) -> None:
        src = cell_source(_nb()["cells"][6])
        assert "adapter.export(" in src, (
            "Cell 7 must call adapter.export(path=...)\n"
            "  Fix: add 'adapter.export(path=\"./physlink_export/\")' to Cell 7"
        )


class TestCell8WhatsNext:
    """AC #5: Cell 8 must be markdown with domain_extension.md GitHub link."""

    def test_cell8_is_markdown_cell(self) -> None:
        cell = _nb()["cells"][7]
        assert cell["cell_type"] == "markdown", (
            f"Cell 8 (index 7) type is {cell['cell_type']!r}\n"
            "  Fix: Cell 8 must be a markdown cell"
        )

    def test_cell8_has_whats_next_heading(self) -> None:
        src = cell_source(_nb()["cells"][7])
        assert "What's next" in src or "What’s next" in src, (
            "Cell 8 must have a 'What's next?' heading\n"
            "  Fix: add '## What's next?' heading to Cell 8"
        )

    def test_cell8_has_domain_extension_link(self) -> None:
        src = cell_source(_nb()["cells"][7])
        assert "domain_extension.md" in src, (
            "Cell 8 must contain a link to 'domain_extension.md'\n"
            "  Fix: add the GitHub issue template link with 'domain_extension.md' to Cell 8"
        )

    def test_cell8_has_github_url(self) -> None:
        src = cell_source(_nb()["cells"][7])
        assert "github.com" in src, (
            "Cell 8 must contain a GitHub URL for the domain extension issue template\n"
            "  Fix: add 'https://github.com/YOUR-ORG/physlink/issues/new?template=domain_extension.md' to Cell 8"
        )

    def test_cell8_domain_extension_in_github_url(self) -> None:
        src = cell_source(_nb()["cells"][7])
        assert "github.com" in src and "domain_extension.md" in src, (
            "Cell 8 must have 'domain_extension.md' within a github.com URL\n"
            "  Fix: use 'https://github.com/YOUR-ORG/physlink/issues/new?template=domain_extension.md'"
        )


class TestIdempotenceContract:
    """AC #6: Notebook structure enforces idempotence (NFR-09)."""

    def test_cell3_fixed_seed_for_idempotence(self) -> None:
        """Cell 3 must use a fixed numpy seed so trajectories are identical on every run."""
        src = cell_source(_nb()["cells"][2])
        assert "default_rng(42)" in src, (
            "Cell 3 must use numpy.random.default_rng(42) for reproducible example data\n"
            "  Fix: replace random seed with 'numpy.random.default_rng(42)'"
        )

    def test_cell5_fresh_adapter_for_idempotence(self) -> None:
        """Cell 5 must create a fresh adapter (not reuse from Cell 4) to avoid doubling invariants."""
        src = cell_source(_nb()["cells"][4])
        assert "DreamerV3Adapter(obs_space, act_space)" in src, (
            "Cell 5 must create 'adapter = DreamerV3Adapter(obs_space, act_space)' for idempotence\n"
            "  Fix: never reuse the adapter from Cell 4 — always construct a fresh one in Cell 5"
        )

    def test_cell8_is_markdown_no_execution(self) -> None:
        """Markdown cells have no execution_count or outputs — inherently idempotent."""
        cell = _nb()["cells"][7]
        assert "execution_count" not in cell, (
            "Cell 8 (markdown) must not have an 'execution_count' field\n"
            "  Fix: remove execution_count from the markdown cell"
        )
        assert "outputs" not in cell, (
            "Cell 8 (markdown) must not have an 'outputs' field\n"
            "  Fix: remove outputs from the markdown cell"
        )

    def test_cell4_no_adapter_construction(self) -> None:
        """Cell 4 must NOT create a DreamerV3Adapter — fresh adapter must be in Cell 5 only.

        If Cell 4 constructed the adapter, re-running Cell 5 alone would call register_invariant()
        a second time on the existing adapter, doubling the registered invariants (NFR-09 violation).
        """
        src = cell_source(_nb()["cells"][3])
        assert "DreamerV3Adapter(" not in src, (
            "Cell 4 (index 3) must NOT instantiate DreamerV3Adapter\n"
            "  Cell 4 must only create obs_space and act_space (stateless objects)\n"
            "  Fix: move adapter = DreamerV3Adapter(...) to Cell 5 where it belongs"
        )

    def test_cell7_export_path(self) -> None:
        """Cell 7 export path must be ./physlink_export/ for idempotent overwrites."""
        src = cell_source(_nb()["cells"][6])
        assert "./physlink_export/" in src or "physlink_export" in src, (
            "Cell 7 must export to './physlink_export/' path\n"
            "  Fix: use adapter.export(path='./physlink_export/') in Cell 7"
        )


class TestNotebookFormat:
    """Validates nbformat 4.5 cell structure conventions (source as list, outputs field)."""

    def test_all_code_cells_have_outputs_field(self) -> None:
        """Every code cell must have an 'outputs' field (required by nbformat 4)."""
        cells = _nb()["cells"]
        for i, cell in enumerate(cells):
            if cell["cell_type"] == "code":
                assert "outputs" in cell, (
                    f"Code cell at index {i} is missing the 'outputs' field\n"
                    "  Fix: add '\"outputs\": []' to the code cell"
                )

    def test_source_is_list_of_strings(self) -> None:
        """All cells must store source as a list of strings (nbformat 4 convention)."""
        cells = _nb()["cells"]
        for i, cell in enumerate(cells):
            src = cell.get("source")
            assert isinstance(src, list), (
                f"Cell {i + 1} (index {i}) has source type {type(src).__name__!r}, expected list\n"
                "  Fix: use source as a JSON array of strings, e.g. [\"line 1\\n\", \"line 2\"]"
            )


class TestAC1Precision:
    """Precision tests for AC #1 — pip install error handling detail."""

    def test_cell1_specifies_version(self) -> None:
        """Cell 1 must pin the physlink version for reproducibility."""
        src = cell_source(_nb()["cells"][0])
        assert "physlink==" in src, (
            "Cell 1 must pin a specific physlink version (e.g., physlink==0.1.2)\n"
            "  Fix: use 'physlink==<version>' in the pip install command for reproducibility"
        )

    def test_cell1_uses_subprocess_run(self) -> None:
        """Cell 1 must use subprocess.run to capture exit code — no shell magic."""
        src = cell_source(_nb()["cells"][0])
        assert "subprocess.run(" in src, (
            "Cell 1 must use subprocess.run() to capture pip exit code\n"
            "  Fix: use subprocess.run([sys.executable, '-m', 'pip', 'install', 'physlink==...'])"
        )


class TestAC2Precision:
    """Precision tests for AC #2 — exact edit marker placement."""

    def test_cell3_first_line_is_edit_marker(self) -> None:
        """Cell 3's first source line must BE the edit marker (not buried in the cell)."""
        src = cell_source(_nb()["cells"][2])
        first_line = src.split("\n")[0]
        assert "Edit this cell" in first_line, (
            f"Cell 3 first line is: {first_line!r}\n"
            "  Expected: first line contains 'Edit this cell'\n"
            "  Fix: '# ⚠️ Edit this cell — this is the ONLY cell you need to modify' must be line 1"
        )


class TestAC3Precision:
    """Precision tests for AC #3 — register_invariant signature and fit parameters."""

    def test_cell5_register_invariant_has_tolerance(self) -> None:
        """register_invariant call must include tolerance= parameter."""
        src = cell_source(_nb()["cells"][4])
        assert "tolerance=" in src, (
            "Cell 5's register_invariant() must include the tolerance= parameter\n"
            "  Fix: add tolerance=0.01 (or appropriate value) to the register_invariant call"
        )

    def test_cell5_register_invariant_has_mode(self) -> None:
        """register_invariant call must include mode= parameter."""
        src = cell_source(_nb()["cells"][4])
        assert "mode=" in src, (
            "Cell 5's register_invariant() must include the mode= parameter\n"
            "  Fix: add mode='hard' to the register_invariant call"
        )

    def test_cell5_fit_with_steps_100(self) -> None:
        """adapter.fit() must use steps=100 (sufficient for compliance, not full training)."""
        src = cell_source(_nb()["cells"][4])
        assert "steps=100" in src, (
            "Cell 5's adapter.fit() must use steps=100\n"
            "  100 steps validates compliance without the 45-min training wait (NFR-03 applies to Hugo's use case)\n"
            "  Fix: use adapter.fit(your_trajectories, steps=100, checkpoint_interval_steps=50)"
        )


class TestAC4Precision:
    """Precision tests for AC #4 — report.plot() title parameter."""

    def test_cell6_plot_has_correct_title(self) -> None:
        """report.plot() must use title='Mass Conservation Check'."""
        src = cell_source(_nb()["cells"][5])
        assert "Mass Conservation Check" in src, (
            "Cell 6's report.plot() must include title=\"Mass Conservation Check\"\n"
            "  Fix: use report.plot(title=\"Mass Conservation Check\", show_threshold=True)"
        )


class TestAC5Precision:
    """Precision tests for AC #5 — Cell 8 domain_extension.md link format."""

    def test_cell8_link_uses_issues_new_template(self) -> None:
        """Cell 8 GitHub link must use the issues/new?template= URL format."""
        src = cell_source(_nb()["cells"][7])
        assert "issues/new?template=domain_extension.md" in src, (
            "Cell 8 GitHub link must use format: "
            "https://github.com/YOUR-ORG/physlink/issues/new?template=domain_extension.md\n"
            "  Fix: use the full issue creation URL with ?template=domain_extension.md query param"
        )
