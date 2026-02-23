# llm-mindmap

LLM-powered mind map generator for topic decomposition.

## Installation

```bash
uv sync
```

## Usage

```python
from llm_mindmap.mindmap import generate_theme_tree

# Configure LLM (use OpenRouter or iFlow)
llm_config = {
    "provider": "openrouter",
    "model": "gpt-4o-mini",
    "connection_config": {
        "api_key": "your-api-key"
    }
}

# Generate mind map
mindmap = generate_theme_tree(
    main_theme="Artificial Intelligence",
    focus="machine learning",
    llm_model_config=llm_config
)

# Display
mindmap.print()

# Visualize
mindmap.visualize(engine="graphviz")
```

## License

MIT