"""Basic usage example for llm-mindmap.

This example demonstrates how to:
- Generate a mind map from a topic using generate_theme_tree()
- Display the mind map as text
- Visualize the mind map using graphviz
- Export the mind map to JSON and DataFrame
"""

import os
from pathlib import Path

from llm_mindmap.mindmap import generate_theme_tree


def setup_output_dir():
    """Create output directory if it doesn't exist."""
    output_dir = Path("_out")
    output_dir.mkdir(exist_ok=True)
    return output_dir


def main():
    """Run basic mind map generation example."""

    # Setup output directory
    output_dir = setup_output_dir()
    print(f"Output directory: {output_dir}")
    print()

    # Configure LLM
    # Option 1: Use default model (reads from .local/llms.json)
    llm_config = None

    # Option 2: Use string format (provider::model)
    # llm_config = "openrouter::gpt-4o-mini"

    # Option 3: Use dict format with custom base URL
    # llm_config = {
    #     "provider": "openrouter",
    #     "model": "gpt-4o-mini",
    #     "connection_config": {
    #         "api_key": "your-api-key",
    #         "base_url": "https://your-provider.com/v1"
    #     }
    # }

    # Option 4: Use iFlow provider explicitly
    # llm_config = "iflow::gpt-4o-mini"

    # Generate mind map
    main_theme = "Artificial Intelligence"
    focus = "machine learning applications"

    print(f"[1/6] Generating mind map for: {main_theme}")
    if focus:
        print(f"      Focus: {focus}")
    print("      Calling LLM API...")
    print()

    mindmap = generate_theme_tree(
        main_theme=main_theme,
        focus=focus,
        llm_model_config=llm_config,
    )

    print("      ✓ Mind map generated successfully")
    print()

    # Display as text
    print("[2/6] Mind Map Structure:")
    print("-" * 50)
    mindmap.print()
    print()

    # Extract terminal nodes
    print("[3/6] Terminal Nodes:")
    print("-" * 50)
    terminal_labels = mindmap.get_terminal_labels()
    for i, label in enumerate(terminal_labels, 1):
        print(f"{i}. {label}")
    print()

    # Visualize using graphviz
    print("[4/6] Generating visualization...")
    old_cwd = os.getcwd()
    try:
        # Change to output directory for visualization output
        os.chdir(output_dir)
        mindmap.visualize(engine="graphviz")
        viz_file = output_dir / "mindmap.gv.pdf"
        print(f"      ✓ Visualization saved to: {viz_file}")
    except ImportError:
        print("      ✗ Graphviz not available. Install graphviz for visualization.")
    except Exception as e:
        if "ExecutableNotFound" in str(type(e)) or "dot" in str(e).lower():
            print("      ✗ Graphviz binary not found. Install graphviz (e.g., 'brew install graphviz').")
        else:
            print(f"      ✗ Visualization error: {e}")
    finally:
        # Always change back to original directory
        os.chdir(old_cwd)
    print()

    # Export to JSON
    print("[5/6] Exporting to JSON...")
    output_file = output_dir / "mindmap_output.json"
    mindmap.save_json(str(output_file))
    print(f"      ✓ Mind map saved to: {output_file}")
    print()

    # Export to DataFrame
    print("[6/6] DataFrame:")
    print("-" * 50)
    df = mindmap.to_dataframe()
    print(df.to_string(index=False))
    print()

    # Get label summaries
    print("Label Summaries:")
    print("-" * 50)
    label_summaries = mindmap.get_label_summaries()
    for label, summary in label_summaries.items():
        print(f"{label}: {summary}")
    print()

    print("=" * 50)
    print("All tasks completed!")
    print(f"Output files saved to: {output_dir}")
    print("=" * 50)


if __name__ == "__main__":
    main()