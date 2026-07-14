# Import standard packages
import os
from dotenv import load_dotenv


class Config:
    """
    Simple config module to import the GH credentials and AWS settings.
    """
   
    # Load the environment variables into runtime
    load_dotenv()

    # Load any GH settings here
    GH_PAT: str = os.getenv("GH_PAT")
    GH_TODO_REPO_OWNER: str = os.getenv("GH_TODO_REPO_OWNER")
    GH_TODO_REPO_NAME: str = os.getenv("GH_TODO_REPO_NAME")
    
    # GH URL settings
    GH_API_URL: str = f"https://api.github.com/repos/{GH_TODO_REPO_OWNER}/{GH_TODO_REPO_NAME}/contents/"
    GH_TODO_REPO_PATHS: list[str] = [
            "Campaign.md",
            "Guild.md",
            "Expedition.md",
    ]

    # Load any AWS credentials here
    AWS_REGION: str = os.getenv("AWS_REGION")
    AWS_BEDROCK_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

config = Config()

