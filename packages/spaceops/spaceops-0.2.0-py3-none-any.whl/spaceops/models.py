"""Pydantic models for Genie space definitions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# COLUMN & TABLE CONFIGS
# =============================================================================


class ColumnConfig(BaseModel):
    """Configuration for a table column."""

    column_name: str
    enable_format_assistance: bool | None = None
    enable_entity_matching: bool | None = None
    # Local documentation only (not sent to API)
    description: str | None = Field(default=None, exclude=True)
    sample_values: list[str] | None = Field(default=None, exclude=True)

    model_config = {"extra": "allow"}


class TableConfig(BaseModel):
    """Configuration for a data source table."""

    identifier: str = Field(..., description="Fully qualified table name (catalog.schema.table)")
    column_configs: list[ColumnConfig] = Field(default_factory=list)
    # Local documentation only
    description: str | None = Field(default=None, exclude=True)

    model_config = {"extra": "allow"}


class DataSources(BaseModel):
    """Data sources configuration for a Genie space."""

    tables: list[TableConfig] = Field(default_factory=list)


# =============================================================================
# INSTRUCTIONS (API FORMAT)
# =============================================================================


class TextInstruction(BaseModel):
    """A text instruction for Genie."""

    id: str | None = None
    content: list[str]  # API expects array of strings


class TableReference(BaseModel):
    """Reference to a table in a join."""

    identifier: str
    alias: str | None = None


class JoinSpec(BaseModel):
    """Join specification between two tables."""

    id: str | None = None
    left: TableReference
    right: TableReference
    sql: list[str]  # Join condition as array of strings
    instruction: list[str] | None = None  # Optional description


class ExampleQuestionSQL(BaseModel):
    """Example question with SQL answer."""

    id: str | None = None
    question: list[str]  # Question as array of strings
    sql: list[str]  # SQL as array of strings (line by line)


class SQLFilter(BaseModel):
    """SQL filter snippet."""

    id: str | None = None
    sql: list[str]
    display_name: str


class SQLExpression(BaseModel):
    """SQL expression snippet."""

    id: str | None = None
    sql: list[str]
    display_name: str
    instruction: list[str] | None = None
    synonyms: list[str] | None = None


class SQLMeasure(BaseModel):
    """SQL measure snippet."""

    id: str | None = None
    sql: list[str]
    display_name: str


class SQLSnippets(BaseModel):
    """Collection of SQL snippets."""

    filters: list[SQLFilter] | None = None
    expressions: list[SQLExpression] | None = None
    measures: list[SQLMeasure] | None = None


class Instructions(BaseModel):
    """All instructions for the Genie space (API format)."""

    text_instructions: list[TextInstruction] | None = None
    example_question_sqls: list[ExampleQuestionSQL] | None = None
    join_specs: list[JoinSpec] | None = None
    sql_snippets: SQLSnippets | None = None


# =============================================================================
# SERIALIZED SPACE (API FORMAT)
# =============================================================================


class SerializedSpace(BaseModel):
    """The serialized space configuration (API format)."""

    version: int = 2
    data_sources: DataSources = Field(default_factory=DataSources)
    instructions: Instructions | None = None

    model_config = {"extra": "allow"}


# =============================================================================
# USER-FRIENDLY SPACE DEFINITION
# =============================================================================


class SimpleInstruction(BaseModel):
    """User-friendly instruction format."""

    content: str
    category: str | None = None


class SimpleJoin(BaseModel):
    """User-friendly join format."""

    left_table: str
    left_alias: str | None = None
    right_table: str
    right_alias: str | None = None
    condition: str  # e.g., "left.sku_name = right.sku_name"
    relationship_type: str = "MANY_TO_ONE"  # MANY_TO_ONE, ONE_TO_MANY, etc.
    description: str | None = None


class SimpleExample(BaseModel):
    """User-friendly example query format."""

    question: str
    sql: str
    description: str | None = None


class SimpleFilter(BaseModel):
    """User-friendly filter snippet."""

    name: str
    sql: str


class SimpleExpression(BaseModel):
    """User-friendly expression snippet."""

    name: str
    sql: str
    description: str | None = None
    synonyms: list[str] | None = None


class SimpleMeasure(BaseModel):
    """User-friendly measure snippet."""

    name: str
    sql: str


class SpaceDefinition(BaseModel):
    """Complete Genie space definition for version control.

    This is the user-friendly format stored in YAML files.
    It gets converted to the API format when pushing to Databricks.
    """

    title: str
    description: str | None = None
    warehouse_id: str | None = Field(
        None, description="Warehouse ID (can be overridden per environment)"
    )

    # Schema version
    version: int | str | None = Field(
        None, description="Schema version (int) or user-defined version (string)"
    )

    # Data sources
    data_sources: DataSources = Field(default_factory=DataSources)

    # Instructions (user-friendly format)
    instructions: list[SimpleInstruction] = Field(default_factory=list)
    joins: list[SimpleJoin] = Field(default_factory=list)
    example_queries: list[SimpleExample] = Field(default_factory=list)

    # SQL Snippets
    filters: list[SimpleFilter] = Field(default_factory=list)
    expressions: list[SimpleExpression] = Field(default_factory=list)
    measures: list[SimpleMeasure] = Field(default_factory=list)

    # Functions (not yet supported by API)
    functions: list[dict] = Field(default_factory=list)

    # Metadata
    tags: dict[str, str] = Field(default_factory=dict)

    def to_serialized_space(self) -> SerializedSpace:
        """Convert to the API serialized format."""

        # Counter for generating unique IDs across all instruction types
        id_counter = [0]  # Use list for mutability in nested functions

        def gen_id() -> str:
            """Generate a unique sortable 32-char hex ID."""
            id_counter[0] += 1
            # Format: prefix (8 chars) + counter (8 chars) + padding (16 chars) = 32 chars
            return f"01f0f000{id_counter[0]:08x}{'0' * 16}"

        # Sort tables by identifier AND column_configs by column_name (API requirements)
        sorted_tables = sorted(
            [
                TableConfig(
                    identifier=table.identifier,
                    column_configs=sorted(
                        [
                            ColumnConfig(
                                column_name=col.column_name,
                                enable_format_assistance=col.enable_format_assistance,
                                enable_entity_matching=col.enable_entity_matching,
                            )
                            for col in table.column_configs
                        ],
                        key=lambda c: c.column_name,
                    ),
                )
                for table in self.data_sources.tables
            ],
            key=lambda t: t.identifier,
        )
        sorted_data_sources = DataSources(tables=sorted_tables)

        # Build instructions in API format
        api_instructions = Instructions()

        # Convert text instructions - API only supports ONE item with multiple content lines
        if self.instructions:
            api_instructions.text_instructions = [
                TextInstruction(id=gen_id(), content=[inst.content for inst in self.instructions])
            ]

        # Convert example queries
        if self.example_queries:
            api_instructions.example_question_sqls = [
                ExampleQuestionSQL(
                    id=gen_id(),
                    question=[ex.question],
                    sql=ex.sql.strip().split("\n"),  # Split SQL into lines
                )
                for ex in self.example_queries
            ]

        # Convert joins
        if self.joins:
            api_instructions.join_specs = [
                JoinSpec(
                    id=gen_id(),
                    left=TableReference(
                        identifier=join.left_table,
                        alias=join.left_alias or join.left_table.split(".")[-1],
                    ),
                    right=TableReference(
                        identifier=join.right_table,
                        alias=join.right_alias or join.right_table.split(".")[-1],
                    ),
                    sql=[join.condition, f"--rt=FROM_RELATIONSHIP_TYPE_{join.relationship_type}--"],
                    instruction=[join.description] if join.description else None,
                )
                for join in self.joins
            ]

        # Convert SQL snippets
        if self.filters or self.expressions or self.measures:
            api_instructions.sql_snippets = SQLSnippets(
                filters=[
                    SQLFilter(id=gen_id(), sql=[f.sql], display_name=f.name) for f in self.filters
                ]
                if self.filters
                else None,
                expressions=[
                    SQLExpression(
                        id=gen_id(),
                        sql=[e.sql],
                        display_name=e.name,
                        instruction=[e.description] if e.description else None,
                        synonyms=e.synonyms,
                    )
                    for e in self.expressions
                ]
                if self.expressions
                else None,
                measures=[
                    SQLMeasure(id=gen_id(), sql=[m.sql], display_name=m.name) for m in self.measures
                ]
                if self.measures
                else None,
            )

        # Only include instructions if there's content
        has_instructions = (
            api_instructions.text_instructions
            or api_instructions.example_question_sqls
            or api_instructions.join_specs
            or api_instructions.sql_snippets
        )

        return SerializedSpace(
            version=2,
            data_sources=sorted_data_sources,
            instructions=api_instructions if has_instructions else None,
        )


# =============================================================================
# API RESPONSE MODELS
# =============================================================================


class GenieSpace(BaseModel):
    """Response model from Genie API."""

    space_id: str
    title: str
    warehouse_id: str
    serialized_space: str | None = None
    description: str | None = None


# =============================================================================
# BENCHMARK MODELS
# =============================================================================


class BenchmarkQuery(BaseModel):
    """A benchmark query for testing accuracy."""

    question: str
    expected_tables: list[str] = Field(default_factory=list)
    expected_columns: list[str] = Field(default_factory=list)
    expected_sql_contains: list[str] = Field(default_factory=list)
    expected_sql_pattern: str | None = None
    tags: list[str] = Field(default_factory=list)


class BenchmarkSuite(BaseModel):
    """A suite of benchmark queries."""

    name: str
    description: str | None = None
    queries: list[BenchmarkQuery]
    min_accuracy: float = Field(0.8, ge=0.0, le=1.0, description="Minimum required accuracy (0-1)")


class BenchmarkResult(BaseModel):
    """Result of a single benchmark query."""

    question: str
    passed: bool
    actual_sql: str | None = None
    error: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class BenchmarkSuiteResult(BaseModel):
    """Result of running a benchmark suite."""

    suite_name: str
    total: int
    passed: int
    failed: int
    accuracy: float
    results: list[BenchmarkResult]

    @property
    def meets_threshold(self) -> bool:
        """Check if accuracy meets the minimum threshold."""
        return self.accuracy >= 0.8


# =============================================================================
# ENVIRONMENT CONFIG MODELS
# =============================================================================


class EnvironmentConfig(BaseModel):
    """Configuration for a specific environment."""

    name: str
    host: str = Field(..., description="Databricks workspace host URL")
    warehouse_id: str
    space_id: str | None = Field(
        None, description="Existing space ID to update, or None to create new"
    )

    table_mappings: dict[str, str] = Field(
        default_factory=dict, description="Map source table names to environment-specific tables"
    )


class PromotionConfig(BaseModel):
    """Configuration for multi-environment promotion."""

    environments: dict[str, EnvironmentConfig]
    promotion_order: list[str] = Field(
        default_factory=lambda: ["dev", "stage", "prod"],
        description="Order of environments for promotion",
    )
