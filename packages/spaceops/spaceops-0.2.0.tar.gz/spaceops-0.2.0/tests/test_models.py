"""Tests for SpaceOps data models."""

import pytest
from spaceops.models import (
    ColumnConfig,
    DataSources,
    SpaceDefinition,
    TableConfig,
    SerializedSpace,
    BenchmarkQuery,
    BenchmarkSuite,
)


class TestColumnConfig:
    def test_default_values(self):
        col = ColumnConfig(column_name="test_col")
        assert col.column_name == "test_col"
        # API sends None by default (optional booleans)
        assert col.enable_format_assistance is None
        assert col.enable_entity_matching is None

    def test_with_all_options(self):
        col = ColumnConfig(
            column_name="category",
            enable_format_assistance=True,
            enable_entity_matching=True,
            description="Product category",
        )
        assert col.enable_format_assistance is True
        assert col.enable_entity_matching is True


class TestTableConfig:
    def test_basic_table(self):
        table = TableConfig(identifier="catalog.schema.table")
        assert table.identifier == "catalog.schema.table"
        assert table.column_configs == []

    def test_table_with_columns(self):
        table = TableConfig(
            identifier="system.billing.usage",
            column_configs=[
                ColumnConfig(column_name="usage_date", enable_format_assistance=True),
                ColumnConfig(column_name="sku_name", enable_entity_matching=True),
            ],
        )
        assert len(table.column_configs) == 2


class TestSpaceDefinition:
    def test_minimal_definition(self):
        definition = SpaceDefinition(title="Test Space")
        assert definition.title == "Test Space"
        assert definition.warehouse_id is None
        assert len(definition.data_sources.tables) == 0

    def test_full_definition(self):
        definition = SpaceDefinition(
            title="Billing Analytics",
            description="Analytics for billing data",
            warehouse_id="abc123",
            data_sources=DataSources(
                tables=[
                    TableConfig(identifier="system.billing.usage"),
                ]
            ),
        )
        assert definition.title == "Billing Analytics"
        assert len(definition.data_sources.tables) == 1

    def test_to_serialized_space(self):
        definition = SpaceDefinition(
            title="Test",
            data_sources=DataSources(
                tables=[TableConfig(identifier="catalog.schema.table")]
            ),
        )
        serialized = definition.to_serialized_space()
        
        assert isinstance(serialized, SerializedSpace)
        assert serialized.version == 2
        assert len(serialized.data_sources.tables) == 1


class TestBenchmarkSuite:
    def test_basic_suite(self):
        suite = BenchmarkSuite(
            name="Test Suite",
            queries=[
                BenchmarkQuery(
                    question="What is total usage?",
                    expected_tables=["system.billing.usage"],
                ),
            ],
        )
        assert suite.name == "Test Suite"
        assert suite.min_accuracy == 0.8
        assert len(suite.queries) == 1

    def test_custom_accuracy(self):
        suite = BenchmarkSuite(
            name="Strict Suite",
            min_accuracy=0.95,
            queries=[
                BenchmarkQuery(question="Test query"),
            ],
        )
        assert suite.min_accuracy == 0.95

