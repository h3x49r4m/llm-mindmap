# LLM MindMap Architecture

## Project Structure

```
src/
├── llm/
│   ├── __init__.py
│   ├── base.py              # LLMConfig, LLMProvider (ABC), LLMEngine
│   ├── openrouter.py        # OpenRouterProvider implementation
│   ├── iflow.py             # IFlowProvider implementation
│   └── utils.py             # run_concurrent_prompts(), run_parallel_prompts()
├── mindmap/
│   ├── __init__.py
│   ├── mindmap.py           # MindMap dataclass, generate_theme_tree()
│   ├── mindmap_generator.py # MindMapGenerator (one-shot, refined)
│   └── mindmap_utils.py     # prompts_dict (theme only), save/load utilities
└── __init__.py

tests/
├── src/
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── test_base.py         # LLMConfig validation, provider loading
│   │   ├── test_openrouter.py   # OpenRouter provider tests
│   │   ├── test_iflow.py        # IFlow provider tests
│   │   └── test_utils.py        # Concurrent execution tests
│   └── mindmap/
│       ├── __init__.py
│       ├── test_mindmap.py      # MindMap parsing, validation, conversion
│       ├── test_mindmap_generator.py  # Generation mode tests
│       └── test_mindmap_utils.py      # Prompts, utilities tests
└── examples/
    ├── __init__.py
    ├── test_mindmap_demo.py     # Basic usage integration test
    └── test_advanced_demo.py    # Advanced features integration test

examples/
├── __init__.py
├── mindmap_demo.py          # Basic: topic → LLM → mindmap → display
└── advanced_demo.py         # Advanced: refined generation, visualization, export

pyproject.toml               # Dependencies (llm-clients-python, pydantic, graphviz, pandas, tqdm)
```

## Dependencies

- **llm-clients-python** - OpenRouter & IFlow clients
- **pydantic** - Configuration validation
- **graphviz** - MindMap visualization
- **pandas** - DataFrame export
- **tqdm** - Progress bars
- **pytest** - Testing framework

## Core Flow

```
User Input (topic, focus)
    ↓
LLMConfig (provider, model, connection_config)
    ↓
LLMEngine (loads OpenRouter or IFlow provider)
    ↓
MindMapGenerator
    ├─ generate_one_shot() → LLM → MindMap
    └─ generate_refined() → LLM (proposes) → LLM (refines) → MindMap
    ↓
MindMap object
    ├─ print() → Text output
    ├─ visualize() → graphviz/plotly
    ├─ to_dataframe() → pandas DataFrame
    └─ save_json() → JSON file
```

## LLM Layer

### `src/llm/base.py`

**Components:**
- `LLMConfig` (Pydantic model)
  - `model`: str - Model identifier
  - `provider`: str - Provider name (openrouter, iflow)
  - `connection_config`: dict - API credentials
  - `temperature`: float | None - Sampling temperature
  - `response_format`: dict - JSON response format
  - `timeout`: int - Request timeout

- `LLMProvider` (ABC)
  - `get_response()` - Single response
  - `get_tools_response()` - Tool-calling response
  - `get_stream_response()` - Streaming response

- `LLMEngine`
  - Factory for loading providers
  - Format: `provider::model` (e.g., `openrouter::anthropic/claude-3.5-sonnet`)

### `src/llm/openrouter.py`

**OpenRouterProvider:**
- Implements LLMProvider interface
- Uses llm-clients-python OpenRouter client
- Supports chat completions, tool calling, streaming

### `src/llm/iflow.py`

**IFlowProvider:**
- Implements LLMProvider interface
- Uses llm-clients-python iFlow client
- Supports chat completions, tool calling, streaming

### `src/llm/utils.py`

**Utilities:**
- `run_concurrent_prompts()` - Async execution with semaphore limiting
- `run_parallel_prompts()` - Thread-based parallel execution
- Retry logic, timeout handling, progress bars, error logging

## MindMap Layer

### `src/mindmap/mindmap.py`

