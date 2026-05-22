"""DreamerV3 adapter for PhysLink."""

import contextlib
from collections.abc import Generator
from typing import Any

from physlink.core._types import TrajectoryBatch
from physlink.core.adapter import BaseAdapter
from physlink.core.exceptions import ConfigurationError
from physlink.core.spaces import ActionSpace, ObservationSpace

MIN_OBS_DIMS: int = 4   # DreamerV3 requires >= 4 observation dimensions
MIN_ACT_DIMS: int = 1   # at least 1 action dimension required

_HEALTH_WINDOW: int = 50
_HEALTH_BASELINE_STEPS: int = 10
_ANOMALY_MULTIPLIER: float = 2.0

_STAGE_NAMES: tuple[str, ...] = (
    "data_loading",
    "world_model_update",
    "actor_update",
    "critic_update",
)

_VIZ_SEQ_LEN: int = 50  # max steps used for triptych inference


class _DebugPanel:
    def __init__(self) -> None:
        self.stages: dict[str, str] = {name: "waiting..." for name in _STAGE_NAMES}

    def update_all(self, statuses: dict[str, str]) -> None:
        self.stages.update(statuses)

    def __rich__(self) -> Any:  # noqa: ANN401
        from rich.table import Table

        table = Table(
            title="[dim]Debug Hooks Panel[/dim]",
            show_header=True,
            box=None,
            padding=(0, 1),
        )
        table.add_column("Stage", style="dim", no_wrap=True)
        table.add_column("Status", no_wrap=True)
        for name, status in self.stages.items():
            label = name.replace("_", " ")
            if status == "OK":
                cell = "[bold green]OK[/bold green]"
            elif status == "waiting...":
                cell = "[dim]waiting...[/dim]"
            else:
                cell = f"[bold red]{status}[/bold red]"
            table.add_row(label, cell)
        return table


@contextlib.contextmanager
def _build_progress_bar(
    steps: int,
) -> Generator[tuple[Any, Any], None, None]:
    """Context manager yielding (progress, task_id) for the adaptation loop."""
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        ProgressColumn,
        SpinnerColumn,
        TextColumn,
        TimeRemainingColumn,
    )
    from rich.text import Text

    class _StepsPerSecColumn(ProgressColumn):
        def render(self, task: Any) -> Text:  # noqa: ANN401
            if task.speed is None:
                return Text("? step/s", style="dim")
            return Text(f"{task.speed:.1f} step/s", style="cyan")

    class _HealthColumn(ProgressColumn):
        def render(self, task: Any) -> Text:  # noqa: ANN401
            health = task.fields.get("health", "OK")
            style = "bold green" if health == "OK" else "bold red"
            return Text(health, style=style)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        TextColumn("•"),
        _StepsPerSecColumn(),
        TextColumn("•"),
        _HealthColumn(),
    ) as progress:
        task_id = progress.add_task(
            "[cyan]DreamerV3 adaptation",
            total=steps,
            health="OK",
        )
        yield progress, task_id


@contextlib.contextmanager
def _build_debug_layout(
    steps: int,
    panel: _DebugPanel,
) -> Generator[tuple[Any, Any], None, None]:
    """Context manager yielding (progress, task_id) with debug panel alongside."""
    from rich.console import Group
    from rich.live import Live
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        ProgressColumn,
        SpinnerColumn,
        TextColumn,
        TimeRemainingColumn,
    )
    from rich.text import Text

    class _StepsPerSecColumn(ProgressColumn):
        def render(self, task: Any) -> Text:  # noqa: ANN401
            if task.speed is None:
                return Text("? step/s", style="dim")
            return Text(f"{task.speed:.1f} step/s", style="cyan")

    class _HealthColumn(ProgressColumn):
        def render(self, task: Any) -> Text:  # noqa: ANN401
            health = task.fields.get("health", "OK")
            style = "bold green" if health == "OK" else "bold red"
            return Text(health, style=style)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        TextColumn("•"),
        _StepsPerSecColumn(),
        TextColumn("•"),
        _HealthColumn(),
    )
    task_id = progress.add_task(
        "[cyan]DreamerV3 adaptation",
        total=steps,
        health="OK",
    )

    with Live(Group(progress, panel), refresh_per_second=4):
        yield progress, task_id


