"""Tests for ModelMaterialization and get_model_materializations."""

import pytest
from lineage.backends.lineage.protocol import (
    ModelMaterialization,
    ModelMaterializationsResult,
)
from pydantic import ValidationError


class TestModelMaterialization:
    """Tests for ModelMaterialization Pydantic model."""

    def test_all_fields_populated(self) -> None:
        """Constructing with all fields populated succeeds."""
        mat = ModelMaterialization(
            type="PhysicalTable",
            fqn="my_db.my_schema.my_table",
            database="my_db",
            schema_name="my_schema",
            relation_name="my_table",
            warehouse_type="snowflake",
            environment="prod",
            materialization_strategy="table",
            updated_at="2024-01-01T00:00:00Z",
        )
        assert mat.type == "PhysicalTable"
        assert mat.database == "my_db"
        assert mat.schema_name == "my_schema"
        assert mat.warehouse_type == "snowflake"

    def test_nullable_fields_accept_none(self) -> None:
        """database, schema_name, warehouse_type can be None from graph."""
        mat = ModelMaterialization(
            type="PhysicalView",
            fqn="my_schema.my_view",
            database=None,
            schema_name=None,
            relation_name="my_view",
            warehouse_type=None,
            environment="dev",
        )
        assert mat.database is None
        assert mat.schema_name is None
        assert mat.warehouse_type is None

    def test_nullable_fields_default_to_none(self) -> None:
        """database, schema_name, warehouse_type default to None when omitted."""
        mat = ModelMaterialization(
            type="PhysicalTable",
            fqn="my_schema.my_table",
            relation_name="my_table",
            environment="prod",
        )
        assert mat.database is None
        assert mat.schema_name is None
        assert mat.warehouse_type is None

    def test_missing_required_field_raises(self) -> None:
        """Missing required 'environment' raises ValidationError."""
        with pytest.raises(ValidationError):
            ModelMaterialization(
                type="PhysicalTable",
                fqn="my_db.my_schema.my_table",
                relation_name="my_table",
                # environment is missing
            )

    def test_materializations_result_empty(self) -> None:
        """ModelMaterializationsResult with no materializations."""
        result = ModelMaterializationsResult(
            model_id="model.test.my_model",
            materializations=[],
        )
        assert result.model_id == "model.test.my_model"
        assert len(result.materializations) == 0

    def test_materializations_result_with_items(self) -> None:
        """ModelMaterializationsResult with multiple materializations."""
        mats = [
            ModelMaterialization(
                type="PhysicalTable",
                fqn="prod_db.marts.my_table",
                database="prod_db",
                schema_name="marts",
                relation_name="my_table",
                warehouse_type="snowflake",
                environment="prod",
            ),
            ModelMaterialization(
                type="PhysicalTable",
                fqn="dev_db.marts.my_table",
                database="dev_db",
                schema_name="marts",
                relation_name="my_table",
                warehouse_type="snowflake",
                environment="dev",
            ),
        ]
        result = ModelMaterializationsResult(
            model_id="model.test.my_model",
            materializations=mats,
        )
        assert len(result.materializations) == 2
        assert result.materializations[0].environment == "prod"
        assert result.materializations[1].environment == "dev"
