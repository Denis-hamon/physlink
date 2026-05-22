"""Visualization utilities for PhysLink.

Provides triptych GIF rendering for adaptation result visualization.
"""

from typing import Any

# From-scratch baseline: empirical measurement on Colab T4 GPU for a 7-DOF arm
# starting from random initialization with standard DreamerV3 hyperparameters.
# Source: internal benchmark (see docs/getting-started.md for methodology).
_FROM_SCRATCH_BASELINE_SECONDS: float = 72.0 * 3600.0  # 72 hours
_FROM_SCRATCH_BASELINE_LABEL: str = "7-DOF arm from random init"


def render_triptych(
    imagination: Any,  # noqa: ANN401
    real: Any,  # noqa: ANN401
    output_path: str,
) -> str:
    """Render a 3-panel triptych GIF: Imagination, Real, Difference.

    Creates a static single-frame GIF with three side-by-side matplotlib
    subplots. Each subplot plots all observation dimensions as line series
    over the time axis.

    Args:
        imagination: Predicted observations from the world model decoder.
            Array-like of shape (T, obs_dims). Will be converted via np.asarray().
        real: Ground-truth observations from the trajectory dataset.
            Array-like of shape (T, obs_dims). Must match imagination shape.
        output_path: Destination file path (including .gif extension).

    Returns:
        Absolute path to the saved GIF file.

    Example:
        >>> import numpy as np
        >>> imagination = np.random.randn(50, 7)
        >>> real = np.random.randn(50, 7)
        >>> path = render_triptych(imagination, real, "triptych.gif")
    """
    import io
    import os

    import matplotlib
    import numpy as np
    try:
        matplotlib.use("Agg")
    except Exception:  # already set or not configurable
        pass
    import matplotlib.pyplot as plt
    from PIL import Image

    imagination = np.asarray(imagination)
    real = np.asarray(real)
    difference = np.abs(imagination - real)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    titles = ["Imagination", "Real", "Difference"]
    for ax, data, title in zip(axes, [imagination, real, difference], titles):
        ax.plot(data)
        ax.set_title(title)
        ax.set_xlabel("Step")
        ax.set_ylabel("Observation")
        ax.legend([f"dim {i}" for i in range(data.shape[1])], fontsize="small")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=72, bbox_inches="tight")
    plt.close(fig)

    buf.seek(0)
    img = Image.open(buf).convert("P")
    img.save(output_path, format="GIF")

    return os.path.abspath(output_path)
