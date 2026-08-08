# Import standard packages
from typing import Any

# Import Langchain packages
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

# Import custom modules
from src.aloy.config import config
from src.aloy.models import AState, ALogger, ARoute, ASummary
from src.aloy.tools import fetch_todos, update_todos
from src.aloy.utils import get_llm, load_system_prompt


class Aloy:
    """
    Python object housing the main design of Aloy.
    """

    def __init__(self):
        """
        Initialize Aloy.
        """

        # Aloy follows a router -> {summarizer, logger} design
        # The router decides whether the user wants a TODO briefing or wants to log a new TODO
        # The logger also determines which TODO category the new TODO belongs to

        # Load all the relevant system prompts for the sub-agents
        self.system_prompt: str = load_system_prompt("PERSONA.md") or ""
        self.router_instructions: str = load_system_prompt("Router.md") or ""
        self.summarizer_instructions: str = load_system_prompt("Summarizer.md") or ""
        self.logger_instructions: str = load_system_prompt("Logger.md") or ""

        # Initialize the LLM (reused for all sub-agents to keep it simple)
        self.llm = get_llm(temperature=0.2)

        # Instantiate the router, summarizer, and logger w/ their respective output classes
        self.router_llm = self.llm.with_structured_output(ARoute)
        self.summarizer_llm = self.llm.with_structured_output(ASummary)
        self.logger_llm = self.llm.with_structured_output(ALogger)

        # Create the state graph
        self._workflow = self.create_workflow()

        return

    def router(self, state: AState) -> dict[str, Any]:
        """
        Router node responsible for determining if we need to invoke the summarizer or the logger sub-agents.

        Args:
            state (AState): The input state

        Returns:
            dict[str, Any]: The dictionary to update in the graph's global state
        """
        # Call the router to classify the user's intent
        result: ARoute = self.router_llm.invoke(
            [
                SystemMessage(content=self.system_prompt),
                SystemMessage(content=self.router_instructions),
                HumanMessage(content=state.input),
            ]
        )

        return {"route": result.route}

    def summarizer(self, state: AState) -> dict[str, Any]:
        """
        Summarizer node responsible for fetching my TODOs and summarizing them.

        Args:
            state (AState): The input state

        Returns:
            dict[str, Any]: The dictionary to update in the graph's global state
        """
        # Fetch my current TODOs from GH
        todos = fetch_todos(config.GH_TODO_REPO_PATHS)
        todos_blob = "\n\n".join(f"### {path}\n{content}" for path, content in todos.items())

        # Call the summarizer to draft the spoken briefing
        result: ASummary = self.summarizer_llm.invoke(
            [
                SystemMessage(content=self.system_prompt),
                SystemMessage(content=self.summarizer_instructions),
                HumanMessage(content=todos_blob),
            ]
        )

        return {"response": result.response}

    def logger(self, state: AState) -> dict[str, Any]:
        """
        Logger node responsible for rephrasing and updating the TODOs in the GH repo.

        Args:
            state (AState): The input state

        Returns:
            dict[str, Any]: The dictionary to update in the graph's global state
        """
        # Call the logger to rephrase the TODO and pick its target category
        extraction: ALogger = self.logger_llm.invoke(
            [
                SystemMessage(content=self.system_prompt),
                SystemMessage(content=self.logger_instructions),
                HumanMessage(content=state.input),
            ]
        )

        # Push the rephrased TODO to the bottom of the chosen category file in GH
        update_todos(todo=extraction.todo, todo_category=extraction.category)

        return {"response": f"Got it. I've added \"{extraction.todo}\" to your {extraction.category} list."}

    def create_workflow(self) -> CompiledStateGraph:
        """
        Routine responsible for creating the LangGraph state graph w/ the router, summarizer, and logger sub-agents.

        Architecture:
        - Aloy follows a router -> {summarizer, logger} design
        - The router decides whether the user wants a TODO briefing or wants to log a new TODO
        - The summarizer fetches and reads back a spoken summary of the outstanding TODOs
        - The logger rephrases the new TODO, picks its category, and pushes it to GH
        """
        # Initialize the graph (no nodes yet)
        graph = StateGraph(AState)

        # Add the router, summarizer, and logger nodes
        graph.add_node("router", self.router)
        graph.add_node("summarizer", self.summarizer)
        graph.add_node("logger", self.logger)

        # Define the flow
        # First, the entry point
        graph.add_edge(START, "router")

        # Next, the conditional edges based on the router's decision
        graph.add_conditional_edges(
            "router",
            lambda state: state.route,
            {
                "summarizer": "summarizer",
                "logger": "logger",
            },
        )

        # Both the summarizer and logger are terminal for now
        graph.add_edge("summarizer", END)
        graph.add_edge("logger", END)

        # Finally, compile the graph itself
        workflow = graph.compile()

        return workflow

    def run(self, input: str = "Give me a summary of my current TODOs.") -> str:
        """
        Runs the entire Aloy architecture.

        Args:
            input (str): The provided input that drives the sub-agent flow

        Returns:
            str: The final response string generated by Aloy
        """
        try:
            # Execute the workflow
            result = self._workflow.invoke({"input": input})

            # Validate the presence of a final response
            response = result.get("response")
            if not response:
                raise ValueError("Aloy failed to generate a response!")

            return response

        except Exception as e:
            # Catch any misc exceptions
            print(f"Error: Ran into an error while running Aloy - {e}")

        return ""
