"""Model enrichment: role classification, domain extraction, PII detection.

This module provides enrichment functionality to classify models and extract
business metadata needed for cluster analysis. It queries the graph for
semantic analysis data and uses LLM extraction (via Fenic) to identify
business domains.

Key functionality:
- Role classification: Classify models as "fact", "dimension", or "mixed"
- Domain extraction: Extract business domain keywords from semantic analysis intent
- PII detection: Aggregate PII flags from BusinessDimension nodes
- Statistics: Count measures and dimensions per model
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List

from pydantic import BaseModel, Field

try:
    import fenic as fc
    FENIC_AVAILABLE = True
except ImportError:
    FENIC_AVAILABLE = False

from lineage.backends.lineage.models.clustering import ModelEnrichmentData

if TYPE_CHECKING:
    from lineage.backends.lineage.protocol import LineageStorage

logger = logging.getLogger(__name__)


class DomainExtraction(BaseModel):
    """Schema for extracting business domains from model intent."""

    domains: List[str] = Field(
        description="List of 1-3 business domain keywords (e.g., 'finance', 'sales', 'customer') "
        "extracted from the intent field describing what this data model is about."
    )


class ModelEnricher:
    """Enriches models with clustering metadata.

    This class coordinates the enrichment process, which includes:
    1. Role classification based on semantic analysis
    2. LLM extraction of business domains from intent field
    3. PII detection from column metadata
    4. Statistical counts (measures, dimensions)
    """

    def __init__(self, storage: LineageStorage):
        """Initialize enricher with storage backend.

        Args:
            storage: LineageStorage instance for querying graph
        """
        self.storage = storage

    async def enrich_all_models(
        self,
        session: fc.Session
    ) -> Dict[str, ModelEnrichmentData]:
        """Enrich all models with clustering metadata.

        This is the main entry point. It queries the graph for all models
        with semantic analysis, classifies their roles, extracts domains
        via LLM, and gathers PII/statistics.

        Args:
            session: Fenic session for LLM operations (managed by integration layer)

        Returns:
            Dictionary mapping model_id -> ModelEnrichmentData
        """
        logger.info("Starting model enrichment...")

        # Get all models with semantic analysis
        models = self.storage.get_all_models_with_analysis()
        logger.info(f"Found {len(models)} models with semantic analysis")

        # Extract domains via LLM (parallel processing)
        domains_by_model = await self._extract_domains_llm(models, session=session)

        # Build enrichment data for each model
        enriched = {}
        for model_data in models:
            model_id = model_data["model_id"]

            # Role classification
            role = self._classify_role(model_data)

            # Statistics from protocol queries
            fact_count = self.storage.get_model_business_measure_count(model_id)
            dim_count = self.storage.get_model_business_dimension_count(model_id)
            has_pii = self.storage.model_has_pii(model_id)

            enriched[model_id] = ModelEnrichmentData(
                model_id=model_id,
                role=role,
                domains=domains_by_model.get(model_id, []),
                has_pii=has_pii,
                fact_count=fact_count,
                dimension_count=dim_count,
            )

        logger.info(f"Enriched {len(enriched)} models")

        # Log role distribution
        role_counts = {}
        for data in enriched.values():
            role_counts[data.role] = role_counts.get(data.role, 0) + 1
        logger.info(f"Role distribution: {role_counts}")

        return enriched

    async def _extract_domains_llm(self, models: List[Dict], session: fc.Session) -> Dict[str, List[str]]:
        """Extract business domains from SemanticAnalysis.intent using LLM.

        Uses Fenic to run parallel LLM extraction on all model intents,
        extracting 1-3 business domain keywords per model.

        Args:
            models: List of model data dicts with 'model_id' and 'intent' fields
            session: Fenic session for LLM operations (managed by integration layer)

        Returns:
            Dictionary mapping model_id -> list of domain keywords
        """
        if not FENIC_AVAILABLE:
            logger.warning("Fenic not available, skipping domain extraction")
            return {}

        # Filter to models with intent
        data = [
            {"model_id": m["model_id"], "intent": m.get("intent", "")}
            for m in models
            if m.get("intent")
        ]

        if not data:
            logger.warning("No models with intent field found, skipping domain extraction")
            return {}

        logger.info(f"Extracting domains from {len(data)} models using LLM...")

        try:
            # Use provided session to create DataFrame
            df = session.create_dataframe(data)

            # Run LLM extraction - semantic.extract returns a struct column
            # We need to select both model_id and the extraction result
            result_df = df.select(
                fc.col("model_id"),
                fc.semantic.extract("intent", DomainExtraction).alias("extraction")
            )

            # Execute and get list of row dicts
            rows = result_df.to_pylist()

            # Convert to dict using Pydantic model validation
            domains_by_model = {}
            for row in rows:
                model_id = row["model_id"]
                extraction_dict = row.get("extraction")

                # Use Pydantic model_validate for type-safe deserialization
                if extraction_dict:
                    try:
                        domain_model = DomainExtraction.model_validate(extraction_dict)
                        domains_by_model[model_id] = domain_model.domains[:3]
                    except Exception as e:
                        logger.debug(f"Failed to validate extraction for {model_id}: {e}")
                        domains_by_model[model_id] = []
                else:
                    domains_by_model[model_id] = []

            logger.info(
                f"Extracted domains for {len(domains_by_model)} models "
                f"({len([d for d in domains_by_model.values() if d])} non-empty)"
            )
            return domains_by_model

        except Exception as e:
            logger.error(f"LLM domain extraction failed: {e}")
            logger.warning("Continuing without domain enrichment")
            return {}

    def _classify_role(self, model_data: Dict) -> str:
        """Classify model as fact, dimension, or mixed.

        Classification logic based on actual BusinessMeasure and BusinessDimension counts:
        - measure_count > 0 AND dimension_count > 0 → "mixed"
        - measure_count > 0 → "fact"
        - Otherwise → "dimension"

        Args:
            model_data: Model data dict with 'model_id' field

        Returns:
            Role string: "fact", "dimension", or "mixed"
        """
        model_id = model_data.get("model_id")

        # Get actual counts from the graph
        fact_count = self.storage.get_model_business_measure_count(model_id)
        dim_count = self.storage.get_model_business_dimension_count(model_id)

        # Classify based on counts
        if fact_count > 0 and dim_count > 0:
            return "mixed"
        elif fact_count > 0:
            return "fact"
        else:
            return "dimension"


__all__ = ["ModelEnricher"]
