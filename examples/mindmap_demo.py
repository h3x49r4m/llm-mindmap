"""Basic usage example for llm-mindmap.

This example demonstrates how to:
- Generate a mind map from a topic using generate_theme_tree()
- Display the mind map as text
- Visualize the mind map using graphviz
- Export the mind map to JSON and DataFrame
"""

import os

from llm_mindmap.mindmap import generate_theme_tree


def main():
    """Run basic mind map generation example."""
    
    # Configure LLM
    # Option 1: Use string format (provider::model)
    llm_config = "openrouter::gpt-4o-mini"

    # Option 2: Use dict format with custom base URL
    # llm_config = {
    #     "provider": "openrouter",
    #     "model": "gpt-4o-mini",
    #     "connection_config": {
    #         "api_key": "your-api-key",
    #         "base_url": "https://your-provider.com/v1"
    #     }
    # }

    # Option 3: Use iFlow provider
    # llm_config = "iflow::gpt-4o-mini"

    # Generate mind map
    main_theme = "Artificial Intelligence"
    focus = "machine learning applications"

    print(f"Generating mind map for: {main_theme}")
    if focus:
        print(f"Focus: {focus}")
    print()

    mindmap = generate_theme_tree(
        main_theme=main_theme,
        focus=focus,
        llm_model_config=llm_config,
    )

    # Display as text
    print("Mind Map Structure:")
    print("-" * 50)
    mindmap.print()
    print()

    # Extract terminal nodes
    print("Terminal Nodes:")
    print("-" * 50)
    terminal_labels = mindmap.get_terminal_labels()
    for i, label in enumerate(terminal_labels, 1):
        print(f"{i}. {label}")
    print()

    # Visualize using graphviz
    print("Generating visualization...")
    try:
        mindmap.visualize(engine="graphviz")
        print("Visualization saved as 'mindmap.gv.pdf'")
    except ImportError:
        print("Graphviz not available. Install graphviz for visualization.")
    print()

    # Export to JSON
    output_file = "mindmap_output.json"
    mindmap.save_json(output_file)
    print(f"Mind map saved to: {output_file}")
    print()

    # Export to DataFrame
    df = mindmap.to_dataframe()
    print("DataFrame:")
    print("-" * 50)
    print(df.to_string(index=False))
    print()

    # Get label summaries
    label_summaries = mindmap.get_label_summaries()
    print("Label Summaries:")
    print("-" * 50)
    for label, summary in label_summaries.items():
        print(f"{label}: {summary}")
    print()


if __name__ == "__main__":
    main()