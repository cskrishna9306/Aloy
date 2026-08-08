# Import standard packages
import importlib.resources
import re

# Import Langchain packages
from langchain_aws import ChatBedrockConverse
from langchain_core.language_models.chat_models import BaseChatModel

# Import markdown parsers
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

# Import custom modules
from src.aloy.config import config


def get_llm(temperature: float) -> BaseChatModel:
    """
    Factory to build the Bedrock-backed chat model shared across all of Aloy's sub-agents.

    Args:
        temperature (float): The sampling temperature to use for the model

    Returns:
        BaseChatModel: The instantiated Bedrock chat model
    """
    return ChatBedrockConverse(
        model=config.AWS_BEDROCK_MODEL_ID,
        region_name=config.AWS_REGION,
        temperature=temperature,
    )


def gh_headers() -> dict[str, str]:
    """
    Build the shared auth headers used by every GitHub REST API call.

    Returns:
        dict[str, str]: The headers to pass along w/ every GitHub API request
    """
    return {
        "Authorization": f"Bearer {config.GH_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def extract_bullets(list_node: SyntaxTreeNode, indent: int = 0) -> str:
    """
    Recursively render the non-completed items of a bullet_list syntax tree node back
    out as markdown, dropping any GFM task items already checked off (`- [x] ...`).

    Args:
        list_node (SyntaxTreeNode): The bullet_list node to extract items from
        indent (int): The current nesting depth, used to indent sub-bullets

    Returns:
        str: The non-completed bullets, rendered back out as markdown
    """
    lines: list[str] = []

    for item in list_node.children:
        text: str = ""
        sublists: list[SyntaxTreeNode] = []

        # A list_item's direct children are its paragraph (the bullet's own text)
        # and, if present, a nested bullet_list of sub-items
        for child in item.children:
            if child.type == "paragraph" and child.children:
                text = child.children[0].content
            elif child.type == "bullet_list":
                sublists.append(child)

        # GFM task checkboxes show up as plain "[ ] "/"[x] " text at the start of
        # the bullet's inline content - there's no dedicated token for them
        checkbox = re.match(r"^\[(?P<check>[xX ])\]\s*(?P<text>.*)$", text)
        completed = checkbox is not None and checkbox.group("check").lower() == "x"

        if completed:
            continue

        display_text = checkbox.group("text") if checkbox else text
        lines.append(f"{'  ' * indent}- {display_text}")

        for sublist in sublists:
            nested = extract_bullets(sublist, indent + 1)
            if nested:
                lines.append(nested)

    return "\n".join(lines)


def trim_todos(todos: str) -> str:
    """
    Routine to trim the provided list of TODOs.
    This will be responsible for not pushing any completed TODOs to the LLM and avoid hallucinations.

    Args:
        todos (str): The TODOs string to trim

    Returns:
        str: The trimmed TODOs

    Raises:
        Exception: Raised when encountering an error while trimming
    """
    try:
        # The final trimmed todos
        trimmed_todos: str = ""

        # Build the syntax tree over the markdown
        tree = SyntaxTreeNode(MarkdownIt().parse(todos))

        # Headings and the content beneath them are siblings in the tree, not
        # parent/child, so walk the top-level nodes in document order and track
        # whether we're currently inside an archived section by heading level
        skip_level: int | None = None

        for node in tree.children:
            if node.type == "heading":
                level = int(node.tag[1:])

                # Stepping back up to (or past) the archived heading's level means
                # we've left that section
                if skip_level is not None and level <= skip_level:
                    skip_level = None

                # Skip archived sections
                if skip_level is None and node.children and "Archive" in node.children[0].content:
                    skip_level = level

            elif node.type == "bullet_list" and skip_level is None:
                # Extract all the non-completed TODOs
                bullets = extract_bullets(node)
                if bullets:
                    trimmed_todos += "\n" + bullets

        return trimmed_todos.strip()

    except Exception as e:
        raise Exception(f"Error: Ran into an error while trimming: {e}")


def load_system_prompt(prompt_file: str) -> str | None:
    """
    Load a system prompt markdown file from src/aloy/prompts/.

    Args:
        prompt_file (str): The name of the prompt file to load (e.g. "Router.md")

    Returns:
        str | None: The contents of the prompt file, or None if it could not be loaded
    """
    try:
        return importlib.resources.files("src.aloy.prompts").joinpath(prompt_file).read_text(encoding="utf-8")
    
    except Exception as e:
        # Catch any misc exceptions and log instead of crashing agent construction
        print(f"Error: Ran into an error while loading system prompt {prompt_file} - {e}")
    
    return
