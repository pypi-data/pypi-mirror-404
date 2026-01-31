"""Ray distributed evaluation backend."""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RayOrchestrator:
    """Ray-based distributed evaluation orchestrator.

    Requires ray. Install with: pip install rotalabs-eval[ray]
    """

    def __init__(self) -> None:
        try:
            import ray
        except ImportError:
            raise ImportError(
                "Ray required. Install with: pip install rotalabs-eval[ray]"
            )

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run distributed evaluation on Ray cluster."""
        raise NotImplementedError("Ray orchestrator available in a future release")
