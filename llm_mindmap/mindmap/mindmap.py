"""MindMap data structure and theme tree generation."""

import ast
import json
from dataclasses import dataclass, field
from logging import Logger, getLogger
from typing import Any

from json_repair import repair_json
from pandas import DataFrame

from llm_mindmap.llm import LLMConfig, LLMEngine
from llm_mindmap.mindmap.mindmap_utils import compose_themes_system_prompt

logger: Logger = getLogger(__name__)


@dataclass
class MindMap:
    """Hierarchical tree structure for mind map representation.

    Each node represents a semantically meaningful unit with a label,
    unique identifier, summary, and optional children.

    Args:
        label: Name of the current node
        node: Unique identifier for the node
        summary: Brief explanation of the node's relevance
        children: List of child nodes representing sub-units
        keywords: List of keywords summarizing the current node
    """

    label: str
    node: int
    summary: str = ""
    children: list["MindMap"] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return self.as_string()

    @staticmethod
    def from_dict(tree_dict: dict) -> "MindMap":
        """Create MindMap object from dictionary.

        Args:
            tree_dict: Dictionary representing the MindMap structure

        Returns:
            MindMap object generated from the dictionary
        """
        tree_dict = dict_keys_to_lowercase(tree_dict)

        tree = MindMap(**tree_dict)
        tree.children = [
            MindMap.from_dict(child) for child in tree_dict.get("children", [])
        ]
        return tree

    def as_string(self, prefix: str = "") -> str:
        """Convert tree to string representation.

        Args:
            prefix: Prefix to add to each branch

        Returns:
            String representation of the tree
        """
        s = prefix + self.label + "\n"

        if not self.children:
            return s

        for i, child in enumerate(self.children):
            is_last = i == (len(self.children) - 1)
            if is_last:
                branch = "└── "
                child_prefix = prefix + "    "
            else:
                branch = "├── "
                child_prefix = prefix + "│   "

            s += prefix + branch
            s += child.as_string(prefix=child_prefix)
        return s

    def get_label_summaries(self) -> dict[str, str]:
        """Extract label summaries from the tree.

        Returns:
            Dictionary with labels as keys and summaries as values
        """
        label_summary = {self.label: self.summary}
        for child in self.children:
            label_summary.update(child.get_label_summaries())
        return label_summary

    def get_summaries(self) -> list[str]:
        """Extract node summaries from the tree.

        Returns:
            List of all summary values in the tree
        """
        summaries = [self.summary]
        for child in self.children:
            summaries.extend(child.get_summaries())
        return summaries

    def get_terminal_label_summaries(self) -> dict[str, str]:
        """Extract items from terminal nodes of the tree.

        Returns:
            Dictionary with terminal node labels as keys and summaries as values
        """
        label_summary = {}
        if not self.children:
            label_summary[self.label] = self.summary
        for child in self.children:
            label_summary.update(child.get_terminal_label_summaries())
        return label_summary

    def get_terminal_labels(self) -> list[str]:
        """Extract terminal labels from the tree.

        Returns:
            List of terminal node labels
        """
        return list(self.get_terminal_label_summaries().keys())

    def get_terminal_summaries(self) -> list[str]:
        """Extract summaries from terminal nodes.

        Returns:
            List of terminal node summaries
        """
        return list(self.get_terminal_label_summaries().values())

    def print(self, prefix: str = "") -> None:
        """Print the tree.

        Args:
            prefix: Prefix to add to each branch
        """
        print(self.as_string(prefix=prefix))

    def visualize(self, engine: str = "graphviz") -> None:
        """Visualize the mind map.

        Args:
            engine: Rendering engine ('graphviz' or 'plotly')

        Raises:
            ValueError: If engine is not supported
        """
        if engine == "graphviz":
            self._visualize_graphviz()
        elif engine == "plotly":
            self._visualize_plotly()
        else:
            raise ValueError(
                f"Unsupported engine '{engine}'. "
                f"Supported engines are 'graphviz' and 'plotly'."
            )

    def _visualize_graphviz(self):
        """Visualize tree using Graphviz."""
        import graphviz

        mindmap = graphviz.Digraph()
        mindmap.attr(rankdir="LR", ordering="in", splines="curved")

        def add_nodes(node: MindMap):
            is_terminal = not node.children

            if is_terminal:
                node_text = f"<B>{node.label}</B>: {node.summary}"
            else:
                node_text = f"<B>{node.label}</B>"

            mindmap.node(
                str(node),
                f"<{node_text}>",
                shape="box",
                style="filled",
                fillcolor="lightgrey" if not is_terminal else "#e0e0e0",
                margin="0.2,0",
                align="left",
                fontsize="12",
                fontname="Arial",
            )

            if node.children:
                for child in node.children:
                    mindmap.edge(str(node), str(child))
                    add_nodes(child)

        add_nodes(self)
        mindmap.render("mindmap.gv", format="pdf", cleanup=True, quiet=True)

    def _visualize_plotly(self) -> None:
        """Visualize tree using Plotly treemap."""
        try:
            import plotly.express as px
        except ImportError:
            raise ImportError(
                "Missing optional dependency for plotly visualization. "
                "Please install plotly."
            )

        def extract_labels(node: MindMap, parent_label=""):
            labels.append(node.label)
            parents.append(parent_label)
            for child in node.children:
                extract_labels(child, node.label)

        labels = []
        parents = []
        extract_labels(self)

        df = DataFrame({"labels": labels, "parents": parents})
        fig = px.treemap(df, names="labels", parents="parents")
        fig.show()

    def get_label_to_parent_mapping(self) -> dict:
        """Return mapping from leaf node labels to parent node labels.

        Returns:
            Dictionary mapping leaf labels to parent labels
        """
        mapping = {}

        def traverse(node, parent_label=None):
            current_label = node.label
            children = node.children or []

            if parent_label and not children:
                mapping[current_label] = parent_label

            for child in children:
                traverse(child, current_label)

        traverse(self)
        return mapping

    def _to_dict(self) -> dict:
        """Convert MindMap to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the MindMap
        """
        return {
            "label": self.label,
            "node": self.node,
            "summary": self.summary,
            "children": (
                [child._to_dict() for child in self.children] if self.children else []
            ),
            "keywords": self.keywords,
        }

    def save_json(self, filepath: str, **kwargs) -> None:
        """Save MindMap as JSON file.

        Args:
            filepath: Path to output JSON file
            **kwargs: Additional arguments passed to json.dump
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._to_dict(), f, ensure_ascii=False, indent=2, **kwargs)

    def to_rows(self, parent_label=None):
        """Flatten tree to rows for DataFrame.

        Args:
            parent_label: Parent label for current node

        Returns:
            List of dictionaries with Parent, Label, Node, Summary
        """
        rows = []
        rows.append(
            {
                "Parent": parent_label,
                "Label": self.label,
                "Node": self.node,
                "Summary": self.summary,
            }
        )
        for child in self.children:
            rows.extend(child.to_rows(parent_label=self.label))
        return rows

    def to_dataframe(self, leaves_only=False):
        """Convert MindMap to pandas DataFrame.

        Args:
            leaves_only: If True, only include leaf nodes

        Returns:
            DataFrame with Parent, Label, Node, Summary columns
        """
        rows = self.to_rows(parent_label=None)
        filtered = [row for row in rows if row["Parent"] not in (None, self.label)]
        if leaves_only:
            filtered = [
                row
                for row in filtered
                if row["Label"] not in {r["Parent"] for r in filtered}
            ]
        return DataFrame(filtered)

    def to_json(self):
        """Convert MindMap to JSON string.

        Returns:
            JSON string representation of the MindMap
        """
        return json.dumps(self._to_dict(), indent=2)


def dict_keys_to_lowercase(d: dict[str, Any]) -> dict[str, Any]:
    """Convert all keys in dictionary to lowercase recursively.

    Args:
        d: Dictionary to convert

    Returns:
        New dictionary with all keys converted to lowercase
    """
    new_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            new_dict[k.lower()] = dict_keys_to_lowercase(v)
        else:
            new_dict[k.lower()] = v
    return new_dict


def stringify_label_summaries(label_summaries: dict[str, str]) -> list[str]:
    """Convert label summaries to list of strings.

    Args:
        label_summaries: Dictionary of label summaries

    Returns:
        List of strings in format "{label}: {summary}"
    """
    return [f"{label}: {summary}" for label, summary in label_summaries.items()]


def generate_theme_tree(
    main_theme: str,
    focus: str = "",
    llm_model_config: LLMConfig | dict | str = "openrouter::gpt-4o-mini",
) -> MindMap:
    """Generate MindMap from main theme and focus.

    Args:
        main_theme: Primary theme to analyze
        focus: Specific aspect to guide sub-theme generation
        llm_model_config: Configuration for LLM model

    Returns:
        Generated theme tree as MindMap object
    """
    if isinstance(llm_model_config, dict):
        llm_model_config = LLMConfig(**llm_model_config)
    elif isinstance(llm_model_config, str):
        provider_model = llm_model_config.split("::")
        if len(provider_model) == 2:
            llm_model_config = LLMConfig(
                provider=provider_model[0],
                model=provider_model[1],
            )
        else:
            llm_model_config = LLMConfig(
                provider="openrouter",
                model=llm_model_config,
            )
    elif llm_model_config is None:
        # Load default configuration from .local/llms.json
        from llm_mindmap.llm.base import load_llm_config

        llm_config = load_llm_config()
        default_provider = llm_config.get("default_provider", "iflow")
        provider_config = llm_config.get("providers", {}).get(default_provider, {})

        default_model = llm_config.get("default_model", "gpt-4o")

        llm_model_config = LLMConfig(
            provider=default_provider,
            model=default_model,
            connection_config=provider_config,
        )

    logger.debug(f"LLM Model Config: {llm_model_config}")

    model_str = llm_model_config.model
    chat_params = llm_model_config.get_llm_kwargs(
        remove_max_tokens=True, remove_timeout=True
    )

    llm = LLMEngine(
        model=model_str,
        provider=llm_model_config.provider,
        **llm_model_config.connection_config,
    )

    system_prompt = compose_themes_system_prompt(main_theme, analyst_focus=focus)

    chat_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": main_theme},
    ]

    tree_str = llm.get_response(chat_history, **chat_params)
    tree_str = repair_json(tree_str)
    tree_dict = ast.literal_eval(tree_str)

    return MindMap.from_dict(tree_dict)
