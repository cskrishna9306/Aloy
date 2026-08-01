# Import standard packages
import importlib.resources

# Import Langchain packages
from langchain_aws import ChatBedrockConverse
from langchain_core.language_models.chat_models import BaseChatModel

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
