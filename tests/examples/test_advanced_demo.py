Integration tests for advanced_demo.py.

Tests the advanced usage examples with mocked LLM responses.
"""

import pytest
import json
import tempfile

from llm_mindmap.mindmap import MindMapGenerator


def test_advanced_demo_one_shot_generation():
    """Test one-shot generation as used in advanced_demo.py."""

    tree_dict = {
        "label": "Climate Change",
        "node": 1,
        "summary": "Climate change topic",
        "children": [
            {
                "label": "Renewable Energy",
                "node": 2,
                "summary": "Clean energy sources",
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

        config = {
            "provider": "openrouter",
            "model": "gpt-4o-mini",
            "connection_config": {},
        }

        generator = MindMapGenerator(llm_model_config_base=config)

        mindmap, results = generator.generate_one_shot(
            main_theme="Climate Change",
            focus="renewable energy",
            map_type="theme",
        )

    assert isinstance(mindmap, MindMap)
    assert mindmap.label == "Climate Change"
    assert "mindmap_text" in results
    assert "mindmap_df" in results


def test_advanced_demo_refined_generation():
    """Test refined generation as used in advanced_demo.py."""

    initial_dict = {
        "label": "Software Development",
        "node": 1,
        "summary": "Creating software",
        "children": [
            {
                "label": "Frontend",
                "node": 2,
                "summary": "UI development",
                "children": [],
            }
        ],
    }

    refined_dict = {
        "label": "Software Development",
        "node": 1,
        "summary": "Creating software",
        "children": [
            {
                "label": "Frontend",
                "node": 2,
                "summary": "UI development",
                "children": [],
            },
            {
                "label": "Backend",
                "node": 3,
                "summary": "Server development",
                "children": [],
            },
        ],
    }

    with pytest.MonkeyPatch.context() as m:
        def mock_get_response(messages, **kwargs):
            return json.dumps(refined_dict)

        m.setattr(
            "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
            mock_get_response,
        )

        generator = MindMapGenerator(
            llm_model_config_base="openrouter::gpt-4o-mini",
            llm_model_config_reasoning="openrouter::gpt-4o",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            mindmap, results = generator.generate_refined(
                main_theme="Software Development",
                focus="full-stack development",
                initial_mindmap=json.dumps(initial_dict),
                output_dir=temp_dir,
                filename="refined_mindmap.json",
                map_type="theme",
            )

    assert isinstance(mindmap, MindMap)
    assert len(mindmap.children) == 2
    assert mindmap.children[0].label == "Frontend"
    assert mindmap.children[1].label == "Backend"


def test_advanced_demo_custom_instructions():
    """Test custom instructions as used in advanced_demo.py."""

    tree_dict = {
        "label": "Blockchain Technology",
        "node": 1,
        "summary": "Blockchain tech",
        "children": [],
    }

    with pytest.MonkeyPatch.context() as m:
        def mock_get_response(messages, **kwargs):
            assert "expert in technology trends" in messages[0]["content"]
            return json.dumps(tree_dict)

        m.setattr(
            "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
            mock_get_response,
        )

        custom_instructions = """
        You are an expert in technology trends.
        Generate a focused mind map with the following constraints:
        """

        generator = MindMapGenerator(
            llm_model_config_base="openrouter::gpt-4o-mini"
        )

        mindmap, results = generator.generate_one_shot(
            main_theme="Blockchain Technology",
            focus="enterprise applications",
            instructions=custom_instructions,
            map_type="theme",
        )

    assert isinstance(mindmap, MindMap)


def test_advanced_demo_data_extraction():
    """Test data extraction as used in advanced_demo.py."""

    tree_dict = {
        "label": "Digital Marketing",
        "node": 1,
        "summary": "Digital marketing",
        "children": [
            {
                "label": "Social Media",
                "node": 2,
                "summary": "Social platforms",
                "children": [],
            }
        ],
    }

    with pytest.MonkeyPatch.context() as m:
        def mock_get_response(chat_history, **kwargs):
            return json.dumps(tree_dict)

        m.setattr(
            "llm_mindmap.llm.llm_engine.LLMEngine.get_response",
            mock_get_response,
        )

        from llm_mindmap.mindmap import generate_theme_tree

        mindmap = generate_theme_tree(
            main_theme="Digital Marketing",
            focus="social media",
            llm_model_config="openrouter::gpt-4o-mini",
        )

    label_summaries = mindmap.get_label_summaries()
    assert len(label_summaries) == 2

    terminal_details = mindmap.get_terminal_label_summaries()
    assert len(terminal_details) == 1

    parent_mapping = mindmap.get_label_to_parent_mapping()
    assert "Social Media" in parent_mapping
    assert parent_mapping["Social Media"] == "Digital Marketing"

    df = mindmap.to_dataframe()
    assert len(df) == 1

    df_leaves = mindmap.to_dataframe(leaves_only=True)
    assert len(df_leaves) == 1