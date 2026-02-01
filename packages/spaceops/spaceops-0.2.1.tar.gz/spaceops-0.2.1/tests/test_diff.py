"""Tests for SpaceOps diff utilities."""

import pytest
from spaceops.diff import compute_diff, parse_serialized_space


class TestParseSerialized:
    def test_parse_string(self):
        json_str = '{"version": 2, "data_sources": {"tables": []}}'
        result = parse_serialized_space(json_str)
        assert result["version"] == 2

    def test_parse_dict(self):
        data = {"version": 2, "data_sources": {"tables": []}}
        result = parse_serialized_space(data)
        assert result["version"] == 2


class TestComputeDiff:
    def test_no_changes(self):
        config = {
            "version": 2,
            "data_sources": {
                "tables": [
                    {"identifier": "catalog.schema.table"}
                ]
            }
        }
        result = compute_diff(config, config)
        
        assert result.has_changes is False
        assert result.summary == "No changes"

    def test_table_added(self):
        local = {
            "data_sources": {
                "tables": [
                    {"identifier": "catalog.schema.table1"},
                    {"identifier": "catalog.schema.table2"},
                ]
            }
        }
        remote = {
            "data_sources": {
                "tables": [
                    {"identifier": "catalog.schema.table1"},
                ]
            }
        }
        
        result = compute_diff(local, remote)
        
        assert result.has_changes is True
        assert "catalog.schema.table2" in result.tables_added

    def test_table_removed(self):
        local = {
            "data_sources": {
                "tables": [
                    {"identifier": "catalog.schema.table1"},
                ]
            }
        }
        remote = {
            "data_sources": {
                "tables": [
                    {"identifier": "catalog.schema.table1"},
                    {"identifier": "catalog.schema.table2"},
                ]
            }
        }
        
        result = compute_diff(local, remote)
        
        assert result.has_changes is True
        assert "catalog.schema.table2" in result.tables_removed

    def test_table_modified(self):
        local = {
            "data_sources": {
                "tables": [
                    {
                        "identifier": "catalog.schema.table1",
                        "column_configs": [{"column_name": "col1"}]
                    },
                ]
            }
        }
        remote = {
            "data_sources": {
                "tables": [
                    {
                        "identifier": "catalog.schema.table1",
                        "column_configs": [{"column_name": "col2"}]
                    },
                ]
            }
        }
        
        result = compute_diff(local, remote)
        
        assert result.has_changes is True
        assert "catalog.schema.table1" in result.tables_modified

    def test_instructions_changed(self):
        local = {"instructions": [{"content": "New instruction"}]}
        remote = {"instructions": [{"content": "Old instruction"}]}
        
        result = compute_diff(local, remote)
        
        assert result.has_changes is True
        assert result.instructions_changed is True

    def test_joins_changed(self):
        local = {"joins": [{"left_table": "t1", "right_table": "t2"}]}
        remote = {"joins": []}
        
        result = compute_diff(local, remote)
        
        assert result.has_changes is True
        assert result.joins_changed is True

