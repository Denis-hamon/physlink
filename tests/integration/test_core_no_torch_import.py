"""AST guard: no torch import in src/physlink/core/.

Enforces NFR-08 (backend-agnostic core). Runs in test-cpu CI — no GPU required.
"""

from __future__ import annotations

import ast
from pathlib import Path


def get_core_files() -> list[Path]:
    core_dir = Path(__file__).parent.parent.parent / "src" / "physlink" / "core"
    return list(core_dir.rglob("*.py"))


def test_no_torch_import_in_core() -> None:
    torch_imports: list[str] = []
    for filepath in get_core_files():
        tree = ast.parse(filepath.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "torch" or alias.name.startswith("torch."):
                        torch_imports.append(f"{filepath}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and (node.module == "torch" or node.module.startswith("torch.")):
                    torch_imports.append(f"{filepath}: from {node.module} import ...")
    assert not torch_imports, "torch imports found in core/ (violates NFR-08):\n" + "\n".join(
        torch_imports
    )