**MindMap Dataclass:**
- `label`: str - Node name
- `node`: int - Unique identifier
- `summary`: str - Brief explanation
- `children`: list[MindMap] - Child nodes
- `keywords`: list[str] - Keywords

**Methods:**
- `to_dataframe()` - Export to pandas DataFrame
- `to_json()` - Export to JSON string
- `save_json()` - Save to JSON file
- `visualize()` - Render with graphviz/plotly
- `print()` - Display as text tree

**Helper Functions:**
- `generate_theme_tree()` - Simple one-shot theme generation

### `src/mindmap/mindmap_generator.py`

**MindMapGenerator:**

**Generation Modes:**
- `generate_one_shot()`
  - Single LLM call
  - Returns MindMap and metadata

- `generate_refined()`
  - Two-step process
  - LLM proposes structure → LLM refines with additional context
  - Returns MindMap and metadata

**Methods:**
- `compose_base_message()` - Build base prompt
- `compose_tool_call_message()` - Build tool-calling prompt
- `send_tool_call()` - Execute tool call
- `compose_refinement_message()` - Build refinement prompt
- `_parse_llm_to_themetree()` - Parse LLM output to MindMap
- `_themetree_to_dataframe()` - Convert to DataFrame

### `src/mindmap/mindmap_utils.py`

**Prompts Dictionary:**
```python
prompts_dict = {
    "theme": {
        "qualifier": "Main Theme",
        "user_prompt_message": "Your given Theme is: {main_theme}",
        "default_instructions": "...",
        "enforce_structure_string": "..."
    }
}
```

**Utilities:**
- `format_mindmap_to_dataframe()` - Parse pipe-delimited tables
- `save_results_to_file()` - Save to JSON
- `load_results_from_file()` - Load from JSON

## Configuration

### String Format
```python
config = "openrouter::anthropic/claude-3.5-sonnet"
```

### Dictionary Format
```python
config = {
    "provider": "openrouter",
    "model": "anthropic/claude-3.5-sonnet",
    "connection_config": {
        "api_key": "your-api-key"
    },
    "temperature": 0,
    "response_format": {"type": "json_object"}
}
```

## Usage Example

### Basic Usage
```python
from src.llm import LLMEngine
from src.mindmap import generate_theme_tree

config = {
    "provider": "openrouter",
    "model": "anthropic/claude-3.5-sonnet",
    "connection_config": {"api_key": "..."}
}

mindmap = generate_theme_tree("Artificial Intelligence", "machine learning", config)
mindmap.print()
mindmap.visualize(engine="graphviz")
```

### Advanced Usage
```python
from src.mindmap import MindMapGenerator

generator = MindMapGenerator(
    llm_model_config_base={
        "provider": "openrouter",
        "model": "anthropic/claude-3.5-sonnet",
        "connection_config": {"api_key": "..."}
    }
)

mindmap, results = generator.generate_one_shot(
    main_theme="Supply Chain Disruption",
    focus="electronics industry"
)
```

## Key Simplifications

- **Removed risk prompts** - Only `prompts_dict["theme"]` remains
- **Removed Bigdata dependency** - No search integration
- **Simplified generation modes** - `generate_one_shot()` and `generate_refined()` only
- **Two LLM providers** - OpenRouter and IFlow

## Testing Strategy

### Unit Tests (`tests/src/`)
- `test_llm/` - Test individual LLM components
- `test_mindmap/` - Test individual MindMap components

### Integration Tests (`tests/examples/`)
- `test_mindmap_demo.py` - Basic flow integration
- `test_advanced_demo.py` - Advanced flow integration

## Test Hierarchy

```
tests/
├── src/          # Unit tests for source code
│   ├── llm/      # Test individual LLM components
│   └── mindmap/  # Test individual MindMap components
└── examples/     # Integration tests for examples
    ├── test_mindmap_demo.py    # Basic flow integration
    └── test_advanced_demo.py   # Advanced flow integration
```
