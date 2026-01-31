"""Evaluation task definition."""
from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvalTask:
    """Defines an evaluation task.

    Ties together dataset, model, prompt template, and metrics
    for a single evaluation run.

    Args:
        task_id: Unique task identifier.
        dataset_path: Path to evaluation dataset.
        input_column: Column containing input text.
        reference_column: Column containing reference/ground truth.
        id_column: Column containing unique example IDs.
        prompt_template: Template string with {{column}} placeholders.
        context_columns: Columns containing context (for RAG evaluation).
        description: Human-readable task description.
        metadata: Arbitrary task metadata.
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    dataset_path: Optional[str] = None
    input_column: str = "input"
    reference_column: Optional[str] = "reference"
    id_column: str = "id"
    prompt_template: Optional[str] = None
    context_columns: Optional[List[str]] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_template_columns(self) -> List[str]:
        """Extract column names from the prompt template.

        Returns:
            List of column names referenced in the template.
        """
        if not self.prompt_template:
            return [self.input_column]
        return re.findall(r"\{\{\s*(\w+)\s*\}\}", self.prompt_template)

    def validate(self, available_columns: List[str]) -> None:
        """Validate task configuration against available columns.

        Args:
            available_columns: Columns available in the dataset.

        Raises:
            ValueError: If required columns are missing.
        """
        required = set(self.get_template_columns())
        available = set(available_columns)
        missing = required - available
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
