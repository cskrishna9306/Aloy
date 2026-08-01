# Import standard packages
from typing import Literal

# Import third-party packages
from pydantic import BaseModel, Field


class AState(BaseModel):
    """
    Models the shared state in the Aloy graph workflow.
    """
    input: str = Field(description="The input from the user")

    # Field to be populated by the router
    route: Literal["summarizer", "logger"] | None = Field(description="Which sub-agent to invoke next", default=None)

    # Field to be populated by the summarizer or logger
    response: str | None = Field(description="The final structured response to speak back to the user", default=None)
