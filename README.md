# LLM MindMap

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen.svg)

A powerful Python library for generating hierarchical mind maps from any topic using Large Language Models (LLMs). Decompose complex themes into structured, hierarchical representations for analysis, visualization, and knowledge exploration.

## Overview

LLM MindMap transforms any topic into a structured, hierarchical mind map by leveraging the reasoning capabilities of modern LLMs. Whether you're exploring "Artificial Intelligence," analyzing "Climate Change," or breaking down complex business concepts, this tool provides an intuitive way to visualize relationships between ideas and concepts.

### Key Features

- **Topic Decomposition**: Generate hierarchical mind maps from any theme using LLM reasoning
- **Multiple Generation Modes**:
  - **One-shot**: Single-pass generation for quick results
  - **Refined**: Iterative enhancement of existing mind maps
  - **Dynamic**: Time-based evolution of mind maps across intervals
  - **Bootstrapped**: Parallel generation of multiple refined variants
- **Multiple LLM Providers**: Support for OpenRouter and iFlow with easy switching
- **Flexible Configuration**: Configure via environment variables, JSON file, or direct parameters
- **Rich Visualization**: Export to Graphviz PDFs, Plotly interactive treemaps
- **Data Export**: Export to JSON, pandas DataFrames for further analysis
- **Parallel Processing**: Generate multiple refined mindmaps concurrently
- **Robust Parsing**: Automatic JSON repair and validation for reliable LLM output handling

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/llm_mindmap.git
cd llm_mindmap

# Install dependencies
uv sync
```

### Optional Dependencies

For Plotly visualization:
```bash
uv pip install plotly
```

For Graphviz visualization, install the Graphviz binary:

**macOS:**
```bash
brew install graphviz
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install graphviz
```

**Windows:**
Download and install from [graphviz.org](https://graphviz.org/download/)

## Configuration

### Option 1: Local Configuration File (Recommended)

Create `.local/llms.json` (already in `.gitignore`):

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

### Option 2: Environment Variables

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
export IFLOW_API_KEY="your-iflow-api-key"
```

### Option 3: Direct Configuration

Pass configuration directly in code using dictionary or string format (see Usage examples below).

## Usage

### Basic Usage

```python
from llm_mindmap.mindmap import generate_theme_tree

# Use default configuration from .local/llms.json
mindmap = generate_theme_tree(
    main_theme="Artificial Intelligence",
    focus="machine learning applications"
)

# Display as text
mindmap.print()

# Visualize with Graphviz (creates PDF)
mindmap.visualize(engine="graphviz")

# Visualize with Plotly (interactive)
mindmap.visualize(engine="plotly")

# Export to JSON
mindmap.save_json("mindmap.json")

# Export to DataFrame
df = mindmap.to_dataframe()
print(df)
```

### Using Specific Provider

```python
# String format (provider::model)
config = "openrouter::gpt-4o-mini"

# Dictionary format with custom configuration
config = {
    "provider": "openrouter",
    "model": "gpt-4o-mini",
    "connection_config": {
        "api_key": "your-api-key",
        "base_url": "https://your-provider.com/v1"
    },
    "temperature": 0.0,
    "timeout": 60
}

mindmap = generate_theme_tree(
    main_theme="Climate Change",
    focus="renewable energy",
    llm_model_config=config
)
```

### Advanced Generation Modes

#### One-Shot Generation

```python
from llm_mindmap.mindmap import MindMapGenerator

generator = MindMapGenerator(
    llm_model_config_base="openrouter::gpt-4o-mini"
)

mindmap, results = generator.generate_one_shot(
    main_theme="Climate Change",
    focus="renewable energy",
    map_type="theme"
)
```

#### Refined Generation

Enhance an existing mind map with additional context:

```python
generator = MindMapGenerator(
    llm_model_config_base="openrouter::gpt-4o-mini",
    llm_model_config_reasoning="openrouter::gpt-4o"
)

initial_mindmap = '''
{
  "label": "Software Development",
  "node": 1,
  "summary": "Creating software applications",
  "children": []
}
'''

refined_mindmap, results = generator.generate_refined(
    main_theme="Software Development",
    focus="full-stack development",
    initial_mindmap=initial_mindmap,
    output_dir="./refined_mindmaps"
)
```

#### Parallel Bootstrapping

Generate multiple refined variants in parallel:

```python
results = generator.bootstrap_refined(
    main_theme="Climate Change",
    focus="renewable energy",
    initial_mindmap=initial_mindmap,
    n_elements=10,
    max_workers=4,
    output_dir="./bootstrapped_mindmaps"
)
```

#### Dynamic Generation Over Time

Evolve mind maps across time intervals:

```python
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
    month_names=month_names,
    output_dir="./dynamic_mindmaps"
)
```

### Data Extraction

