# Import standard packages
import base64
from pathlib import Path
import requests

# Import AWS SDK
import boto3

# Import custom modules
from src.aloy.config import config


class Aloy:
    """
    Python object housing the main design of Aloy.
    """

    def __init__(self):
        """
        Initialize Aloy.
        """

        # Initialize the AWS bedrock client
        self.bedrock_client = boto3.client(
                "bedrock-runtime",
                region_name=config.AWS_REGION
        )

        # Load the system prompt for Aloy
        self.persona: str = Path(__file__).with_name("PERSONA.md").read_text()

        return

    
    def fetch_todos(
            self,
            paths: list[str] | None = config.GH_TODO_REPO_PATHS
    ) -> dict[str, str]:
        """
        Routine responsible for fetching my TODOs from my private repo.

        Args:
            paths (list[str]): A list of paths to the TODO files in the repo

        Returns:
            dict[str, str]: key-value pairs of the different TODOs and the TODOs

        Raises:
            Exception: If any error is encountered while fetching the TODOs from GH
        """
        try:
            # This routine will be hardcoded for now to keep it simple
            # Future iterations MIGHT include universal traversal of a GH repo
            todos: dict[str, str] = {}

            # Iterate over all the provided paths
            for path in paths:
                try:
                    response = requests.get(
                        config.GH_API_URL + path,
                        headers={
                            "Authorization": f"Bearer {config.GH_PAT}",
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28",
                        },
                        timeout=5,
                    )
                    response.raise_for_status()

                    # Update our local TODOs dictionary with the new content
                    todos[path] = base64.b64decode(response.json()["content"]).decode("utf-8")
                except Exception as e:
                    raise Exception(f"Error: Ran into an error while fetching TODO at {path} - {e}")

            return todos

        except Exception as e:
            # Catch any misc exceptions and return as is
            raise Exception(f"Error: Ran into an error while fetching TODOs from GH - {e}")

        return {}

    
    def summarize(self, todos: dict[str, str]) -> str:
        """
        Routine to invoke the LLM to summarize the TODOs and motivate me.

        Args:
            todos: A dictionary of pending TODOs

        Returns:
            str: Summary of the TODOs
        """
        try:
            # Invoke the model via AWS Bedrock
            response = self.bedrock_client.converse(
                modelId=config.AWS_BEDROCK_MODEL_ID,
                system=[{"text": self.persona}],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "text":  "\n\n".join(f"### {path}\n{content}" for path, content in todos.items())
                            }
                        ]
                    }
                ],
                inferenceConfig={"maxTokens": 500, "temperature": 0.7},
            )

            # Finally, we return the model's response
            return response["output"]["message"]["content"][0]["text"]
        
        except Exception as e:
            # Catch any exception raised in this routine
            raise Exception(f"Error: Ran into an error while calling summarize() - {e}")

        return ""


    def run(self):
        """
        Runs the entire Aloy architecture.
        """
        try:
            todos = self.fetch_todos()

            summary = self.summarize(todos)

            return summary

        except Exception as e:
            # Catch any misc exceptions
            print(f"Error: Ran into an error while runnning Aloy - {e}")

        return

