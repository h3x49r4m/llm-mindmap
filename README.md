# llm-mindmap

LLM-powered mind map generator for topic decomposition and hierarchical analysis.

## Features

- **Topic Decomposition**: Generate hierarchical mind maps from any theme using LLM
- **Multiple LLM Providers**: Support for OpenRouter and iFlow
- **Flexible Configuration**: Configure via environment variables, JSON file, or direct parameters
- **Multiple Generation Modes**: One-shot, refined, and dynamic generation
- **Data Export**: Export to JSON, DataFrame, and visualize with Graphviz or Plotly
- **Parallel Processing**: Generate multiple refined mindmaps in parallel

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd llm_mindmap

# Install dependencies
uv sync
```

## Configuration

### Option 1: Environment Variables

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
# or
export IFLOW_API_KEY="your-iflow-api-key"
```

### Option 2: Local Configuration File

Create `.local/llms.json` (already in .gitignore):

```json
{
  "default_provider": "iflow",
  "default_model": "qwen3-max",
  "providers": {
    "openrouter": {
      "api_key": "your-openrouter-api-key",
      "base_url": "https://openrouter.ai/api/v1"
    },
    "iflow": {
      "api_key": "your-iflow-api-key",
      "base_url": "https://apis.iflow.cn"
    }
  }
}
```

## Usage

### Basic Usage

```python
from llm_mindmap.mindmap import generate_theme_tree

# Use default configuration from .local/llms.json
mindmap = generate_theme_tree(
    main_theme="Artificial Intelligence",
    focus="machine learning"
)

# Display as text
mindmap.print()

# Visualize with Graphviz
mindmap.visualize(engine="graphviz")

# Export to JSON
mindmap.save_json("mindmap.json")

# Export to DataFrame
df = mindmap.to_dataframe()
```

### Using Specific Provider

```python
# String format (provider::model)
config = "openrouter::gpt-4o-mini"

# Dictionary format
config = {
    "provider": "openrouter",
    "model": "gpt-4o-mini",
    "connection_config": {
        "api_key": "your-api-key",
        "base_url": "https://your-provider.com/v1"
    }
}

mindmap = generate_theme_tree(
    main_theme="Climate Change",
    focus="renewable energy",
    llm_model_config=config
)
```

### Advanced Generation

```python
from llm_mindmap.mindmap import MindMapGenerator

# Initialize generator
generator = MindMapGenerator(
    llm_model_config_base="openrouter::gpt-4o-mini",
    llm_model_config_reasoning="openrouter::gpt-4o"
)

# One-shot generation
mindmap, results = generator.generate_one_shot(
    main_theme="Climate Change",
    focus="renewable energy",
    map_type="theme"
)

# Refined generation with initial mind map
initial_mindmap = '{"label": "Software Development", "node": 1, "summary": "Creating software applications", "children": []}'
refined_mindmap, results = generator.generate_refined(
    main_theme="Software Development",
    focus="modern practices",
    initial_mindmap=initial_mindmap
)

# Parallel generation of multiple refined mindmaps
results = generator.bootstrap_refined(
    main_theme="Climate Change",
    focus="renewable energy",
    initial_mindmap=initial_mindmap,
    n_elements=10,
    max_workers=4
)

# Dynamic generation over time intervals
month_intervals = [
    ("2024-01-01", "2024-01-31"),
    ("2024-02-01", "2024-02-29"),
    ("2024-03-01", "2024-03-31")
]
month_names = ["January", "February", "March"]

mindmaps, results = generator.generate_dynamic(
    main_theme="Climate Change",
    focus="renewable energy",
    month_intervals=month_intervals,
    month_names=month_names
)
```

## Examples

```bash
# Basic example
uv run examples/mindmap_demo.py

# Advanced examples
uv run examples/advanced_demo.py
```

## Output

All outputs are saved to the `_out/` directory:
- `mindmap.gv` - Graphviz visualization file
- `mindmap_output.json` - JSON export
- DataFrames are displayed in the console

## LLM Providers

### OpenRouter

Supported models include `gpt-4o-mini`, `gpt-4o`, `claude-3.5-sonnet`, and more.

### iFlow

Supported models include `qwen3-max`, `deepseek-v3`, `glm-4.6`, and more. See [iFlow API](https://iflow.cn) for available models.

## Development

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=llm_mindmap --cov-report=html
```

## License

MIT