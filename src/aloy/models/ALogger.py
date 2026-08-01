# Import standard packages
from typing import Literal

# Import third-party packages
from pydantic import BaseModel, Field


class ALogger(BaseModel):
    """
    Models the logger node's structured extraction of a rephrased TODO and its target category.
    """
    todo: str = Field(description="The rephrased, concise TODO list item text")
    category: Literal["Campaign.md", "Guild.md", "Expedition.md"] = Field(description="The TODO category file this belongs in")
