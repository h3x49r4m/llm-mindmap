"""Tests for MindMap data structure."""

import pytest
import json
import ast

from llm_mindmap.mindmap.mindmap import (
    MindMap,
    dict_keys_to_lowercase,
    stringify_label_summaries,
    generate_theme_tree,
)


class TestMindMap:
    """Test MindMap dataclass."""

    def test_create_mindmap(self):
        """Test creating a simple MindMap."""
        mindmap = MindMap(
            label="Root",
            node=1,
            summary="Root node",
        )

        assert mindmap.label == "Root"
        assert mindmap.node == 1
        assert mindmap.summary == "Root node"
        assert mindmap.children == []
        assert mindmap.keywords == []

    def test_mindmap_with_children(self):
        """Test creating MindMap with children."""
        child1 = MindMap(label="Child 1", node=2, summary="First child")
        child2 = MindMap(label="Child 2", node=3, summary="Second child")

        mindmap = MindMap(
            label="Root",
            node=1,
            summary="Root node",
            children=[child1, child2],
        )

        assert len(mindmap.children) == 2
        assert mindmap.children[0].label == "Child 1"
        assert mindmap.children[1].label == "Child 2"

    def test_from_dict_simple(self):
        """Test creating MindMap from simple dictionary."""
        tree_dict = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
            "keywords": [],
        }

        mindmap = MindMap.from_dict(tree_dict)

        assert mindmap.label == "Root"
        assert mindmap.node == 1
        assert mindmap.summary == "Root node"

    def test_from_dict_with_children(self):
        """Test creating MindMap from dictionary with children."""
        tree_dict = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [
                {"label": "Child 1", "node": 2, "summary": "First child", "children": []},
                {"label": "Child 2", "node": 3, "summary": "Second child", "children": []},
            ],
            "keywords": [],
        }

        mindmap = MindMap.from_dict(tree_dict)

        assert len(mindmap.children) == 2
        assert mindmap.children[0].label == "Child 1"
        assert mindmap.children[1].label == "Child 2"

    def test_from_dict_case_insensitive(self):
        """Test from_dict handles case-insensitive keys."""
        tree_dict = {
            "Label": "Root",
            "Node": 1,
            "Summary": "Root node",
            "Children": [],
            "Keywords": [],
        }

        mindmap = MindMap.from_dict(tree_dict)

        assert mindmap.label == "Root"
        assert mindmap.node == 1

    def test_as_string(self):
        """Test string representation of MindMap."""
        child = MindMap(label="Child", node=2, summary="Child node")
        mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

        result = mindmap.as_string()

        assert "Root" in result
        assert "Child" in result
        assert "└──" in result

    def test_get_label_summaries(self):
        """Test extracting label summaries."""
        child1 = MindMap(label="Child 1", node=2, summary="First child")
        child2 = MindMap(label="Child 2", node=3, summary="Second child")
        mindmap = MindMap(
            label="Root",
            node=1,
            summary="Root node",
            children=[child1, child2],
        )

        result = mindmap.get_label_summaries()

        assert len(result) == 3
        assert "Root" in result
        assert "Child 1" in result
        assert "Child 2" in result
        assert result["Root"] == "Root node"

    def test_get_summaries(self):
        """Test extracting all summaries."""
        child = MindMap(label="Child", node=2, summary="Child node")
        mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

        result = mindmap.get_summaries()

        assert len(result) == 2
        assert "Root node" in result
        assert "Child node" in result

    def test_get_terminal_label_summaries(self):
        """Test extracting terminal node label summaries."""
        child = MindMap(label="Child", node=2, summary="Child node")
        mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

        result = mindmap.get_terminal_label_summaries()

        assert len(result) == 1
        assert "Child" in result
        assert "Root" not in result

    def test_get_terminal_labels(self):
        """Test extracting terminal node labels."""
        child = MindMap(label="Child", node=2, summary="Child node")
        mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

        result = mindmap.get_terminal_labels()

        assert len(result) == 1
        assert "Child" in result

    def test_get_terminal_summaries(self):
        """Test extracting terminal node summaries."""
        child = MindMap(label="Child", node=2, summary="Child node")
        mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

        result = mindmap.get_terminal_summaries()

        assert len(result) == 1
        assert "Child node" in result

    def test_get_label_to_parent_mapping(self):
        """Test mapping leaf labels to parent labels."""
        child = MindMap(label="Child", node=2, summary="Child node")
        mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

        result = mindmap.get_label_to_parent_mapping()

        assert result == {"Child": "Root"}

    def test_to_dict(self):
        """Test converting MindMap to dictionary."""
        child = MindMap(label="Child", node=2, summary="Child node")
        mindmap = MindMap(
            label="Root",
            node=1,
            summary="Root node",
            children=[child],
            keywords=["key1"],
        )

        result = mindmap._to_dict()

        assert result["label"] == "Root"
        assert result["node"] == 1
        assert result["summary"] == "Root node"
        assert len(result["children"]) == 1
        assert result["children"][0]["label"] == "Child"
        assert result["keywords"] == ["key1"]

    def test_to_json(self):
        """Test converting MindMap to JSON string."""
        mindmap = MindMap(label="Root", node=1, summary="Root node")

        result = mindmap.to_json()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["label"] == "Root"

    def test_to_rows(self):
        """Test flattening MindMap to rows."""
        child = MindMap(label="Child", node=2, summary="Child node")
        mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

        result = mindmap.to_rows()

        assert len(result) == 2
        assert result[0]["Label"] == "Root"
        assert result[1]["Label"] == "Child"
        assert result[1]["Parent"] == "Root"

    def test_to_dataframe(self):
        """Test converting MindMap to DataFrame."""
        child = MindMap(label="Child", node=2, summary="Child node")
        mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

        df = mindmap.to_dataframe()

        assert len(df) == 1
        assert df.iloc[0]["Label"] == "Child"
        assert df.iloc[0]["Parent"] == "Root"

    def test_to_dataframe_leaves_only(self):
        """Test converting MindMap to DataFrame with leaves only."""
        grandchild = MindMap(label="Grandchild", node=3, summary="Grandchild node")
        child = MindMap(
            label="Child",
            node=2,
            summary="Child node",
            children=[grandchild],
        )
        mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

        df = mindmap.to_dataframe(leaves_only=True)

        assert len(df) == 1
        assert df.iloc[0]["Label"] == "Grandchild"

    def test_visualize_unsupported_engine(self):
        """Test visualization with unsupported engine."""
        mindmap = MindMap(label="Root", node=1, summary="Root node")

        with pytest.raises(ValueError) as exc_info:
            mindmap.visualize(engine="unsupported")

        assert "Unsupported engine" in str(exc_info.value)


