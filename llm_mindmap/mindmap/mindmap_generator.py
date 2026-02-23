"""MindMap generator with advanced generation modes."""

import ast
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import Logger, getLogger
from typing import Optional

from tqdm import tqdm

from llm_mindmap.llm import LLMConfig, LLMEngine
from llm_mindmap.mindmap.mindmap import MindMap
from llm_mindmap.mindmap.mindmap_utils import prompts_dict, save_results_to_file

logger: Logger = getLogger(__name__)


class MindMapGenerator:
    """Core orchestrator for generating, refining, and dynamically evolving mind maps using LLMs.

    Features:
    - One-shot mind map generation (optionally grounded in search results)
    - Refined mind map generation (LLM proposes searches to enhance an initial mind map)
    - Dynamic mind map evolution over time intervals (each step refines previous map with new search context)
    """

    def __init__(
        self,
        llm_model_config_base: LLMConfig | dict | str = "openrouter::gpt-4o-mini",
        llm_model_config_reasoning: Optional[LLMConfig | dict | str] = None,
    ):
        """Initialize MindMapGenerator.

        Args:
            llm_model_config_base: Base LLM configuration for generation
            llm_model_config_reasoning: Reasoning LLM configuration for refinement
        """
        llm_model_config_reasoning = (
            llm_model_config_reasoning
            if llm_model_config_reasoning
            else llm_model_config_base
        )

        self.llm_model_config_base = self._parse_config(llm_model_config_base)
        self.llm_model_config_reasoning = self._parse_config(
            llm_model_config_reasoning
        )

        self.llm_base = LLMEngine(
            model=self.llm_model_config_base.model,
            provider=self.llm_model_config_base.provider,
            **self.llm_model_config_base.connection_config,
        )

        self.llm_reasoning = LLMEngine(
            model=self.llm_model_config_reasoning.model,
            provider=self.llm_model_config_reasoning.provider,
            **self.llm_model_config_reasoning.connection_config,
        )

    def _parse_config(self, config: LLMConfig | dict | str) -> LLMConfig:
        """Parse configuration to LLMConfig.

        Args:
            config: Configuration in LLMConfig, dict, or string format

        Returns:
            Parsed LLMConfig object
        """
        if isinstance(config, LLMConfig):
            return config
        elif isinstance(config, dict):
            return LLMConfig(**config)
        elif isinstance(config, str):
            provider_model = config.split("::")
            if len(provider_model) == 2:
                return LLMConfig(
                    provider=provider_model[0],
                    model=provider_model[1],
                )
            else:
                return LLMConfig(
                    provider="openrouter",
                    model=config,
                )
        else:
            raise ValueError(f"Invalid config type: {type(config)}")

    def _parse_llm_to_themetree(self, mindmap_text: str) -> MindMap:
        """Parse LLM output to MindMap.

        Args:
            mindmap_text: LLM response text containing JSON

        Returns:
            Parsed MindMap object

        Raises:
            ValueError: If parsing or validation fails
        """
        text = mindmap_text.strip()

        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"```$", "", text)
        text = re.sub(r"^[a-zA-Z]+\s*\n*{", "{", text)
        text = re.sub(r"^[^({\[]*({|\[)", r"\1", text, flags=re.DOTALL)

        try:
            tree_dict = json.loads(text)
        except Exception:
            try:
                tree_dict = ast.literal_eval(text)
            except Exception as e:
                raise ValueError(
                    f"Failed to parse LLM output as JSON or Python dict.\n"
                    f"Raw output:\n{mindmap_text}\n"
                    f"CLEANED OUTPUT:\n{text}\n"
                    f"Error: {e}"
                )

        allowed_keys = {"label", "node", "summary", "children"}

        def validate_node(node, path="root"):
            if not isinstance(node, dict):
                raise ValueError(f"Node at {path} is not a dict: {node}")

            illegal_keys = set(node.keys()) - allowed_keys
            if illegal_keys:
                raise ValueError(
                    f"Illegal key(s) {illegal_keys} at {path}. Node: {node}"
                )

            for key in allowed_keys:
                if key not in node or node[key] is None:
                    raise ValueError(
                        f"Missing or null required field '{key}' at {path}. Node: {node}"
                    )

            if not isinstance(node["children"], list):
                raise ValueError(
                    f"'children' field at {path} is not a list. Node: {node}"
                )

            for idx, child in enumerate(node["children"]):
                validate_node(child, path=f"{path} -> children[{idx}]")

        def dict_keys_to_lowercase(d):
            if isinstance(d, dict):
                return {k.lower(): dict_keys_to_lowercase(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [dict_keys_to_lowercase(i) for i in d]
            else:
                return d

        tree_dict = dict_keys_to_lowercase(tree_dict)

        try:
            validate_node(tree_dict)
        except Exception as e:
            raise ValueError(
                f"Mind map structure validation failed: {e}\n"
                f"Parsed dict:\n{json.dumps(tree_dict, indent=2)}"
            )

        try:
            theme_tree = MindMap.from_dict(tree_dict)
        except Exception as e:
            raise ValueError(
                f"Failed to build MindMap from dict: {e}\n"
                f"Parsed dict:\n{json.dumps(tree_dict, indent=2)}"
            )

        return theme_tree

    def compose_base_message(
        self, main_theme: str, focus: str, map_type: str, instructions: Optional[str]
    ) -> list:
        """Compose base message for LLM.

        Args:
            main_theme: Main theme to analyze
            focus: Specific aspect to guide generation
            map_type: Type of map ('theme' or 'risk')
            instructions: Optional custom instructions

        Returns:
            List of message dictionaries
        """
        if instructions is None:
            instructions = prompts_dict[map_type]["default_instructions"].format(
                main_theme=main_theme, analyst_focus=focus
            )

        enforce_structure = prompts_dict[map_type]["enforce_structure_string"]

        messages = [
            {
                "role": "system",
                "content": f"{instructions} {focus}\n{enforce_structure}",
            },
            {
                "role": "user",
                "content": prompts_dict[map_type]["user_prompt_message"].format(
                    main_theme=main_theme
                ),
            },
        ]

        return messages

    def generate_one_shot(
        self,
        main_theme: str,
        focus: str = "",
        allow_grounding: bool = False,
        instructions: Optional[str] = None,
        map_type: str = "theme",
    ) -> tuple[MindMap, dict]:
        """Generate mind map in one LLM call.

        Args:
            main_theme: Main theme to analyze
            focus: Specific aspect to guide generation
            allow_grounding: Whether to allow LLM to request grounding (not implemented in current version)
            instructions: Optional custom instructions
            map_type: Type of map ('theme' or 'risk')

        Returns:
            Tuple of (MindMap object, results dictionary)
        """
        messages = self.compose_base_message(
            main_theme=main_theme,
            focus=focus,
            map_type=map_type,
            instructions=instructions,
        )

        llm_kwargs = self.llm_model_config_base.get_llm_kwargs(
            remove_max_tokens=True, remove_timeout=True
        )

        mindmap_text = self.llm_base.get_response(messages, **llm_kwargs)

        theme_tree = self._parse_llm_to_themetree(mindmap_text)
        df = theme_tree.to_dataframe()

        return theme_tree, {
            "mindmap_text": mindmap_text,
            "mindmap_tree": theme_tree,
            "mindmap_json": theme_tree.to_json(),
            "mindmap_df": df,
            "grounded": False,
        }

    def generate_refined(
        self,
        main_theme: str,
        focus: str,
        initial_mindmap: str,
        output_dir: str = "./refined_mindmaps",
        filename: str = "refined_mindmap.json",
        map_type: str = "theme",
        instructions: Optional[str] = None,
    ) -> tuple[MindMap | None, dict]:
        """Refine an initial mind map with additional context.

        Args:
            main_theme: Main theme to analyze
            focus: Specific aspect to guide generation
            initial_mindmap: Initial mind map JSON string
            output_dir: Directory to save results
            filename: Name of output file
            map_type: Type of map ('theme' or 'risk')
            instructions: Optional custom instructions

        Returns:
            Tuple of (MindMap object or None, results dictionary)
        """
        if instructions is None:
            instructions = prompts_dict[map_type]["default_instructions"].format(
                main_theme=main_theme, analyst_focus=focus
            )

        refine_prompt = (
            f"{instructions} {prompts_dict[map_type]['qualifier']}: {main_theme} {focus}.\n"
            f"Based on these instructions, enhance the given mindmap with the information below. "
            f"Only return the mindmap without extra text.\n"
            f"IMPORTANT: Only create additional branches if the new information suggests that new branches would be relevant.\n"
            f"{prompts_dict[map_type]['enforce_structure_string']}."
        )

        refinement_messages = [
            {"role": "system", "content": refine_prompt},
            {"role": "user", "content": initial_mindmap},
        ]

        llm_kwargs = self.llm_model_config_reasoning.get_llm_kwargs(
            remove_max_tokens=True, remove_timeout=True
        )

        mindmap_text = self.llm_reasoning.get_response(refinement_messages, **llm_kwargs)

        try:
            theme_tree = self._parse_llm_to_themetree(mindmap_text)
            df = theme_tree.to_dataframe()
            result_dict = {
                "mindmap_text": mindmap_text,
                "mindmap_df": df,
                "mindmap_json": theme_tree.to_json(),
            }
            save_results_to_file(result_dict, output_dir, filename)
            return theme_tree, result_dict
        except Exception as e:
            logger.error(f"Failed to parse refined mindmap: {e}")
            result_dict = {
                "mindmap_text": mindmap_text,
                "mindmap_df": None,
                "mindmap_json": "",
                "error": str(e),
            }
            save_results_to_file(result_dict, output_dir, filename)
            return None, result_dict

    def generate_or_load_refined(
        self,
        main_theme: str,
        focus: str,
        map_type: str,
        initial_mindmap: str,
        instructions: Optional[str] = None,
        output_dir: str = "./refined_mindmaps",
        filename: str = "refined_mindmap",
        i: int = 0,
    ) -> dict:
        """Generate or load a refined mindmap.

        Args:
            main_theme: Main theme to analyze
            focus: Specific aspect to guide generation
            map_type: Type of map ('theme' or 'risk')
            initial_mindmap: Initial mind map JSON string
            instructions: Optional custom instructions
            output_dir: Directory to save/load results
            filename: Name of output file (without extension)
            i: Index for multiple refinements

        Returns:
            Results dictionary
        """
        filepath = os.path.join(output_dir, f"{filename}_{i}.json")

        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                result = json.load(f)
            logger.info(f"Loaded existing result for {filename}_{i}.json")
        else:
            try:
                _, result = self.generate_refined(
                    instructions=instructions,
                    focus=focus,
                    main_theme=main_theme,
                    map_type=map_type,
                    initial_mindmap=initial_mindmap,
                    output_dir=output_dir,
                    filename=f"{filename}_{i}.json",
                )
            except Exception as e:
                logger.error(f"Error generating refined mindmap {i}: {e}")
                result = {
                    "mindmap_text": "",
                    "mindmap_df": None,
                    "mindmap_json": "",
                    "error": str(e),
                }

        return result

    def bootstrap_refined(
        self,
        main_theme: str,
        focus: str,
        map_type: str,
        initial_mindmap: str,
        instructions: Optional[str] = None,
        output_dir: str = "./refined_mindmaps",
        filename: str = "refined_mindmap",
        n_elements: int = 50,
        max_workers: int = 10,
    ) -> list[dict]:
        """Generate multiple refined mindmaps in parallel using ThreadPoolExecutor.

        Generates n_elements mindmaps by calling generate_or_load_refined for each index.
        Uses a thread pool to parallelize the generation process for better efficiency.
        Each mindmap is saved with an index suffix to the output_dir.

        Args:
            main_theme: Main theme to analyze
            focus: Specific aspect to guide generation
            map_type: Type of map ('theme' or 'risk')
            initial_mindmap: Initial mind map JSON string
            instructions: Optional custom instructions
            output_dir: Directory to save results
            filename: Name of output file (without extension)
            n_elements: Number of mindmaps to generate
            max_workers: Maximum number of worker threads

        Returns:
            List of all generated mindmap results
        """
        os.makedirs(output_dir, exist_ok=True)

        refined_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {}

            for i in range(n_elements):
                future = executor.submit(
                    self.generate_or_load_refined,
                    instructions=instructions,
                    focus=focus,
                    main_theme=main_theme,
                    map_type=map_type,
                    initial_mindmap=initial_mindmap,
                    output_dir=output_dir,
                    filename=filename,
                    i=i,
                )
                future_to_index[future] = i

            for future in tqdm(
                as_completed(future_to_index),
                total=n_elements,
                desc="Bootstrapping Refined Mindmaps...",
            ):
                i = future_to_index[future]
                try:
                    refined_results.append(future.result())
                except Exception as e:
                    logger.error(f"Error in generating mindmap {i}: {e}")
                    refined_results.append({
                        "error": str(e),
                        "mindmap_text": "",
                        "mindmap_df": None,
                        "mindmap_json": "",
                    })

        return refined_results

    def generate_dynamic(
        self,
        main_theme: str,
        focus: str,
        initial_mindmap: Optional[str] = None,
        month_intervals: Optional[list[tuple[str, str]]] = None,
        month_names: Optional[list[str]] = None,
        instructions: Optional[str] = None,
        output_dir: str = "./dynamic_mindmaps",
        map_type: str = "theme",
    ) -> tuple[dict[str, MindMap], dict]:
        """Dynamic/iterative mind map generation over time intervals.

        Returns a list of dicts, one per interval.
        Each step: generate/refine mind map for the given interval.

        Args:
            main_theme: Main theme to analyze
            focus: Specific aspect to guide generation
            initial_mindmap: Optional initial mind map to start with
            month_intervals: List of (start_date, end_date) tuples for each interval
            month_names: List of names for each interval
            instructions: Optional custom instructions
            output_dir: Directory to save results
            map_type: Type of map ('theme' or 'risk')

        Returns:
            Tuple of (mindmap objects dict, results dict)
        """
        results = {}
        mind_map_objs = {}

        # If no initial mindmap provided, generate one
        if initial_mindmap is None:
            one_shot_map, one_shot_dict = self.generate_one_shot(
                main_theme=main_theme,
                focus=focus,
                instructions=instructions,
                map_type=map_type,
            )
            prev_mindmap = one_shot_dict["mindmap_json"]
            mind_map_objs["base_mindmap"] = one_shot_map
            results["base_mindmap"] = one_shot_dict
        else:
            prev_mindmap = initial_mindmap

        # For each interval, refine using previous mind map
        if month_intervals and month_names:
            for i, (date_range, month_name) in enumerate(
                zip(month_intervals, month_names), start=0
            ):
                refined_map, refined = self.generate_refined(
                    main_theme=main_theme,
                    focus=focus,
                    initial_mindmap=prev_mindmap,
                    map_type=map_type,
                    output_dir=output_dir,
                    filename=f"{month_name}.json",
                    instructions=instructions,
                )

                results[month_name] = refined
                mind_map_objs[month_name] = refined_map
                prev_mindmap = refined["mindmap_json"]

        return mind_map_objs, results