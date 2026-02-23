"""Tests for MindMap utilities."""

import pytest
import json
import os
import tempfile
import pandas as pd

from llm_mindmap.mindmap.mindmap_utils import (
    prompts_dict,
    compose_themes_system_prompt,
    format_mindmap_to_dataframe,
    save_results_to_file,
    load_results_from_file,
)


class TestPromptsDict:
    """Test prompts_dict structure."""

    def test_theme_prompts_exist(self):
        """Test that theme prompts exist."""
        assert "theme" in prompts_dict

    def test_theme_prompts_structure(self):
        """Test that theme prompts have correct structure."""
        theme_prompts = prompts_dict["theme"]

        required_keys = [
            "qualifier",
            "user_prompt_message",
            "default_instructions",
            "enforce_structure_string",
        ]

        for key in required_keys:
            assert key in theme_prompts

    def test_theme_prompts_format_strings(self):
        """Test that theme prompts contain format placeholders."""
        theme_prompts = prompts_dict["theme"]

        assert "{main_theme}" in theme_prompts["default_instructions"]
        assert "{main_theme}" in theme_prompts["enforce_structure_string"]


class TestComposeThemesSystemPrompt:
    """Test compose_themes_system_prompt function."""

    def test_compose_without_focus(self):
        """Test composing system prompt without analyst focus."""
        result = compose_themes_system_prompt("AI Technology", "")

        assert "AI Technology" in result
        assert "professional analyst" in result
        assert "tree structure" in result

    def test_compose_with_focus(self):
        """Test composing system prompt with analyst focus."""
        result = compose_themes_system_prompt("AI Technology", "machine learning")

        assert "AI Technology" in result
        assert "machine learning" in result

    def test_compose_includes_structure_enforcement(self):
        """Test that composed prompt includes structure enforcement."""
        result = compose_themes_system_prompt("Test Theme", "")

        assert "JSON object" in result
        assert "label" in result
        assert "node" in result
        assert "summary" in result
        assert "children" in result


class TestFormatMindmapToDataframe:
    """Test format_mindmap_to_dataframe function."""

    def test_simple_table(self):
        """Test parsing simple pipe-delimited table."""
        text = """
        | Main Branches | Sub-Branches | Description |
        |---|---|---|
        | Branch 1 | Sub 1 | Description 1 |
        | Branch 1 | Sub 2 | Description 2 |
        """

        df = format_mindmap_to_dataframe(text)

        assert len(df) == 2
        assert "Main Branches" in df.columns
        assert "Sub-Branches" in df.columns
        assert "Description" in df.columns
        assert df.iloc[0]["Main Branches"] == "Branch 1"

    def test_removes_unnamed_columns(self):
        """Test that unnamed columns are removed."""
        text = """
        | Main Branches | Sub-Branches | Description |
        |---|---|---|
        | Branch 1 | Sub 1 | Description 1 |
        """

        df = format_mindmap_to_dataframe(text)

        assert not any("Unnamed" in col for col in df.columns)

    def test_missing_required_columns_raises_error(self):
        """Test that missing required columns raises ValueError."""
        text = """
        | Invalid | Column |
        |---|---|
        | Value | Value |
        """

        with pytest.raises(ValueError) as exc_info:
            format_mindmap_to_dataframe(text)

        assert "Missing required columns" in str(exc_info.value)

    def test_handles_extra_whitespace(self):
        """Test that extra whitespace is handled correctly."""
        text = """
        | Main Branches | Sub-Branches | Description |
        |---|---|---|
        |  Branch 1  |  Sub 1  |  Description 1  |
        """

        df = format_mindmap_to_dataframe(text)

        assert df.iloc[0]["Main Branches"] == "Branch 1"
        assert df.iloc[0]["Sub-Branches"] == "Sub 1"


class TestSaveAndLoadResults:
    """Test save_results_to_file and load_results_from_file functions."""

    def test_save_and_load_results(self):
        """Test saving and loading results."""
        results = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}

        with tempfile.TemporaryDirectory() as temp_dir:
            filename = "test_results.json"

            save_results_to_file(results, temp_dir, filename)
            loaded = load_results_from_file(temp_dir, filename)

            assert loaded == results

    def test_save_creates_directory(self):
        """Test that save creates directory if it doesn't exist."""
        results = {"test": "data"}

        with tempfile.TemporaryDirectory() as temp_dir:
            subdir = os.path.join(temp_dir, "new_subdir")
            filename = "test_results.json"

            assert not os.path.exists(subdir)

            save_results_to_file(results, subdir, filename)

            assert os.path.exists(subdir)

            loaded = load_results_from_file(subdir, filename)
            assert loaded == results

    def test_save_json_format(self):
        """Test that saved JSON is properly formatted."""
        results = {"key1": "value1", "key2": {"nested": "data"}}

        with tempfile.TemporaryDirectory() as temp_dir:
            filename = "test_results.json"

            save_results_to_file(results, temp_dir, filename)

            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "r") as f:
                content = f.read()

            assert content.startswith("{")
            assert content.endswith("}")

            parsed = json.loads(content)
            assert parsed == results