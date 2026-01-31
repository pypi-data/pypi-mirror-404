"""Apache Spark distributed evaluation backend."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from rotalabs_eval.core.exceptions import EvalOrchestratorError

logger = logging.getLogger(__name__)


class SparkOrchestrator:
    """Spark-based distributed evaluation orchestrator.

    Requires pyspark. Install with: pip install rotalabs-eval[spark]
    """

    def __init__(self, spark_session: Optional[Any] = None) -> None:
        try:
            from pyspark.sql import SparkSession
        except ImportError:
            raise ImportError(
                "PySpark required. Install with: pip install rotalabs-eval[spark]"
            )
        self.spark = spark_session

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run distributed evaluation on Spark cluster."""
        raise NotImplementedError("Spark orchestrator available in a future release")
