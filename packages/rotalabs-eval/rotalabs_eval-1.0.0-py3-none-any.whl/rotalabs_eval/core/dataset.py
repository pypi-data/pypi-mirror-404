"""Dataset handling for evaluation."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from rotalabs_eval.core.exceptions import EvalDatasetError

logger = logging.getLogger(__name__)


@dataclass
class DatasetConfig:
    """Configuration for dataset loading.

    Args:
        path: Path to dataset file or table.
        id_column: Column containing unique example IDs.
        input_column: Column containing input text.
        reference_column: Column containing reference/ground truth.
        metadata_columns: Additional columns to preserve.
        filter_condition: Pandas query filter string.
        sample_size: Number of examples to sample.
        sample_seed: Random seed for sampling.
    """

    path: str
    id_column: str = "id"
    input_column: str = "input"
    reference_column: str = "reference"
    metadata_columns: List[str] = field(default_factory=list)
    filter_condition: Optional[str] = None
    sample_size: Optional[int] = None
    sample_seed: int = 42


class DatasetHandler:
    """Handles loading, sampling, and managing evaluation datasets."""

    def __init__(self, config: DatasetConfig) -> None:
        self.config = config
        self._df: Optional[pd.DataFrame] = None
        self._count: Optional[int] = None

    def load(self) -> pd.DataFrame:
        """Load dataset from file.

        Supports CSV, JSON, JSONL, and Parquet formats.

        Returns:
            Loaded DataFrame.
        """
        path = self.config.path
        logger.info(f"Loading dataset from {path}")

        if path.endswith(".csv"):
            df = pd.read_csv(path)
        elif path.endswith(".jsonl"):
            df = pd.read_json(path, lines=True)
        elif path.endswith(".json"):
            df = pd.read_json(path)
        elif path.endswith(".parquet"):
            df = pd.read_parquet(path)
        else:
            raise EvalDatasetError(f"Unsupported file format: {path}")

        if self.config.filter_condition:
            df = df.query(self.config.filter_condition)

        # Select required columns
        columns = [
            self.config.id_column,
            self.config.input_column,
            self.config.reference_column,
        ] + self.config.metadata_columns
        existing = [c for c in columns if c in df.columns]
        df = df[existing]

        # Sample if requested
        if self.config.sample_size is not None and len(df) > self.config.sample_size:
            df = df.sample(
                n=self.config.sample_size,
                random_state=self.config.sample_seed,
            )
            logger.info(f"Sampled {self.config.sample_size} examples")

        self._df = df
        return df

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._df is None:
            self.load()
        return self._df

    def count(self) -> int:
        if self._count is None:
            self._count = len(self.dataframe)
        return self._count


def load_dataset(
    path: str,
    id_column: str = "id",
    input_column: str = "input",
    reference_column: str = "reference",
    filter_condition: Optional[str] = None,
    sample_size: Optional[int] = None,
) -> pd.DataFrame:
    """Convenience function to load a dataset.

    Args:
        path: Path to dataset file.
        id_column: Column for example IDs.
        input_column: Column for input text.
        reference_column: Column for reference text.
        filter_condition: Optional pandas query filter.
        sample_size: Optional sample size.

    Returns:
        Loaded DataFrame.
    """
    config = DatasetConfig(
        path=path,
        id_column=id_column,
        input_column=input_column,
        reference_column=reference_column,
        filter_condition=filter_condition,
        sample_size=sample_size,
    )
    handler = DatasetHandler(config)
    return handler.load()


def create_eval_dataset(
    data: List[Dict[str, Any]],
    id_column: str = "id",
    input_column: str = "input",
    reference_column: str = "reference",
) -> pd.DataFrame:
    """Create evaluation dataset from list of dictionaries.

    Args:
        data: List of dicts with evaluation examples.
        id_column: Name of ID column.
        input_column: Name of input column.
        reference_column: Name of reference column.

    Returns:
        DataFrame with evaluation data.
    """
    if not data:
        raise EvalDatasetError("Data cannot be empty")

    required = {id_column, input_column, reference_column}
    first_keys = set(data[0].keys())
    missing = required - first_keys
    if missing:
        raise EvalDatasetError(f"Missing required columns: {missing}")

    return pd.DataFrame(data)
