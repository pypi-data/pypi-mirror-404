"""SQL Analyzer prompts."""

# Technical prompts (Passes 1-4)
from .technical import (
    JOIN_EDGE_EXTRACTION_PROMPT,
    FILTER_EXTRACTION_PROMPT,
)

# Analytical prompts (Passes 5-8)
from .analytical import (
    GROUPING_EXTRACTION_PROMPT,
    TIME_ANALYSIS_PROMPT,
    WINDOW_EXTRACTION_PROMPT,
    OUTPUT_SHAPE_PROMPT,
)

# Validation prompts (Pass 9)
from .validation import AUDITOR_PROMPT

# Business prompts (Passes 10-10a)
from .business import (
    BUSINESS_SEMANTICS_PROMPT,
    GRAIN_HUMANIZATION_PROMPT,
)

__all__ = [
    # Technical
    "JOIN_EDGE_EXTRACTION_PROMPT",
    "FILTER_EXTRACTION_PROMPT",
    # Analytical
    "GROUPING_EXTRACTION_PROMPT",
    "TIME_ANALYSIS_PROMPT",
    "WINDOW_EXTRACTION_PROMPT",
    "OUTPUT_SHAPE_PROMPT",
    # Validation
    "AUDITOR_PROMPT",
    # Business
    "BUSINESS_SEMANTICS_PROMPT",
    "GRAIN_HUMANIZATION_PROMPT",
]