def _save_checkpoint(
    model: Any,  # noqa: ANN401
    actor: Any,  # noqa: ANN401
    critic: Any,  # noqa: ANN401
    step: int,
    checkpoint_dir: str,
) -> str:
    import datetime
    import os

    from safetensors.torch import save_file

    import physlink

    os.makedirs(checkpoint_dir, exist_ok=True)
    filename = f"checkpoint_step_{step}.safetensors"
    path = os.path.join(checkpoint_dir, filename)
    tensors: dict[str, Any] = {}
    tensors.update({f"model.{k}": v for k, v in model.state_dict().items()})
    tensors.update({f"actor.{k}": v for k, v in actor.state_dict().items()})
    tensors.update({f"critic.{k}": v for k, v in critic.state_dict().items()})
    metadata = {
        "physlink_version": physlink.__version__,
        "adapter_class": "DreamerV3Adapter",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checkpoint_step": str(step),
    }
    save_file(tensors, path, metadata=metadata)
    print(f"[physlink] Checkpoint saved: {os.path.abspath(path)}")
    return path


def _check_checkpoint_metadata(path: str) -> dict[str, str]:
    from safetensors import safe_open

    import physlink
    from physlink.core.exceptions import CheckpointCorruptError, CheckpointVersionError

    try:
        with safe_open(path, framework="pt", device="cpu") as f:
            metadata = f.metadata()
    except Exception as exc:
        raise CheckpointCorruptError(
            f"Cannot open checkpoint: {path}\n"
            f"  Got:      {type(exc).__name__}: {exc}\n"
            f"  Expected: valid safetensors file\n"
            f"  Fix:      re-run adapter.fit() to generate a fresh checkpoint."
        )

    if metadata is None or "physlink_version" not in metadata:
        raise CheckpointCorruptError(
            f"Checkpoint metadata missing or incomplete: {path}\n"
            f"  Got:      metadata={metadata!r}\n"
            f"  Expected: metadata dict with key 'physlink_version'\n"
            f"  Fix:      re-run adapter.fit() to generate a fresh checkpoint."
        )

    checkpoint_version = metadata["physlink_version"]
    current_version = physlink.__version__
    cv_parts = checkpoint_version.split(".")
    cur_parts = current_version.split(".")
    if cv_parts[:2] != cur_parts[:2]:
        raise CheckpointVersionError(
            f"Checkpoint version incompatible: {path}\n"
            f"  Got:      checkpoint saved with physlink=={checkpoint_version}\n"
            f"  Expected: compatible version (same major.minor as {current_version})\n"
            f"  Fix:      re-run adapter.fit() to generate a fresh checkpoint.",
            checkpoint_version=checkpoint_version,
            current_version=current_version,
        )

    return metadata


def _share_panel(export_path: str) -> None:
    """Trigger the Colab share panel: copy notebook URL to clipboard.

    In Google Colab, copies the current notebook URL to the clipboard via
    Javascript. Outside Colab, prints a graceful fallback message.

    Args:
        export_path: Absolute path to the export directory. Shown in fallback
            message so collaborators know where to find the artifacts.

    Example:
        >>> _share_panel("./physlink_export")
        [physlink] Share panel: URL copy is only available in Google Colab.
        ...
    """
    try:
        import google.colab  # noqa: F401
        in_colab = True
    except ImportError:
        in_colab = False

    try:
        if in_colab:
            from IPython.display import Javascript, display
            display(Javascript(
                "navigator.clipboard.writeText(window.location.href)"
                ".then(() => console.log('[physlink] Notebook URL copied.'));"
            ))
            print("[physlink] Share panel: notebook URL copied to clipboard.")
            print(f"[physlink] Export path for collaborators: {export_path}")
        else:
            print(
                "[physlink] Share panel: URL copy is only available in Google Colab.\n"
                f"           To share your results, send the export directory: {export_path}"
            )
    except Exception as exc:
        print(f"[physlink] Share panel unavailable: {type(exc).__name__}")


