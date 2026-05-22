"""MkDocs hook: copy custom landing page to site root after build."""

from __future__ import annotations

import shutil
from pathlib import Path


def on_post_build(config: dict) -> None:
    landing = Path("landing") / "index.html"
    dest = Path(config["site_dir"]) / "index.html"
    if landing.exists():
        shutil.copy(landing, dest)
