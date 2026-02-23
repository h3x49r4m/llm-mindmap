Integration tests for mindmap_demo.py.

Tests the basic usage example with mocked LLM responses.
"""

import pytest
import json

from llm_mindmap.mindmap import MindMap


def test_mindmap_demo_generate_theme_tree():
    """Test generate_theme_tree function as used in mindmap_demo.py."""

    tree_dict = {
        "label": "Artificial Intelligence",
        "node": 1,
        "summary": "AI technology",
        "children": [
            {
                "label": "Machine Learning",
                "node": 2,
                "summary": "ML algorithms",
                "children": [
                    {
                        "label": "Supervised Learning",
                        "node": 3,
                        "summary": "Learning with labels",
                        "children": [],
                    }
                ],
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
            main_theme="Artificial Intelligence",
            focus="machine learning applications",
            llm_model_config="openrouter::gpt-4o-mini",
        )

    assert isinstance(mindmap, MindMap)
    assert mindmap.label == "Artificial Intelligence"
    assert len(mindmap.children) == 1


def test_mindmap_demo_print():
    """Test print method as used in mindmap_demo.py."""

    mindmap = MindMap(
        label="Root",
        node=1,
        summary="Root node",
        children=[
            MindMap(label="Child", node=2, summary="Child node", children=[])
        ],
    )

    output = mindmap.as_string()

    assert "Root" in output
    assert "Child" in output
    assert "└──" in output


def test_mindmap_demo_get_terminal_labels():
    """Test get_terminal_labels as used in mindmap_demo.py."""

    child = MindMap(label="Child", node=2, summary="Child node", children=[])
    mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

    terminal_labels = mindmap.get_terminal_labels()

    assert len(terminal_labels) == 1
    assert "Child" in terminal_labels


def test_mindmap_demo_save_json():
    """Test save_json method as used in mindmap_demo.py."""

    import tempfile
    import os

    mindmap = MindMap(label="Root", node=1, summary="Root node")

    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "mindmap_output.json")
        mindmap.save_json(output_file)

        assert os.path.exists(output_file)

        with open(output_file, "r") as f:
            data = json.load(f)

        assert data["label"] == "Root"
        assert data["node"] == 1


def test_mindmap_demo_to_dataframe():
    """Test to_dataframe method as used in mindmap_demo.py."""

    child = MindMap(label="Child", node=2, summary="Child node", children=[])
    mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

    df = mindmap.to_dataframe()

    assert len(df) == 1
    assert df.iloc[0]["Label"] == "Child"
    assert df.iloc[0]["Parent"] == "Root"


def test_mindmap_demo_get_label_summaries():
    """Test get_label_summaries as used in mindmap_demo.py."""

    child = MindMap(label="Child", node=2, summary="Child node")
    mindmap = MindMap(label="Root", node=1, summary="Root node", children=[child])

    label_summaries = mindmap.get_label_summaries()

    assert len(label_summaries) == 2
    assert "Root" in label_summaries
    assert "Child" in label_summaries
    assert label_summaries["Root"] == "Root node"