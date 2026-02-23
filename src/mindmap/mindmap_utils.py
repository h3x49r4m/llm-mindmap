"""MindMap utilities and prompt templates."""

import json
import os
from io import StringIO

import pandas as pd


prompts_dict = {
    "theme": {
        "qualifier": "Main Theme",
        "user_prompt_message": "Your given Theme is: {main_theme}",
        "default_instructions": (
            "Forget all previous prompts."
            "You are assisting a professional analyst tasked with creating a screener to measure the impact of the theme {main_theme} on companies."
            "Your objective is to generate a comprehensive tree structure of distinct sub-themes that will guide the analyst's research process."
            "Follow these steps strictly:"
            "1. **Understand the Core Theme {main_theme}":"
            "   - The theme {main_theme} is a central concept. All components are essential for a thorough understanding."
            "2. **Create a Taxonomy of Sub-themes for {main_theme}":"
            "   - Decompose the main theme {main_theme} into concise, focused, and self-contained sub-themes."
            "   - Each sub-theme should represent a singular, concise, informative, and clear aspect of the main theme."
            "   - Expand the sub-theme to be relevant for the {main_theme}: a single word is not informative enough."
            "   - Prioritize clarity and specificity in your sub-themes."
            "   - Avoid repetition and strive for diverse angles of exploration."
            "   - Provide a comprehensive list of potential sub-themes."
            "3. **Iterate Based on the Analyst's Focus {analyst_focus}":"
            "   - If no specific {analyst_focus} is provided, transition directly to formatting the JSON response."
            "4. **Format Your Response as a JSON Object**:"
            "   - Each node in the JSON object must include:"
            "     - `node`: an integer representing the unique identifier for the node."
            "     - `label`: a string for the name of the sub-theme."
            "     - `summary`: a string to explain briefly in maximum 15 words why the sub-theme is related to the theme {main_theme}."
            "       - For the node referring to the first node {main_theme}, just define briefly in maximum 15 words the theme {main_theme}."
            "     - `children`: an array of child nodes."
        ),
        "enforce_structure_string": (
            """IMPORTANT: Your response MUST be a valid JSON object. Each node in the JSON object must include:\n"
		            "- `node`: an integer representing the unique identifier for the node.\n"
		            "- `label`: a string for the name of the sub-theme.\n"
		            "- `summary`: a string to explain briefly in maximum 15 words why the sub-theme is related to the theme.\n"
		            "- For the node referring to the main theme, just define briefly in maximum 15 words the theme.\n"
		            "- `children`: an array of child nodes.\n"
	                "Format the JSON object as a nested dictionary. Be careful when specifying keys and items.\n"
	        "Avoid overlapping labels. Break down joint concepts into unique parents so that each parent represents ONLY ONE concept. AVOID creating branch names such as 'Compliance and Regulatory Risk'. Keep risks separate and create a single branch for each risk, such as 'Compliance Risk' and 'Regulatory Risk', each with their own children.\n"
            "Return ONLY the JSON object, with no extra text, explanation, or markdown.\n"
            "You MUST use ONLY these field names: label, node, summary, children. Do NOT use underscores, spaces, or any other characters in field names. If you use any other field names, your answer will be rejected.\n"
            "## Example Structure:\n"
            "**Theme: Global Warming**\n\n"
            "{\n"
            "  \"node\": 1,\n"
            "  \"label\": \"Global Warming\",\n"
            "  \"summary\": \"Global Warming is a serious risk\",\n"
            "  \"children\": [\n"
            "    {\"node\": 2, \"label\": \"Renewable Energy Adoption\", \"summary\": \"Renewable energy reduces greenhouse gas emissions and thereby global warming and climate change effects\", \"children\": [\n"
            "      {\"node\": 5, \"label\": \"Solar Energy\", \"summary\": \"Solar energy reduces greenhouse gas emissions\"},\n"
            "      {\"node\": 6, \"label\": \"Wind Energy\", \"summary\": \"Wind energy reduces greenhouse gas emissions\"},\n"
            "      {\"node\": 7, \"label\": \"Hydropower\", \"summary\": \"Hydropower reduces greenhouse gas emissions\"}\n"
            "    ]},\n"
            "    {\"node\": 3, \"label\": \"Carbon Emission Reduction\", \"summary\": \"Carbon emission reduction decreases greenhouse gases\", \"children\": [\n"
            "      {\"node\": 8, \"label\": \"Carbon Capture Technology\", \"summary\": \"Carbon capture technology reduces atmospheric CO2\"},\n"
            "      {\"node\": 9, \"label\": \"Emission Trading Systems\", \"summary\": \"Emission trading systems incentivizes reductions in greenhouse gases\"}\n"
            "    ]}\n"
            "  ]\n"
            "}\n"
            """
        ),
    },
}


def compose_themes_system_prompt(main_theme: str, analyst_focus: str = "") -> str:
    """Compose system prompt for theme generation.

    Args:
        main_theme: The main theme to analyze
        analyst_focus: Specific aspect to guide sub-theme generation

    Returns:
        Composed system prompt string
    """
    instructions = prompts_dict["theme"]["default_instructions"].format(
        main_theme=main_theme, analyst_focus=analyst_focus
    )
    enforce_structure = prompts_dict["theme"]["enforce_structure_string"]

    return f"{instructions} {analyst_focus}\n{enforce_structure}"


def format_mindmap_to_dataframe(mindmap_text: str) -> pd.DataFrame:
    """Parse mind map in pipe-delimited table format to DataFrame.

    Args:
        mindmap_text: Mind map content as pipe-delimited string

    Returns:
        Cleaned pandas DataFrame

    Raises:
        ValueError: If DataFrame doesn't contain required columns
    """
    try:
        df = pd.read_csv(
            StringIO(mindmap_text.strip()), sep="|", engine="python", skiprows=[1]
        )
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    except Exception:
        try:
            df = pd.read_csv(
                StringIO(mindmap_text.strip()),
                sep="|",
                engine="python",
                skiprows=[1],
                on_bad_lines="skip",
            )
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        except Exception as e2:
            raise ValueError(f"Failed to parse mindmap text to DataFrame: {e2}")

    required_columns = {"Main Branches", "Sub-Branches", "Description"}
    if not required_columns.issubset(set(df.columns)):
        raise ValueError(f"Missing required columns in mindmap table: {df.columns}")

    return df


def save_results_to_file(results: dict, output_dir: str, filename: str) -> None:
    """Save results to JSON file.

    Args:
        results: Results dictionary to save
        output_dir: Directory to save file in
        filename: Name of the output file
    """
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, filename)

    with open(output_file, "w") as f:
        json.dump(results, f, default=str, indent=2)


def load_results_from_file(output_dir: str, filename: str) -> dict:
    """Load results from JSON file.

    Args:
        output_dir: Directory containing the file
        filename: Name of the file to load

    Returns:
        Loaded results dictionary
    """
    input_file = os.path.join(output_dir, filename)
    with open(input_file, "r") as f:
        return json.load(f)