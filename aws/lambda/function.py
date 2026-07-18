# Import Alexa Skills Kit SDK
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# Import custom modules
from src.aloy import Aloy

# Instantiate once per warm Lambda container, not per invocation
# This avoids rebuilding the Bedrock client/re-reading the persona file every call
aloy = Aloy()


class LaunchRequestHandler(AbstractRequestHandler):
    """
    Handles "Alexa, open Aloy".
    """

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        summary = aloy.run()

        return (
            handler_input.response_builder
            .speak(summary)
            .set_should_end_session(True)
            .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Fallback so a Bedrock/GH failure doesn't just hang Alexa.
    """

    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        return (
            handler_input.response_builder
            .speak("Something went wrong fetching your TODOs. Try again shortly.")
            .set_should_end_session(True)
            .response
        )


# Instantiate the Alexa SkillBuilder
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()
