"""Advanced usage example for llm-mindmap.

This example demonstrates:
- Using MindMapGenerator for advanced generation modes
- One-shot generation with custom instructions
- Refined generation with initial mind map
- Working with different LLM providers
- Handling errors and edge cases
"""

import json
import tempfile

from llm_mindmap.mindmap import MindMapGenerator, generate_theme_tree


def example_one_shot_generation():
    """Example: One-shot mind map generation."""

    print("Example 1: One-Shot Generation")
    print("=" * 60)

    # Configure LLM
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        config = {
            "provider": "openrouter",
            "model": "gpt-4o-mini",
            "connection_config": {
                "api_key": api_key,
            },
        }
    else:
        # Use iFlow from .local/llms.json
        config = None  # Will use default from .local/llms.json

    # Initialize generator
    generator = MindMapGenerator(
        llm_model_config_base=config,
    )

    # Generate in one shot
    main_theme = "Climate Change"
    focus = "renewable energy"

    print(f"Generating mind map for: {main_theme}")
    print(f"Focus: {focus}")
    print()

    mindmap, results = generator.generate_one_shot(
        main_theme=main_theme,
        focus=focus,
        map_type="theme",
    )

    # Display results
    print("Generated Mind Map:")
    print("-" * 40)
    mindmap.print()
    print()

    print(f"Nodes: {len(mindmap.get_summaries())}")
    print(f"Terminal nodes: {len(mindmap.get_terminal_labels())}")
    print()


def example_refined_generation():
    """Example: Refined mind map generation."""

    print("Example 2: Refined Generation")
    print("=" * 60)

    # Configure LLM with separate reasoning model
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        base_config = "openrouter::gpt-4o-mini"
        reasoning_config = "openrouter::gpt-4o"
    else:
        # Use iFlow from .local/llms.json
        base_config = None
        reasoning_config = None

    # Initialize generator
    generator = MindMapGenerator(
        llm_model_config_base=base_config,
        llm_model_config_reasoning=reasoning_config,
    )

    # Create initial mind map
    initial_dict = {
        "label": "Software Development",
        "node": 1,
        "summary": "Creating software applications",
        "children": [
            {
                "label": "Frontend",
                "node": 2,
                "summary": "User interface development",
                "children": [],
            }
        ],
    }

    initial_json = json.dumps(initial_dict)

    print("Initial Mind Map:")
    print("-" * 40)
    print(initial_json)
    print()

    # Refine the mind map
    print("Refining mind map...")
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        refined_mindmap, results = generator.generate_refined(
            main_theme="Software Development",
            focus="full-stack development",
            initial_mindmap=initial_json,
            output_dir=temp_dir,
            filename="refined_mindmap.json",
            map_type="theme",
        )

        if refined_mindmap:
            print("Refined Mind Map:")
            print("-" * 40)
            refined_mindmap.print()
            print()

            print(f"Nodes: {len(refined_mindmap.get_summaries())}")
            print(f"Terminal nodes: {len(refined_mindmap.get_terminal_labels())}")
        else:
            print("Refinement failed:")
            print(results.get("error", "Unknown error"))
    print()


def example_custom_instructions():
    """Example: Using custom instructions."""

    print("Example 3: Custom Instructions")
    print("=" * 60)

    # Configure LLM
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        config = "openrouter::gpt-4o-mini"
    else:
        # Use iFlow from .local/llms.json
        config = None

    # Initialize generator
    generator = MindMapGenerator(
        llm_model_config_base=config,
    )

    # Custom instructions
    custom_instructions = """
    You are an expert in technology trends.
    Generate a focused mind map with the following constraints:
    - Maximum 3 levels of depth
    - Each sub-theme must be practical and actionable
    - Include at least 2 sub-themes for each main branch
    """

    print("Using custom instructions:")
    print("-" * 40)
    print(custom_instructions.strip())
    print()

    # Generate with custom instructions
    mindmap, results = generator.generate_one_shot(
        main_theme="Blockchain Technology",
        focus="enterprise applications",
        instructions=custom_instructions,
        map_type="theme",
    )

    print("Generated Mind Map:")
    print("-" * 40)
    mindmap.print()
    print()


def example_data_extraction():
    """Example: Extracting data from mind map."""

    print("Example 4: Data Extraction")
    print("=" * 60)

    # Generate a simple mind map
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        config = "openrouter::gpt-4o-mini"
    else:
        # Use iFlow from .local/llms.json
        config = None

    mindmap = generate_theme_tree(
        main_theme="Digital Marketing",
        focus="social media",
        llm_model_config=config,
    )

    # Extract various data
    print("Label-Summary Mapping:")
    print("-" * 40)
    label_summaries = mindmap.get_label_summaries()
    for label, summary in label_summaries.items():
        print(f"{label}: {summary}")
    print()

    print("Terminal Node Details:")
    print("-" * 40)
    terminal_details = mindmap.get_terminal_label_summaries()
    for label, summary in terminal_details.items():
        print(f"{label}: {summary}")
    print()

    print("Parent-Child Mapping:")
    print("-" * 40)
    parent_mapping = mindmap.get_label_to_parent_mapping()
    for child, parent in parent_mapping.items():
        print(f"{child} -> {parent}")
    print()

    # Convert to DataFrame
    df = mindmap.to_dataframe()
    print("DataFrame (all nodes):")
    print("-" * 40)
    print(df.to_string(index=False))
    print()

    # Convert to DataFrame (leaves only)
    df_leaves = mindmap.to_dataframe(leaves_only=True)
    print("DataFrame (terminal nodes only):")
    print("-" * 40)
    print(df_leaves.to_string(index=False))
    print()


def main():
    """Run all advanced examples."""

    print("Advanced llm-mindmap Examples")
    print("=" * 60)
    print()

    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Warning: OPENROUTER_API_KEY not set.")
        print("Set it with: export OPENROUTER_API_KEY=your-key")
        print()
        print("Using iFlow from .local/llms.json configuration...")
        print()

    # Run examples
    try:
        example_one_shot_generation()
    except Exception as e:
        print(f"Error in one-shot generation: {e}")
        print()

    try:
        example_refined_generation()
    except Exception as e:
        print(f"Error in refined generation: {e}")
        print()

    try:
        example_custom_instructions()
    except Exception as e:
        print(f"Error in custom instructions: {e}")
        print()

    try:
        example_data_extraction()
    except Exception as e:
        print(f"Error in data extraction: {e}")
        print()

    print("All examples completed!")


if __name__ == "__main__":
    import os
    main()