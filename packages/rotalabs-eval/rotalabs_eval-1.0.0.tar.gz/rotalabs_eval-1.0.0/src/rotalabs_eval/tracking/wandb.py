"""Weights & Biases integration for experiment tracking."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_wandb = None


def _get_wandb():
    global _wandb
    if _wandb is None:
        try:
            import wandb
            _wandb = wandb
        except ImportError:
            raise ImportError("wandb not installed. Install with: pip install rotalabs-eval[wandb]")
    return _wandb


class WandbTracker:
    """Weights & Biases experiment tracker."""

    def __init__(
        self,
        project: str,
        entity: Optional[str] = None,
        run_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None,
    ) -> None:
        self.project = project
        self.entity = entity
        self.run_name = run_name
        self.run_config = config or {}
        self.tags = tags or []
        self._run = None

    def start_run(self) -> None:
        """Initialize a W&B run."""
        wb = _get_wandb()
        self._run = wb.init(
            project=self.project,
            entity=self.entity,
            name=self.run_name,
            config=self.run_config,
            tags=self.tags,
        )

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """Log metrics to W&B."""
        if self._run is None:
            self.start_run()
        kwargs: Dict[str, Any] = {}
        if step is not None:
            kwargs["step"] = step
        self._run.log(metrics, **kwargs)

    def log_config(self, config: Dict[str, Any]) -> None:
        """Log config parameters."""
        if self._run is None:
            self.start_run()
        self._run.config.update(config)

    def log_artifact(self, data: Any, name: str, artifact_type: str = "result") -> None:
        """Log an artifact to W&B."""
        if self._run is None:
            self.start_run()
        import json
        import tempfile
        import os
        wb = _get_wandb()
        artifact = wb.Artifact(name, type=artifact_type)
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, f"{name}.json")
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
            artifact.add_file(filepath)
        self._run.log_artifact(artifact)

    def finish(self) -> None:
        """Finish the W&B run."""
        if self._run:
            self._run.finish()
            self._run = None

    def __enter__(self):
        self.start_run()
        return self

    def __exit__(self, *args):
        self.finish()