```python
# Get all label-summary pairs
label_summaries = mindmap.get_label_summaries()

# Get terminal (leaf) nodes only
terminal_labels = mindmap.get_terminal_labels()
terminal_summaries = mindmap.get_terminal_summaries()

# Get parent-child relationships
parent_mapping = mindmap.get_label_to_parent_mapping()

# Convert to DataFrame (all nodes or leaves only)
df_all = mindmap.to_dataframe()
df_leaves = mindmap.to_dataframe(leaves_only=True)
```

### Custom Instructions

```python
custom_instructions = """
You are an expert in technology trends.
Generate a focused mind map with the following constraints:
- Maximum 3 levels of depth
- Each sub-theme must be practical and actionable
- Include at least 2 sub-themes for each main branch
"""

mindmap, results = generator.generate_one_shot(
    main_theme="Blockchain Technology",
    focus="enterprise applications",
    instructions=custom_instructions,
    map_type="theme"
)
```

## Examples

Run the included examples to see the library in action:

```bash
# Basic usage example
uv run examples/mindmap_demo.py

# Advanced usage examples
uv run examples/advanced_demo.py
```

## API Reference

### `generate_theme_tree()`

Simple one-shot mind map generation.

**Parameters:**
- `main_theme` (str): Primary theme to analyze
- `focus` (str, optional): Specific aspect to guide sub-theme generation
- `llm_model_config` (str|dict|LLMConfig, optional): LLM configuration

**Returns:** `MindMap` object

### `MindMap` Class

Hierarchical tree structure representing a mind map.

**Attributes:**
- `label` (str): Node name
- `node` (int): Unique identifier
- `summary` (str): Brief explanation
- `children` (list[MindMap]): Child nodes
- `keywords` (list[str]): Keywords

**Methods:**
- `print()`: Display as text tree
- `visualize(engine)`: Render with Graphviz or Plotly
- `save_json(filepath)`: Save to JSON file
- `to_json()`: Convert to JSON string
- `to_dataframe(leaves_only)`: Convert to pandas DataFrame
- `get_label_summaries()`: Extract all label-summary pairs
- `get_terminal_labels()`: Get leaf node labels
- `get_terminal_summaries()`: Get leaf node summaries
- `get_label_to_parent_mapping()`: Get parent-child relationships

### `MindMapGenerator` Class

Advanced generator with multiple generation modes.

**Methods:**
- `generate_one_shot()`: Single-pass generation
- `generate_refined()`: Iterative refinement
- `bootstrap_refined()`: Parallel generation of variants
- `generate_dynamic()`: Time-based evolution

## LLM Providers

### OpenRouter

Access to multiple LLM providers through a single API.

**Supported models:**
- `gpt-4o-mini`, `gpt-4o`
- `claude-3.5-sonnet`, `claude-3.5-haiku`
- And many more via [OpenRouter](https://openrouter.ai/models)

### iFlow

High-performance LLM API service.

**Supported models:**
- `qwen3-max`, `qwen3-plus`
- `deepseek-v3`
- `glm-4.6`, `glm-4.5`

See [iFlow API](https://iflow.cn) for available models.

## Project Structure

```
llm_mindmap/
├── llm/
│   ├── base.py              # LLMConfig, LLMProvider (ABC), LLMEngine
│   ├── openrouter.py        # OpenRouterProvider implementation
│   ├── iflow.py             # IFlowProvider implementation
│   └── utils.py             # Concurrent/parallel execution utilities
├── mindmap/
│   ├── mindmap.py           # MindMap dataclass, generate_theme_tree()
│   ├── mindmap_generator.py # MindMapGenerator (advanced modes)
│   └── mindmap_utils.py     # Prompts, save/load utilities
└── __init__.py

examples/
├── mindmap_demo.py          # Basic usage
└── advanced_demo.py         # Advanced features

tests/
├── llm_mindmap/
│   ├── llm/                 # LLM component tests
│   └── mindmap/             # MindMap component tests
└── examples/                # Integration tests
```

## Development

### Setting Up Development Environment

```bash
# Clone and install
git clone https://github.com/yourusername/llm_mindmap.git
cd llm_mindmap
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=llm_mindmap --cov-report=html

# Run specific test file
uv run pytest tests/llm_mindmap/mindmap/test_mindmap.py

# Run with verbose output
uv run pytest -v
```

### Code Style

The project uses standard Python conventions. When contributing:
- Follow PEP 8 style guidelines
- Add type hints for new functions
- Include docstrings for public APIs
- Write tests for new features

## Output

All generated outputs are saved to the `_out/` directory:
- `mindmap.gv` - Graphviz source file
- `mindmap.gv.pdf` - Rendered PDF visualization
- `mindmap_output.json` - JSON export
- DataFrames are displayed in console and can be saved to CSV

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`uv run pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs. actual behavior
- Environment details (Python version, OS, etc.)

## Acknowledgments

Built with:
- [Pydantic](https://pydantic-docs.helpmanual.io/) for configuration validation
- [Graphviz](https://graphviz.org/) for visualization
- [pandas](https://pandas.pydata.org/) for data manipulation
- [tqdm](https://tqdm.github.io/) for progress bars
- [json-repair](https://github.com/mangiucugna/json_repair) for robust JSON parsing

