"""Tests for MindMapGenerator."""

import pytest
import json
import tempfile

from llm_mindmap.mindmap.mindmap_generator import MindMapGenerator
from llm_mindmap.mindmap.mindmap import MindMap


class TestMindMapGenerator:
    """Test MindMapGenerator class."""

    def test_init_with_string_config(self):
        """Test initializing with string config."""
        generator = MindMapGenerator(
            llm_model_config_base="openrouter::gpt-4o-mini"
        )

        assert generator.llm_model_config_base.model == "gpt-4o-mini"
        assert generator.llm_model_config_base.provider == "openrouter"

    def test_init_with_dict_config(self):
        """Test initializing with dict config."""
        config = {
            "provider": "openrouter",
            "model": "gpt-4o-mini",
            "connection_config": {},
        }

        generator = MindMapGenerator(llm_model_config_base=config)

        assert generator.llm_model_config_base.model == "gpt-4o-mini"
        assert generator.llm_model_config_base.provider == "openrouter"

    def test_init_with_separate_reasoning_config(self):
        """Test initializing with separate reasoning config."""
        generator = MindMapGenerator(
            llm_model_config_base="openrouter::gpt-4o-mini",
            llm_model_config_reasoning="openrouter::gpt-4o",
        )

        assert generator.llm_model_config_base.model == "gpt-4o-mini"
        assert generator.llm_model_config_reasoning.model == "gpt-4o"

    def test_compose_base_message(self):
        """Test composing base message."""
        generator = MindMapGenerator()

        messages = generator.compose_base_message(
            main_theme="AI Technology",
            focus="machine learning",
            map_type="theme",
            instructions=None,
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "AI Technology" in messages[1]["content"]

    def test_compose_base_message_with_custom_instructions(self):
        """Test composing base message with custom instructions."""
        generator = MindMapGenerator()

        custom_instructions = "Custom instructions for testing."

        messages = generator.compose_base_message(
            main_theme="Test Theme",
            focus="",
            map_type="theme",
            instructions=custom_instructions,
        )

        assert custom_instructions in messages[0]["content"]

    def test_parse_llm_to_themetree_valid_json(self):
        """Test parsing valid JSON response."""
        generator = MindMapGenerator()

        tree_dict = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
        }

        mindmap_text = json.dumps(tree_dict)
        result = generator._parse_llm_to_themetree(mindmap_text)

        assert isinstance(result, MindMap)
        assert result.label == "Root"

    def test_parse_llm_to_themetree_with_code_blocks(self):
        """Test parsing JSON with markdown code blocks."""
        generator = MindMapGenerator()

        tree_dict = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
        }

        mindmap_text = f"```json\n{json.dumps(tree_dict)}\n```"
        result = generator._parse_llm_to_themetree(mindmap_text)

        assert result.label == "Root"

    def test_parse_llm_to_themetree_invalid_json(self):
        """Test parsing invalid JSON raises ValueError."""
        generator = MindMapGenerator()

        mindmap_text = "This is not valid JSON"

        with pytest.raises(ValueError) as exc_info:
            generator._parse_llm_to_themetree(mindmap_text)

        assert "Failed to parse" in str(exc_info.value)

    def test_parse_llm_to_themetree_missing_required_field(self):
        """Test parsing JSON missing required field raises ValueError."""
        generator = MindMapGenerator()

        invalid_dict = {
            "label": "Root",
            "summary": "Root node",
        }

        mindmap_text = json.dumps(invalid_dict)

        with pytest.raises(ValueError) as exc_info:
            generator._parse_llm_to_themetree(mindmap_text)

        assert "Missing or null required field" in str(exc_info.value)

    def test_generate_one_shot(self):
        """Test generating mind map in one shot."""
        tree_dict = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [
                {
                    "label": "Child",
                    "node": 2,
                    "summary": "Child node",
                    "children": [],
                }
            ],
        }

        with pytest.MonkeyPatch.context() as m:
            def mock_get_response(messages, **kwargs):
                return json.dumps(tree_dict)

            m.setattr(
                "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
                mock_get_response,
            )

            generator = MindMapGenerator()
            mindmap, results = generator.generate_one_shot(
                main_theme="Test Theme",
                focus="",
                map_type="theme",
            )

        assert isinstance(mindmap, MindMap)
        assert mindmap.label == "Root"
        assert "mindmap_text" in results
        assert "mindmap_df" in results
        assert "mindmap_json" in results

    def test_generate_one_shot_with_focus(self):
        """Test generating mind map with focus."""
        tree_dict = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
        }

        with pytest.MonkeyPatch.context() as m:
            def mock_get_response(messages, **kwargs):
                assert "machine learning" in messages[0]["content"]
                return json.dumps(tree_dict)

            m.setattr(
                "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
                mock_get_response,
            )

            generator = MindMapGenerator()
            mindmap, results = generator.generate_one_shot(
                main_theme="AI Technology",
                focus="machine learning",
                map_type="theme",
            )

        assert mindmap.label == "Root"

    def test_generate_refined(self):
        """Test refining an initial mind map."""
        initial_tree = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
        }

        refined_tree = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [
                {
                    "label": "New Child",
                    "node": 2,
                    "summary": "Added child",
                    "children": [],
                }
            ],
        }

        with pytest.MonkeyPatch.context() as m:
            def mock_get_response(messages, **kwargs):
                return json.dumps(refined_tree)

            m.setattr(
                "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
                mock_get_response,
            )

            generator = MindMapGenerator()

            with tempfile.TemporaryDirectory() as temp_dir:
                mindmap, results = generator.generate_refined(
                    main_theme="Test Theme",
                    focus="",
                    initial_mindmap=json.dumps(initial_tree),
                    output_dir=temp_dir,
                    filename="test_refined.json",
                    map_type="theme",
                )

        assert isinstance(mindmap, MindMap)
        assert len(mindmap.children) == 1
        assert mindmap.children[0].label == "New Child"

    def test_generate_refined_parse_error(self):
        """Test refine handles parse errors gracefully."""
        initial_tree = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
        }

        with pytest.MonkeyPatch.context() as m:
            def mock_get_response(messages, **kwargs):
                return "Invalid JSON response"

            m.setattr(
                "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
                mock_get_response,
            )

            generator = MindMapGenerator()

            with tempfile.TemporaryDirectory() as temp_dir:
                mindmap, results = generator.generate_refined(
                    main_theme="Test Theme",
                    focus="",
                    initial_mindmap=json.dumps(initial_tree),
                    output_dir=temp_dir,
                    filename="test_refined.json",
                    map_type="theme",
                )

        assert mindmap is None
        assert "error" in results

    def test_generate_refined_saves_to_file(self):
        """Test that refined results are saved to file."""
        initial_tree = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
        }

        refined_tree = {
            "label": "Root",
            "node": 1,
            "summary": "Root node",
            "children": [],
        }

        with pytest.MonkeyPatch.context() as m:
            def mock_get_response(messages, **kwargs):
                return json.dumps(refined_tree)

            m.setattr(
                "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
                mock_get_response,
            )

            generator = MindMapGenerator()

            with tempfile.TemporaryDirectory() as temp_dir:
                filename = "test_output.json"
                mindmap, results = generator.generate_refined(
                    main_theme="Test Theme",
                    focus="",
                    initial_mindmap=json.dumps(initial_tree),
                    output_dir=temp_dir,
                    filename=filename,
                    map_type="theme",
                )

                import os

                filepath = os.path.join(temp_dir, filename)
                assert os.path.exists(filepath)

                with open(filepath, "r") as f:
                    saved = json.load(f)

                assert "mindmap_json" in saved