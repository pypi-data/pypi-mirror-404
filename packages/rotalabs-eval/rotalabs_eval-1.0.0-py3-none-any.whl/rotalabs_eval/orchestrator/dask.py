"""Dask distributed evaluation backend."""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DaskOrchestrator:
    """Dask-based distributed evaluation orchestrator.

    Requires dask[distributed]. Install with: pip install rotalabs-eval[dask]
    """

    def __init__(self, client: Optional[Any] = None) -> None:
        try:
            import dask.distributed
        except ImportError:
            raise ImportError(
                "Dask required. Install with: pip install rotalabs-eval[dask]"
            )
        self.client = client

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run distributed evaluation on Dask cluster."""
        raise NotImplementedError("Dask orchestrator available in a future release")
