"""MLflow integration for experiment tracking."""
from __future__ import annotations

import json
import logging
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional

logger = logging.getLogger(__name__)

_mlflow = None


def _get_mlflow():
    global _mlflow
    if _mlflow is None:
        try:
            import mlflow
            _mlflow = mlflow
        except ImportError:
            raise ImportError("MLflow not installed. Install with: pip install rotalabs-eval[tracking]")
    return _mlflow


@dataclass
class TrackingConfig:
    """Configuration for experiment tracking."""
    experiment_name: str
    tracking_uri: Optional[str] = None
    run_name: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    log_artifacts: bool = True
    artifact_location: Optional[str] = None


class MLflowTracker:
    """Handles MLflow experiment tracking for evaluations."""

    def __init__(self, config: TrackingConfig) -> None:
        self.config = config
        self._run_id: Optional[str] = None
        self._mlflow: Any = None
        self._initialized = False

    def _init_mlflow(self) -> None:
        if self._initialized:
            return
        self._mlflow = _get_mlflow()
        if self.config.tracking_uri:
            self._mlflow.set_tracking_uri(self.config.tracking_uri)
        experiment = self._mlflow.get_experiment_by_name(self.config.experiment_name)
        if experiment is None:
            experiment_id = self._mlflow.create_experiment(
                self.config.experiment_name,
                artifact_location=self.config.artifact_location,
            )
        else:
            experiment_id = experiment.experiment_id
        self._mlflow.set_experiment(experiment_id=experiment_id)
        self._initialized = True

    @contextmanager
    def start_run(self, run_name: Optional[str] = None) -> Iterator[str]:
        """Context manager for MLflow run."""
        self._init_mlflow()
        name = run_name or self.config.run_name
        with self._mlflow.start_run(run_name=name) as run:
            self._run_id = run.info.run_id
            if self.config.tags:
                self._mlflow.set_tags(self.config.tags)
            try:
                yield self._run_id
            finally:
                self._run_id = None

    def log_params(self, params: Dict[str, Any]) -> None:
        if self._mlflow is None:
            self._init_mlflow()
        flat = self._flatten_dict(params)
        truncated = {}
        for k, v in flat.items():
            sv = str(v)
            if len(sv) > 500:
                sv = sv[:497] + "..."
            truncated[k] = sv
        self._mlflow.log_params(truncated)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        if self._mlflow is None:
            self._init_mlflow()
        self._mlflow.log_metrics(metrics, step=step)

    def log_metric_with_ci(
        self, name: str, value: float, ci_lower: float, ci_upper: float,
        step: Optional[int] = None,
    ) -> None:
        self.log_metrics({name: value, f"{name}_ci_lower": ci_lower, f"{name}_ci_upper": ci_upper}, step=step)

    def log_artifact(self, data: Any, filename: str, artifact_path: Optional[str] = None) -> None:
        if not self.config.log_artifacts:
            return
        if self._mlflow is None:
            self._init_mlflow()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, filename)
            if isinstance(data, dict):
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=2, default=str)
            elif isinstance(data, str):
                with open(filepath, "w") as f:
                    f.write(data)
            else:
                import pickle
                with open(filepath, "wb") as f:
                    pickle.dump(data, f)
            self._mlflow.log_artifact(filepath, artifact_path)

    def set_tag(self, key: str, value: str) -> None:
        if self._mlflow is None:
            self._init_mlflow()
        self._mlflow.set_tag(key, value)

    @staticmethod
    def _flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        items: list = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(MLflowTracker._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


def create_tracker(
    experiment_name: str,
    tracking_uri: Optional[str] = None,
    run_name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> MLflowTracker:
    """Create an MLflow tracker with convenient defaults."""
    config = TrackingConfig(
        experiment_name=experiment_name,
        tracking_uri=tracking_uri,
        run_name=run_name,
        tags=tags or {},
    )
    return MLflowTracker(config)