class TestDictKeysToLowercase:
    """Test dict_keys_to_lowercase utility function."""

    def test_simple_dict(self):
        """Test converting simple dictionary keys."""
        d = {"Key1": "value1", "Key2": "value2"}
        result = dict_keys_to_lowercase(d)

        assert result == {"key1": "value1", "key2": "value2"}

    def test_nested_dict(self):
        """Test converting nested dictionary keys."""
        d = {"Key1": {"NestedKey": "value"}}
        result = dict_keys_to_lowercase(d)

        assert result == {"key1": {"nestedkey": "value"}}

    def test_mixed_dict(self):
        """Test dictionary with mixed keys."""
        d = {"Key1": "value1", "key2": {"NestedKey": "value2"}}
        result = dict_keys_to_lowercase(d)

        assert result == {"key1": "value1", "key2": {"nestedkey": "value2"}}


class TestStringifyLabelSummaries:
    """Test stringify_label_summaries utility function."""

    def test_stringify_simple(self):
        """Test stringifying simple label summaries."""
        summaries = {"label1": "summary1", "label2": "summary2"}
        result = stringify_label_summaries(summaries)

        assert result == ["label1: summary1", "label2: summary2"]

    def test_stringify_empty(self):
        """Test stringifying empty dictionary."""
        result = stringify_label_summaries({})

        assert result == []


class TestGenerateThemeTree:
    """Test generate_theme_tree function."""

    def test_with_string_config(self):
        """Test generating theme tree with string config."""
        tree_dict = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
            "keywords": [],
        }

        with pytest.MonkeyPatch.context() as m:
            def mock_get_response(chat_history, **kwargs):
                return json.dumps(tree_dict)

            m.setattr(
                "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
                mock_get_response,
            )

            result = generate_theme_tree("Test Theme", focus="")

        assert result.label == "Root"
        assert result.node == 1

    def test_with_dict_config(self):
        """Test generating theme tree with dict config."""
        tree_dict = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
            "keywords": [],
        }

        config = {
            "provider": "openrouter",
            "model": "gpt-4o-mini",
            "connection_config": {},
        }

        with pytest.MonkeyPatch.context() as m:
            def mock_get_response(chat_history, **kwargs):
                return json.dumps(tree_dict)

            m.setattr(
                "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
                mock_get_response,
            )

            result = generate_theme_tree("Test Theme", focus="", llm_model_config=config)

        assert result.label == "Root"

    def test_model_string_without_provider(self):
        """Test generating theme tree with model string without provider."""
        tree_dict = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
            "keywords": [],
        }

        with pytest.MonkeyPatch.context() as m:
            def mock_get_response(chat_history, **kwargs):
                return json.dumps(tree_dict)

            m.setattr(
                "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
                mock_get_response,
            )

            result = generate_theme_tree(
                "Test Theme",
                focus="",
                llm_model_config="gpt-4o-mini",
            )

        assert result.label == "Root"