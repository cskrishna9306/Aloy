# Import standard packages
from typing import Literal

# Import third-party packages
from pydantic import BaseModel, Field


class ARoute(BaseModel):
    """
    Models the router's structured decision on which sub-agent to invoke next.
    """
    route: Literal["summarizer", "logger"] = Field(description="Which sub-agent to invoke next")