class DreamerV3Adapter(BaseAdapter):
    """DreamerV3 adapter for physical simulation reinforcement learning.

    Validates space compatibility at construction time. Training, visualization,
    and export are deferred to fit() / visualize() / export() respectively.
    No model weights are loaded and no GPU is required at construction.

    Args:
        obs_space: Observation space with dims >= 4.
        act_space: Action space with dims >= 1.

    Raises:
        ConfigurationError: If obs_space.dims < 4 or act_space.dims < 1.

    Example:
        >>> from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
        >>> obs = ObservationSpace.from_proprioception(joints=7, include_velocity=True)
        >>> act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
        >>> adapter = DreamerV3Adapter(obs, act)
        >>> adapter.obs_space.dims
        14
    """

    def __init__(self, obs_space: ObservationSpace, act_space: ActionSpace) -> None:
        if obs_space.dims < MIN_OBS_DIMS:
            raise ConfigurationError(
                f"DreamerV3Adapter: incompatible obs_space.\n"
                f"  Got:      obs_space.dims={obs_space.dims}\n"
                f"  Expected: obs_space.dims >= {MIN_OBS_DIMS} (DreamerV3 minimum)\n"
                f"  Fix:      construct ObservationSpace with joints >= {MIN_OBS_DIMS}, "
                f"or use include_velocity=True to double the dimension count."
            )
        if act_space.dims < MIN_ACT_DIMS:
            raise ConfigurationError(
                f"DreamerV3Adapter: incompatible act_space.\n"
                f"  Got:      act_space.dims={act_space.dims}\n"
                f"  Expected: act_space.dims >= {MIN_ACT_DIMS}\n"
                f"  Fix:      construct ActionSpace with dims >= 1."
            )
        super().__init__(obs_space, act_space)
        self._model: Any | None = None
        self._actor: Any | None = None
        self._critic: Any | None = None
        self._loss_history: list[float] = []
        self._baseline_loss: float | None = None
        self._fit_elapsed_seconds: float | None = None
        self._triptych_path: str | None = None
        self._last_checkpoint_path: str | None = None

    def _initialize_model(self, device: Any) -> None:  # noqa: ANN401
        import torch.nn as nn

        obs_dims = self.obs_space.dims
        act_dims = self.act_space.dims
        hidden = 256
        latent = 256

        class _WorldModel(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.encoder = nn.Sequential(
                    nn.Linear(obs_dims, hidden), nn.ELU(),
                    nn.Linear(hidden, hidden), nn.ELU(),
                )
                self.gru = nn.GRUCell(hidden + act_dims, hidden)
                self.posterior = nn.Sequential(
                    nn.Linear(hidden + hidden, hidden), nn.ELU(),
                    nn.Linear(hidden, latent * 2),
                )
                self.prior = nn.Sequential(
                    nn.Linear(hidden, hidden), nn.ELU(),
                    nn.Linear(hidden, latent * 2),
                )
                self.decoder = nn.Sequential(
                    nn.Linear(hidden + latent, hidden), nn.ELU(),
                    nn.Linear(hidden, obs_dims),
                )
                self.reward_head = nn.Sequential(
                    nn.Linear(hidden + latent, hidden), nn.ELU(),
                    nn.Linear(hidden, 1),
                )

        class _Actor(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(hidden + latent, hidden), nn.ELU(),
                    nn.Linear(hidden, hidden), nn.ELU(),
                    nn.Linear(hidden, act_dims * 2),
                )

        class _Critic(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(hidden + latent, hidden), nn.ELU(),
                    nn.Linear(hidden, hidden), nn.ELU(),
                    nn.Linear(hidden, 1),
                )

        self._model = _WorldModel().to(device)
        self._actor = _Actor().to(device)
        self._critic = _Critic().to(device)

    def _reset_training_state(self) -> None:
        """Reset all mutable training state for a fresh fit() run (NFR-09)."""
        self._loss_history = []
        self._baseline_loss = None

    def load_checkpoint(self, path: str) -> None:
        """Load model weights from a safetensors checkpoint.

        Reads checkpoint metadata before loading weights for early detection
        of version incompatibility or file corruption.

        Args:
            path: Path to the .safetensors checkpoint file to load.

        Raises:
            CheckpointCorruptError: If the file is malformed, unreadable, or
                missing required metadata.
            CheckpointVersionError: If physlink_version in the checkpoint
                metadata is incompatible with the installed version
                (different major.minor component).

        Example:
            >>> adapter = DreamerV3Adapter(obs, act)
            >>> adapter.load_checkpoint("./physlink_checkpoints/checkpoint_step_1000.safetensors")
        """
        _check_checkpoint_metadata(path)

        import os

        import torch
        from safetensors.torch import load_file
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self._model is None:
            self._initialize_model(device)
        self._model.to(device)
        self._actor.to(device)
        self._critic.to(device)
        state_dict_all = load_file(path, device="cpu")
        model_sd = {
            k[len("model."):]: v for k, v in state_dict_all.items() if k.startswith("model.")
        }
        actor_sd = {
            k[len("actor."):]: v for k, v in state_dict_all.items() if k.startswith("actor.")
        }
        critic_sd = {
            k[len("critic."):]: v for k, v in state_dict_all.items() if k.startswith("critic.")
        }
        self._model.load_state_dict(model_sd)
        self._actor.load_state_dict(actor_sd)
        self._critic.load_state_dict(critic_sd)
        print(f"[physlink] Checkpoint loaded: {os.path.abspath(path)}")

    def _compute_health(self, loss: float) -> str:
        self._loss_history.append(loss)
        if len(self._loss_history) > _HEALTH_WINDOW:
            self._loss_history = self._loss_history[-_HEALTH_WINDOW:]

        if self._baseline_loss is None and len(self._loss_history) >= _HEALTH_BASELINE_STEPS:
            self._baseline_loss = (
                sum(self._loss_history[:_HEALTH_BASELINE_STEPS]) / _HEALTH_BASELINE_STEPS
            )

        if self._baseline_loss is None or self._baseline_loss <= 0:
            return "OK"

        current_avg = sum(self._loss_history) / len(self._loss_history)
        return "ANOMALY" if current_avg > _ANOMALY_MULTIPLIER * self._baseline_loss else "OK"

    def _training_step(self, batch: Any, device: Any) -> Any:  # noqa: ANN401
        import torch
        import torch.nn as nn

        obs_all, act_all = batch  # pre-processed tensors: (N, obs_dims), (N, act_dims)
        n = obs_all.shape[0]

        batch_size = 16
        seq_len = min(50, max(1, n))
        max_start = max(0, n - seq_len)

        starts = torch.randint(0, max_start + 1, (batch_size,)).tolist()
        obs_seq = torch.stack([obs_all[s: s + seq_len] for s in starts])
        act_seq = torch.stack([act_all[s: s + seq_len] for s in starts])

        b_size, t_steps, obs_d = obs_seq.shape
        gru_hidden = self._model.gru.hidden_size

        with torch.cuda.amp.autocast(enabled=(device.type == "cuda")):
            h_state = torch.zeros(b_size, gru_hidden, device=device)
            latents: list[Any] = []
            kl_losses: list[Any] = []
            recon_losses: list[Any] = []

            for t in range(t_steps):
                obs_t = obs_seq[:, t]
                act_t = act_seq[:, t]

                encoded = self._model.encoder(obs_t)
                gru_input = torch.cat([encoded, act_t], dim=-1)
                h_state = self._model.gru(gru_input, h_state)

                post_params = self._model.posterior(torch.cat([h_state, encoded], dim=-1))
                post_mean, post_log_std = post_params.chunk(2, dim=-1)
                post_std = post_log_std.clamp(-5, 2).exp()
                z = post_mean + post_std * torch.randn_like(post_std)
                latents.append(z)

                prior_params = self._model.prior(h_state)
                prior_mean, prior_log_std = prior_params.chunk(2, dim=-1)
                prior_std = prior_log_std.clamp(-5, 2).exp().clamp(min=1e-8)

                kl = 0.5 * (
                    (post_mean - prior_mean).pow(2) / prior_std.pow(2)
                    + (post_std / prior_std).pow(2)
                    - 1
                    - 2 * (post_std / prior_std).log()
                ).sum(-1).mean()
                kl_losses.append(kl)

                recon = self._model.decoder(torch.cat([h_state, z], dim=-1))
                recon_losses.append(nn.functional.mse_loss(recon, obs_t))

            wm_loss = torch.stack(recon_losses).mean() + 0.1 * torch.stack(kl_losses).mean()

            # Imagination rollout
            imagine_horizon = 15
            hidden_i = h_state.detach()
            latent_i = latents[-1].detach()

            imagined_values: list[Any] = []
            imagined_rewards: list[Any] = []

            for _ in range(imagine_horizon):
                actor_input = torch.cat([hidden_i, latent_i], dim=-1)
                actor_params = self._actor.net(actor_input)
                act_mean, act_log_std = actor_params.chunk(2, dim=-1)
                act_i = torch.tanh(
                    act_mean + act_log_std.clamp(-5, 2).exp() * torch.randn_like(act_mean)
                )

                enc_i = self._model.encoder(torch.zeros(b_size, obs_d, device=device))
                gru_in = torch.cat([enc_i, act_i], dim=-1)
                hidden_i = self._model.gru(gru_in, hidden_i)

                prior_p = self._model.prior(hidden_i)
                latent_i, _ = prior_p.chunk(2, dim=-1)

                critic_in = torch.cat([hidden_i, latent_i], dim=-1)
                imagined_values.append(self._critic.net(critic_in))
                imagined_rewards.append(
                    self._model.reward_head(torch.cat([hidden_i, latent_i], dim=-1))
                )

            # λ-returns (simplified)
            returns = imagined_values[-1].detach()
            for v, r in zip(reversed(imagined_values[:-1]), reversed(imagined_rewards[:-1])):
                returns = r + 0.99 * (0.95 * v + 0.05 * returns)

            actor_loss = -returns.mean()

            critic_in = torch.cat([h_state.detach(), latents[-1].detach()], dim=-1)
            critic_val = self._critic.net(critic_in)
            critic_loss = nn.functional.mse_loss(critic_val, returns.detach())

            total_loss = wm_loss + actor_loss + critic_loss

        return total_loss

    def fit(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
        steps: int,
        checkpoint_interval_steps: int = 1000,
        debug_hooks: bool = False,
        checkpoint_dir: str = "physlink_checkpoints",
    ) -> None:
        """Run the DreamerV3 adaptation loop with a live progress bar.

        Adapts the DreamerV3 world model to the provided trajectory data over
        ``steps`` gradient updates. Displays a rich progress bar in Colab output
        with step count, ETA, prediction health (OK/ANOMALY), and throughput.

        Calling fit() multiple times is safe: each call resets optimizer state
        and training history for a fresh run (NFR-09 idempotence).

        Args:
            trajectories: Trajectory dataset. list[dict] is silently converted
                to TrajectoryBatch. Each dict must contain at minimum "obs" and
                "action" keys with numpy-compatible values.
            steps: Total gradient steps to run. Must be > 0.
            checkpoint_interval_steps: Interval (in steps) between checkpoint
                saves. A checkpoint file is written every this many steps. Must
                be > 0.
            debug_hooks: When True, displays a debug panel alongside the progress
                bar showing pipeline stage statuses (data_loading, world_model_update,
                actor_update, critic_update). Each stage shows OK or a diagnostic
                status. Defaults to False (opt-in, not default).
            checkpoint_dir: Directory where checkpoint files are written. Defaults
                to "physlink_checkpoints" relative to the current working directory.

        Raises:
            ValidationError: If steps <= 0 or checkpoint_interval_steps <= 0.

        Example:
            >>> from physlink import DreamerV3Adapter, ObservationSpace, ActionSpace
            >>> obs = ObservationSpace.from_proprioception(joints=7)
            >>> act = ActionSpace.continuous(dims=7, bounds=[(-1.0, 1.0)] * 7)
            >>> adapter = DreamerV3Adapter(obs, act)
            >>> trajectories = [{"obs": [0.1] * 7, "action": [0.0] * 7}] * 100
            >>> adapter.fit(trajectories, steps=10, debug_hooks=True)
        """
        import time

        from physlink.core.exceptions import ValidationError

        if isinstance(steps, bool) or not isinstance(steps, int) or steps <= 0:
            raise ValidationError(
                f"DreamerV3Adapter.fit: invalid steps.\n"
                f"  Got:      steps={steps}\n"
                f"  Expected: steps > 0\n"
                f"  Fix:      provide a positive integer, e.g. steps=10000."
            )
        if (
            isinstance(checkpoint_interval_steps, bool)
            or not isinstance(checkpoint_interval_steps, int)
            or checkpoint_interval_steps <= 0
        ):
            raise ValidationError(
                f"DreamerV3Adapter.fit: invalid checkpoint_interval_steps.\n"
                f"  Got:      checkpoint_interval_steps={checkpoint_interval_steps}\n"
                f"  Expected: checkpoint_interval_steps > 0\n"
                f"  Fix:      provide a positive integer, e.g. checkpoint_interval_steps=1000."
            )

        if isinstance(trajectories, list):
            trajectories = TrajectoryBatch.from_list(trajectories)

        import torch

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if self._model is None:
            self._initialize_model(device)

        self._reset_training_state()

        # Pre-process trajectory data to tensors once
        raw_data = trajectories.data
        obs_all = torch.tensor(
            [d["obs"] for d in raw_data], dtype=torch.float32, device=device
        )
        act_raw = torch.tensor(
            [d["action"] for d in raw_data], dtype=torch.float32, device=device
        )

        # Align action dims to model's act_dims via zero-padding or truncation
        model_act_dims = self.act_space.dims
        if act_raw.shape[-1] < model_act_dims:
            pad = torch.zeros(
                act_raw.shape[0], model_act_dims - act_raw.shape[-1], device=device
            )
            act_all = torch.cat([act_raw, pad], dim=-1)
        elif act_raw.shape[-1] > model_act_dims:
            act_all = act_raw[:, :model_act_dims]
        else:
            act_all = act_raw

        tensor_batch = (obs_all, act_all)

        all_params = (
            list(self._model.parameters())
            + list(self._actor.parameters())
            + list(self._critic.parameters())
        )
        optimizer = torch.optim.Adam(all_params, lr=3e-4)
        scaler = torch.cuda.amp.GradScaler(enabled=(device.type == "cuda"))

        _fit_start_time = time.monotonic()

        if debug_hooks:
            debug_panel = _DebugPanel()
            with _build_debug_layout(steps, debug_panel) as (progress, task_id):
                for step_idx in range(steps):
                    stage_statuses = {name: "OK" for name in _STAGE_NAMES}
                    optimizer.zero_grad(set_to_none=True)
                    try:
                        loss = self._training_step(tensor_batch, device)
                    except Exception as exc:
                        for name in ("world_model_update", "actor_update", "critic_update"):
                            stage_statuses[name] = type(exc).__name__
                        debug_panel.update_all(stage_statuses)
                        raise
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(all_params, max_norm=100.0)
                    scaler.step(optimizer)
                    scaler.update()
                    debug_panel.update_all(stage_statuses)
                    progress.update(
                        task_id, advance=1, health=self._compute_health(loss.item())
                    )
                    completed = step_idx + 1
                    if completed % checkpoint_interval_steps == 0:
                        self._last_checkpoint_path = _save_checkpoint(
                            self._model, self._actor, self._critic,
                            completed, checkpoint_dir,
                        )
        else:
            with _build_progress_bar(steps) as (progress, task_id):
                for step_idx in range(steps):
                    optimizer.zero_grad(set_to_none=True)
                    loss = self._training_step(tensor_batch, device)
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(all_params, max_norm=100.0)
                    scaler.step(optimizer)
                    scaler.update()
                    progress.update(
                        task_id, advance=1, health=self._compute_health(loss.item())
                    )
                    completed = step_idx + 1
                    if completed % checkpoint_interval_steps == 0:
                        self._last_checkpoint_path = _save_checkpoint(
                            self._model, self._actor, self._critic,
                            completed, checkpoint_dir,
                        )

        self._fit_elapsed_seconds = time.monotonic() - _fit_start_time

    def explain(self) -> dict[str, Any]:
        """Return a metadata dict describing this adapter's space configuration.

        Returns:
            A JSON-serializable dict with keys: type, obs_space, act_space.

        Example:
            >>> adapter = DreamerV3Adapter(obs, act)
            >>> info = adapter.explain()
            >>> info["type"]
            'DreamerV3Adapter'
        """
        return {
            "type": "DreamerV3Adapter",
            "obs_space": self.obs_space.explain(),
            "act_space": self.act_space.explain(),
        }

    def visualize(
        self,
        trajectories: list[dict[str, Any]] | TrajectoryBatch,
        output_path: str = "physlink_triptych.gif",
    ) -> str:
        """Produce a triptych GIF comparing Imagination, Real, and Difference panels.

        Runs a single inference pass through the trained world model to produce
        reconstructed (Imagination) observations, then renders them alongside the
        real observations and the absolute difference as a 3-panel GIF.

        Prints a "Friday afternoon window" callout comparing elapsed adaptation
        time to the documented from-scratch baseline.

        Args:
            trajectories: Trajectory dataset to visualize. Uses the first trajectory
                for the panel rendering. list[dict] is silently converted to
                TrajectoryBatch. Each dict must contain at minimum an "obs" key.
            output_path: File path for the output GIF. Defaults to
                "physlink_triptych.gif" in the current working directory.

        Returns:
            Absolute path to the saved GIF file.

        Raises:
            AdapterError: If the model has not been initialized via fit() or
                load_checkpoint().

        Example:
            >>> adapter = DreamerV3Adapter(obs, act)
            >>> adapter.fit(trajectories, steps=1000)
            >>> path = adapter.visualize(trajectories)
            >>> print(path)  # absolute path to physlink_triptych.gif
        """
        from physlink.core.exceptions import AdapterError

        if self._model is None:
            raise AdapterError(
                "DreamerV3Adapter.visualize: model not initialized.\n"
                "  Got:      self._model is None\n"
                "  Expected: model weights loaded via fit() or load_checkpoint()\n"
                "  Fix:      call adapter.fit(trajectories, steps=N) before visualize()."
            )

        if isinstance(trajectories, list):
            trajectories = TrajectoryBatch.from_list(trajectories)

        import numpy as np
        import torch

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(device)

        obs_raw = [d["obs"] for d in trajectories.data[:_VIZ_SEQ_LEN]]
        obs_seq = torch.tensor(obs_raw, dtype=torch.float32, device=device)  # (T, obs_dims)

        with torch.no_grad():
            h_state = torch.zeros(1, self._model.gru.hidden_size, device=device)
            imagination_frames = []
            for t in range(obs_seq.shape[0]):
                obs_t = obs_seq[t : t + 1]  # shape (1, obs_dims)
                act_t = torch.zeros(1, self.act_space.dims, device=device)
                encoded = self._model.encoder(obs_t)
                gru_input = torch.cat([encoded, act_t], dim=-1)
                h_state = self._model.gru(gru_input, h_state)
                post_params = self._model.posterior(torch.cat([h_state, encoded], dim=-1))
                post_mean, _ = post_params.chunk(2, dim=-1)
                recon = self._model.decoder(torch.cat([h_state, post_mean], dim=-1))
                imagination_frames.append(recon.squeeze(0).cpu().numpy())

        imagination_np = np.stack(imagination_frames)  # (T, obs_dims)
        real_np = obs_seq.cpu().numpy()  # (T, obs_dims)

        from physlink.utils.visualization import (
            _FROM_SCRATCH_BASELINE_LABEL,
            _FROM_SCRATCH_BASELINE_SECONDS,
            render_triptych,
        )

        gif_path = render_triptych(imagination_np, real_np, output_path)
        self._triptych_path = gif_path
        print(f"[physlink] Triptych saved: {gif_path}")

        elapsed = self._fit_elapsed_seconds
        if elapsed is not None:
            elapsed_min = elapsed / 60
            baseline_hours = _FROM_SCRATCH_BASELINE_SECONDS / 3600
            speedup = _FROM_SCRATCH_BASELINE_SECONDS / max(elapsed, 1.0)
            print(
                f"[physlink] ⏱  Adaptation complete in {elapsed_min:.1f} min\n"
                f"           vs. from-scratch baseline ({_FROM_SCRATCH_BASELINE_LABEL}): "
                f"{baseline_hours:.0f}h\n"
                f"           Speedup: ~{speedup:.0f}x"
            )
        else:
            print(
                "[physlink] ⏱  Adaptation time not available "
                "(call fit() before visualize() to see the Friday afternoon window callout)"
            )

        return gif_path

    def export(self, path: str) -> dict[str, str]:
        """Export a complete artifact bundle to the specified directory.

        Copies the triptych GIF, writes a YAML configuration file, and writes
        a human-readable summary. Calls the share panel to copy the Colab
        notebook URL to the clipboard (Colab only; graceful fallback elsewhere).

        Args:
            path: Directory path for the exported artifacts. Created if it does
                not exist. Existing files in the directory are overwritten.

        Returns:
            dict with keys ``gif``, ``config``, ``summary`` mapping to the
            absolute paths of the respective exported files.

        Raises:
            AdapterError: If ``visualize()`` has not been called (no triptych
                available to export).

        Example:
            >>> adapter.fit(trajectories, steps=1000)
            >>> adapter.visualize(trajectories)
            >>> artifacts = adapter.export("./physlink_export")
            >>> artifacts["config"]  # absolute path to config.yaml
            '/abs/path/physlink_export/config.yaml'
        """
        import datetime
        import os
        import shutil

        import yaml

        from physlink.core.exceptions import AdapterError

        if self._triptych_path is None:
            raise AdapterError(
                "DreamerV3Adapter.export: no triptych available.\n"
                "  Got:      self._triptych_path is None\n"
                "  Expected: visualize() called before export()\n"
                "  Fix:      call adapter.visualize(trajectories) before adapter.export(path)."
            )

        os.makedirs(path, exist_ok=True)

        gif_dest = os.path.join(path, "triptych.gif")
        shutil.copy2(self._triptych_path, gif_dest)

        config = {
            "obs_space": self.obs_space.explain(),
            "act_space": self.act_space.explain(),
            "checkpoint_path": self._last_checkpoint_path,
        }
        yaml_path = os.path.join(path, "config.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        elapsed_min = (
            self._fit_elapsed_seconds / 60.0
            if self._fit_elapsed_seconds is not None
            else None
        )
        elapsed_str = f"{elapsed_min:.1f} min" if elapsed_min is not None else "N/A"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        summary_lines = [
            "physlink Export Summary",
            "=======================",
            "Adapter:          DreamerV3Adapter",
            f"obs_dims:         {self.obs_space.dims}",
            f"act_dims:         {self.act_space.dims}",
            f"Fit elapsed:      {elapsed_str}",
            f"Triptych GIF:     {os.path.abspath(self._triptych_path)}",
            f"Checkpoint:       {self._last_checkpoint_path or 'N/A'}",
            f"Exported at:      {timestamp}",
        ]
        summary_path = os.path.join(path, "summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")

        print(f"[physlink] Export complete: {os.path.abspath(path)}")
        print(f"[physlink]   GIF:     {os.path.abspath(gif_dest)}")
        print(f"[physlink]   Config:  {os.path.abspath(yaml_path)}")
        print(f"[physlink]   Summary: {os.path.abspath(summary_path)}")

        _share_panel(os.path.abspath(path))

        return {
            "gif": os.path.abspath(gif_dest),
            "config": os.path.abspath(yaml_path),
            "summary": os.path.abspath(summary_path),
        }

    def __repr__(self) -> str:
        return (
            f"DreamerV3Adapter("
            f"obs_dims={self.obs_space.dims}, "
            f"act_dims={self.act_space.dims})"
        )
