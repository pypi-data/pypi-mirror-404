"""Base class for all SQL analysis passes."""

from abc import ABC, abstractmethod
from typing import List

import fenic as fc

from lineage.ingest.config import PipelineConfig


class BasePass(ABC):
    """Abstract base class for SQL analysis passes."""

    def __init__(self, session: fc.Session, name: str, pipeline_config: PipelineConfig):
        """Initialize a pass with a Fenic session and pipeline configuration.

        Args:
            session: Fenic session for DataFrame operations
            name: Name of this pass (e.g., "relation_analysis")
            pipeline_config: Pipeline configuration with model assignments and settings
        """
        self.session = session
        self.name = name
        self.pipeline_config = pipeline_config

    @abstractmethod
    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check if required columns exist in the DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            True if all required inputs are present

        Raises:
            ValueError: If required columns are missing
        """
        pass

    @abstractmethod
    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Run the pass and return updated DataFrame.

        Args:
            df: Input DataFrame with previous pass results

        Returns:
            Updated DataFrame with this pass's results added
        """
        pass

    @abstractmethod
    def get_required_passes(self) -> List[str]:
        """Return list of prerequisite pass names.

        Returns:
            List of pass names that must run before this one
        """
        pass

    def get_name(self) -> str:
        """Get the name of this pass.

        Returns:
            Pass name
        """
        return self.name

    def _check_columns(self, df: fc.DataFrame, required_columns: List[str]) -> bool:
        """Helper to check if required columns exist.

        Args:
            df: DataFrame to check
            required_columns: List of required column names

        Returns:
            True if all columns exist

        Raises:
            ValueError: If any required column is missing
        """
        # Get column names from DataFrame
        existing_columns = df.columns

        missing = [col for col in required_columns if col not in existing_columns]
        if missing:
            raise ValueError(
                f"Pass '{self.name}' requires columns {missing} which are not present. "
                f"Available columns: {existing_columns}"
            )

        return True
