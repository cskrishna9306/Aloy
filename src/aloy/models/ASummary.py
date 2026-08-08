# Import third-party packages
from pydantic import BaseModel, Field


class ASummary(BaseModel):
    """
    Models the summarizer's structured spoken briefing of the outstanding TODOs.
    """
    response: str = Field(description="The final spoken summary to read back to the user")
