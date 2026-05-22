"""Unit tests for render_triptych() — CPU only (no GPU required)."""

from __future__ import annotations

import pathlib

import numpy as np
import pytest


def _make_synthetic_frames(T: int = 20, obs_dims: int = 6) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    imagination = rng.standard_normal((T, obs_dims))
    real = rng.standard_normal((T, obs_dims))
    return imagination, real


def test_render_triptych_produces_gif_file(tmp_path: pathlib.Path) -> None:
    from physlink.utils.visualization import render_triptych

    imagination, real = _make_synthetic_frames()
    render_triptych(imagination, real, str(tmp_path / "out.gif"))
    assert (tmp_path / "out.gif").exists()


def test_render_triptych_returns_absolute_path(tmp_path: pathlib.Path) -> None:
    from physlink.utils.visualization import render_triptych

    imagination, real = _make_synthetic_frames()
    result = render_triptych(imagination, real, str(tmp_path / "out.gif"))
    assert result == str((tmp_path / "out.gif").resolve())


def test_render_triptych_output_is_valid_gif(tmp_path: pathlib.Path) -> None:
    from PIL import Image

    from physlink.utils.visualization import render_triptych

    imagination, real = _make_synthetic_frames()
    out = str(tmp_path / "out.gif")
    render_triptych(imagination, real, out)
    img = Image.open(out)
    assert img.format == "GIF"


def test_render_triptych_different_inputs_produce_different_output(tmp_path: pathlib.Path) -> None:
    from physlink.utils.visualization import render_triptych

    rng1 = np.random.default_rng(1)
    rng2 = np.random.default_rng(99)
    # Clearly different data: large vs tiny values produce visually different plots
    data1_imagination = rng1.standard_normal((20, 6)) * 100.0
    data1_real = rng1.standard_normal((20, 6)) * 100.0
    data2_imagination = rng2.standard_normal((20, 6)) * 0.0001
    data2_real = rng2.standard_normal((20, 6)) * 0.0001

    out1 = str(tmp_path / "out1.gif")
    out2 = str(tmp_path / "out2.gif")
    render_triptych(data1_imagination, data1_real, out1)
    render_triptych(data2_imagination, data2_real, out2)

    size1 = (tmp_path / "out1.gif").stat().st_size
    size2 = (tmp_path / "out2.gif").stat().st_size
    assert size1 != size2


def test_from_scratch_baseline_constants_are_documented() -> None:
    from physlink.utils.visualization import (
        _FROM_SCRATCH_BASELINE_LABEL,
        _FROM_SCRATCH_BASELINE_SECONDS,
    )

    assert isinstance(_FROM_SCRATCH_BASELINE_SECONDS, float)
    assert _FROM_SCRATCH_BASELINE_SECONDS > 0
    assert isinstance(_FROM_SCRATCH_BASELINE_LABEL, str)
    assert len(_FROM_SCRATCH_BASELINE_LABEL) > 0


def test_render_triptych_idempotent(tmp_path: pathlib.Path) -> None:
    from PIL import Image

    from physlink.utils.visualization import render_triptych

    imagination, real = _make_synthetic_frames()
    out = str(tmp_path / "out.gif")
    render_triptych(imagination, real, out)
    render_triptych(imagination, real, out)  # second call overwrites without error
    img = Image.open(out)
    assert img.format == "GIF"


def test_render_triptych_under_10_seconds(tmp_path: pathlib.Path) -> None:
    """NFR-06: triptych render must complete in < 10 seconds."""
    import time

    from physlink.utils.visualization import render_triptych

    imagination, real = _make_synthetic_frames()
    start = time.monotonic()
    render_triptych(imagination, real, str(tmp_path / "out.gif"))
    elapsed = time.monotonic() - start
    assert elapsed < 10.0, (
        f"render_triptych NFR-06 violation: {elapsed:.2f}s (limit: 10.0s)\n"
        f"  Got:      {elapsed:.2f}s\n"
        f"  Expected: < 10.0s (NFR-06)\n"
        f"  Fix:      investigate render_triptych for unexpected blocking operations"
    )


def test_from_scratch_baseline_seconds_is_72_hours() -> None:
    """AC #2: from-scratch baseline must be traceable to the documented 72-hour value."""
    from physlink.utils.visualization import _FROM_SCRATCH_BASELINE_SECONDS

    assert _FROM_SCRATCH_BASELINE_SECONDS == 72.0 * 3600.0, (
        f"_FROM_SCRATCH_BASELINE_SECONDS must equal 72 hours (259200.0s), "
        f"got {_FROM_SCRATCH_BASELINE_SECONDS}"
    )


def test_render_triptych_accepts_list_input(tmp_path: pathlib.Path) -> None:
    """render_triptych must accept plain Python lists (converted via np.asarray)."""
    from physlink.utils.visualization import render_triptych

    imagination = [[float(i + j) for j in range(6)] for i in range(20)]
    real = [[float(i - j) * 0.1 for j in range(6)] for i in range(20)]
    out = str(tmp_path / "out.gif")
    render_triptych(imagination, real, out)
    assert (tmp_path / "out.gif").exists()
