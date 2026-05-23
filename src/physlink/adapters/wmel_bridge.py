"""Bridge between PhysLink DreamerV3Adapter and the WMEL evaluation framework.

Install WMEL from source before using this module::

    pip install "git+https://github.com/Denis-hamon/world-model-eval-lab.git"
    # or:
    pip install "physlink[eval]"

Then import the bridge::

    from physlink.adapters.wmel_bridge import DreamerWMELAdapter
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from physlink.adapters.dreamer import DreamerV3Adapter

# Resolve WMEL base class at import time.
# Falls back to a stub so the module is importable even when wmel is absent.
try:
    from wmel.adapters.lewm_adapter_stub import (
        LeWMAdapterStub as _LeWMBase,  # type: ignore[import-not-found]
    )
    _WMEL_AVAILABLE = True
except ImportError:
    class _LeWMBase:  # type: ignore[no-redef]
        pass
    _WMEL_AVAILABLE = False


class DreamerWMELAdapter(_LeWMBase):  # type: ignore[misc]
    """Wraps a fitted DreamerV3Adapter to satisfy the WMEL LeWMAdapterStub interface.

    After training a :class:`~physlink.DreamerV3Adapter`, pass it to this class
    to evaluate it against any WMEL ``BenchmarkEnvironment``.

    Planning uses **random-shoot MPC in latent space**: at each call to
    :meth:`plan`, ``n_candidates`` random action sequences are sampled, rolled
    forward through the world model via :meth:`rollout`, and the sequence whose
    final latent state is closest (L2 in z-space) to the encoded goal is returned.

    Args:
        adapter: A fitted DreamerV3Adapter. ``fit()`` must have been called.
        n_candidates: Number of random candidate sequences evaluated per :meth:`plan` call.
            Higher values improve plan quality at the cost of latency. Default: 100.
        device: Torch device for inference. ``"cpu"`` is recommended for WMEL
            benchmarking (consistent with WMEL's CPU-only design). Default: ``"cpu"``.

    Raises:
        ImportError: If ``wmel`` is not installed.
        RuntimeError: If ``adapter.fit()`` has not been called yet.

    Example:
        >>> from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
        >>> from physlink.adapters.wmel_bridge import DreamerWMELAdapter
        >>> obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        >>> act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        >>> adapter = DreamerV3Adapter(obs, act)
        >>> # adapter.fit(trajectories, steps=5000)  # train first
        >>> # bridge = DreamerWMELAdapter(adapter, n_candidates=50)
    """

    def __init__(
        self,
        adapter: DreamerV3Adapter,
        n_candidates: int = 100,
        device: str = "cpu",
    ) -> None:
        if not _WMEL_AVAILABLE:
            raise ImportError(
                "wmel is required for the PhysLink-WMEL bridge.\n"
                "  Install: pip install "
                "'git+https://github.com/Denis-hamon/world-model-eval-lab.git'\n"
                "  Or:      pip install 'physlink[eval]'"
            )
        if adapter._model is None:
            raise RuntimeError(
                "DreamerWMELAdapter requires a fitted adapter — "
                "call adapter.fit() first."
            )

        self._adapter = adapter
        self._n_candidates = n_candidates

        import torch
        self._device = torch.device(device)
        self._model = adapter._model.to(self._device).eval()
        self._obs_dims: int = adapter.obs_space.dims
        self._act_dims: int = adapter.act_space.dims
        self._act_bounds: list[tuple[float, float]] = list(adapter.act_space.bounds)
        self._hidden: int = self._model.gru.hidden_size

    # ── PlannerPolicy required interface ──────────────────────────────────────

    @property
    def name(self) -> str:
        """Human-readable identifier used in WMEL scorecard reports."""
        return (
            f"physlink-dreamer"
            f"({self._obs_dims}obs,{self._act_dims}act,"
            f"n={self._n_candidates})"
        )

    # ── LeWMAdapterStub interface ─────────────────────────────────────────────

    def encode(self, observation: Any) -> dict[str, Any]:  # noqa: ANN401
        """Encode an observation into a latent state dict.

        Runs the GRU encoder on the observation (with a zero initial hidden state
        and zero action) and returns the posterior mean as the latent z-vector.

        Args:
            observation: Array-like of shape ``(obs_dims,)``.

        Returns:
            Dict with keys ``"h"`` (GRU hidden, shape ``(hidden,)``) and
            ``"z"`` (posterior mean, shape ``(hidden,)``), both 1-D ``torch.Tensor``.
        """
        import torch

        obs_t = self._to_obs_tensor(observation)  # (1, obs_dims)
        h = torch.zeros(1, self._hidden, device=self._device)

        with torch.no_grad():
            enc = self._model.encoder(obs_t)
            zero_act = torch.zeros(1, self._act_dims, device=self._device)
            h = self._model.gru(torch.cat([enc, zero_act], dim=-1), h)
            post_params = self._model.posterior(torch.cat([h, enc], dim=-1))
            z_mean, _ = post_params.chunk(2, dim=-1)

        return {"h": h.squeeze(0), "z": z_mean.squeeze(0)}

    def rollout(
        self,
        latent: dict[str, Any],
        actions: Sequence[Any],
    ) -> list[dict[str, Any]]:
        """Advance the world model through an action sequence in latent space.

        Uses the prior (imagination rollout) without real observations — identical
        to DreamerV3's latent imagination used during training.

        Args:
            latent: Starting latent dict from :meth:`encode` with keys ``"h"`` and ``"z"``.
            actions: Sequence of actions, each array-like of shape ``(act_dims,)``.

        Returns:
            List of latent dicts (one per step), each with ``"h"`` and ``"z"``.
        """
        import torch

        h = latent["h"].unsqueeze(0).to(self._device)  # (1, hidden)
        zero_obs = torch.zeros(1, self._obs_dims, device=self._device)
        results: list[dict[str, Any]] = []

        with torch.no_grad():
            for action in actions:
                act_t = self._to_act_tensor(action)  # (1, act_dims)
                enc_dummy = self._model.encoder(zero_obs)
                h = self._model.gru(torch.cat([enc_dummy, act_t], dim=-1), h)
                prior_params = self._model.prior(h)
                z_mean, _ = prior_params.chunk(2, dim=-1)
                results.append({"h": h.squeeze(0), "z": z_mean.squeeze(0)})

        return results

    def score(self, latent: dict[str, Any], goal_latent: dict[str, Any]) -> float:
        """L2 distance between the z-vectors of two latent states (lower = closer).

        Args:
            latent: Current latent dict with key ``"z"``.
            goal_latent: Goal latent dict with key ``"z"``.

        Returns:
            Float ≥ 0. Lower values indicate proximity to the goal in latent space.
        """
        import torch  # noqa: F401

        return float((latent["z"] - goal_latent["z"]).norm().item())

    def plan(
        self,
        observation: Any,  # noqa: ANN401
        goal: Any,  # noqa: ANN401
        horizon: int,
    ) -> list[Any]:
        """Return an action sequence using random-shoot MPC in latent space.

        Samples ``n_candidates`` random action sequences of length ``horizon``,
        rolls each forward via the world model prior, and returns the sequence
        whose final latent state scores lowest against the encoded goal.

        Args:
            observation: Current observation, array-like of shape ``(obs_dims,)``.
            goal: Target observation, array-like of shape ``(obs_dims,)``.
            horizon: Maximum plan length. The returned list always has exactly
                ``horizon`` elements (≥ 1).

        Returns:
            List of ``horizon`` numpy arrays, each of shape ``(act_dims,)``.
        """
        if horizon <= 0:
            return []

        z0 = self.encode(observation)
        z_goal = self.encode(goal)

        best_actions = self._sample_action_sequence(horizon)
        best_score = float("inf")

        for _ in range(self._n_candidates):
            candidate = self._sample_action_sequence(horizon)
            trajectory = self.rollout(z0, candidate)
            s = self.score(trajectory[-1], z_goal)
            if s < best_score:
                best_score = s
                best_actions = candidate

        return best_actions

    # ── Private helpers ───────────────────────────────────────────────────────

    def _sample_action_sequence(self, length: int) -> list[Any]:
        import numpy as np

        rng = np.random.default_rng()
        return [
            np.array(
                [rng.uniform(lo, hi) for lo, hi in self._act_bounds],
                dtype=np.float32,
            )
            for _ in range(length)
        ]

    def _to_obs_tensor(self, observation: Any) -> Any:  # noqa: ANN401
        import numpy as np
        import torch

        if isinstance(observation, torch.Tensor):
            return observation.float().unsqueeze(0).to(self._device)
        return torch.from_numpy(
            np.asarray(observation, dtype=np.float32)
        ).unsqueeze(0).to(self._device)

    def _to_act_tensor(self, action: Any) -> Any:  # noqa: ANN401
        import numpy as np
        import torch

        if isinstance(action, torch.Tensor):
            return action.float().unsqueeze(0).to(self._device)
        return torch.from_numpy(
            np.asarray(action, dtype=np.float32)
        ).unsqueeze(0).to(self._device)
