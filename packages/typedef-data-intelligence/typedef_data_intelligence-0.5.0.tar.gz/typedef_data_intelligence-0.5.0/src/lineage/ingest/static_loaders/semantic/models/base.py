"""Base models and common types for SQL analysis pipeline."""

from pydantic import BaseModel, Field
from typing import Optional


class Evidence(BaseModel):
    """Evidence for grounding into canonical SQL."""

    start: int = Field(
        description="Char start offset in canonical_sql where this alias/base appears"
    )
    end: int = Field(description="Char end offset in canonical_sql")
    text: str = Field(description="Matched substring for debugging")


class Ptr(BaseModel):
    """Pointer to a column or relation in another pass's output."""

    pass_name: str = Field(
        description="Which pass contains this data (e.g., 'column_analysis')"
    )
    field_path: str = Field(
        description="JSON path to the field (e.g., 'columns[0].name')"
    )
    rationale: Optional[str] = Field(
        None, description="Why this reference is important"
    )
