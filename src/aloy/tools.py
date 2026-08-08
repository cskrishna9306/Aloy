# Import standard packages
import base64
from uuid import uuid4
import requests

# Import custom modules
from src.aloy.config import config
from src.aloy.utils import gh_headers, trim_todos


def fetch_todos(paths: list[str] | None = config.GH_TODO_REPO_PATHS) -> dict[str, str]:
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
                    f"{config.GH_REPO_API_URL}/contents/{path}",
                    headers=gh_headers(),
                    timeout=5,
                )
                response.raise_for_status()

                # Update our local TODOs dictionary with the new content
                todos[path] = base64.b64decode(response.json()["content"]).decode("utf-8")

                # TODO: Here we make sure to exclude any completed TODOs marked either by [x]
                # or enclosed ~~
                todos[path] = trim_todos(todos[path])

            except Exception as e:
                raise Exception(f"Error: Ran into an error while fetching TODO at {path} - {e}")

        return todos

    except Exception as e:
        # Catch any misc exceptions and return as is
        raise Exception(f"Error: Ran into an error while fetching TODOs from GH - {e}")


def update_todos(todo: str, todo_category: str) -> bool:
    """
    Routine responsible for augmenting the category file w/ the provided TODO.
    This routine is responsible for creating a new branch, committing the TODO to the new branch, and opening a PR.

    Args:
        todo (str): The (already rephrased) TODO to add
        todo_category (str): The TODO category file to update

    Returns:
        bool: True if the update was successful, False otherwise

    Raises:
        Exception: If any error is encountered while updating the TODOs
    """
    try:
        # Fetch the current contents + sha of the target category file
        get_response = requests.get(
            f"{config.GH_REPO_API_URL}/contents/{todo_category}",
            headers=gh_headers(),
            timeout=5,
        )
        get_response.raise_for_status()
        payload = get_response.json()
        file_sha = payload["sha"]
        current_content = base64.b64decode(payload["content"]).decode("utf-8")

        # Append the new TODO as a checkbox item at the end of the list
        updated_content = current_content.rstrip("\n") + f"\n- [ ] {todo}\n"

        # Resolve the latest commit sha on the default branch
        ref_response = requests.get(
            f"{config.GH_REPO_API_URL}/git/ref/heads/{config.GH_DEFAULT_BRANCH}",
            headers=gh_headers(),
            timeout=5,
        )
        ref_response.raise_for_status()
        base_sha = ref_response.json()["object"]["sha"]

        # Create a new branch off of the default branch to hold this change
        branch_name = f"aloy/add-todo-{uuid4().hex[:8]}"
        branch_response = requests.post(
            f"{config.GH_REPO_API_URL}/git/refs",
            headers=gh_headers(),
            json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
            timeout=5,
        )
        branch_response.raise_for_status()

        # Commit the updated file content to the new branch
        commit_response = requests.put(
            f"{config.GH_REPO_API_URL}/contents/{todo_category}",
            headers=gh_headers(),
            json={
                "message": f"Add TODO: {todo}",
                "content": base64.b64encode(updated_content.encode("utf-8")).decode("utf-8"),
                "sha": file_sha,
                "branch": branch_name,
            },
            timeout=5,
        )
        commit_response.raise_for_status()

        # Finally, open a PR from the new branch into the default branch
        pr_response = requests.post(
            f"{config.GH_REPO_API_URL}/pulls",
            headers=gh_headers(),
            json={
                "title": f"Add TODO: {todo}",
                "head": branch_name,
                "base": config.GH_DEFAULT_BRANCH,
                "body": f"Adding new TODO to `{todo_category}`:\n\n- [ ] {todo}",
            },
            timeout=5,
        )
        pr_response.raise_for_status()

        return True

    except Exception as e:
        # Catch any misc exceptions
        raise Exception(f"Error: Ran into an error while updating the TODOs - {e}")
