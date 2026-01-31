from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

from kognitos.bdk.api.http_response import HTTPResponse

T = TypeVar("T")


@dataclass
class TriggerResponse(Generic[T]):
    """
    Base class for trigger resolver responses.

    All trigger resolver responses inherit from this class and provide
    a unified interface for handling trigger events.

    Attributes:
        trigger_instance_reference: Optional reference to the trigger instance.
            None for non-shared endpoints, required string for shared endpoints.
        http_response: The HTTP response to return to the caller
        event: The trigger event data
    """

    trigger_instance_reference: Optional[str]
    http_response: HTTPResponse
    event: Optional[T]


@dataclass
class NonSharedTriggerResponse(TriggerResponse[T]):
    """
    Response container for non-shared endpoint trigger resolvers.

    Used when is_shared_endpoint=False. Automatically sets trigger_instance_reference
    to None since each trigger instance has its own unique endpoint.

    Attributes:
        http_response: The HTTP response to return to the caller
        event: The trigger event data

    Example:
        @trigger_event
        @dataclass
        class GitHubEvent:
            event_type: str
            repository: str
            action: str

        @trigger(name="GitHub Webhook", resolver="handle_webhook", is_shared_endpoint=False)
        def setup_webhook(self, endpoint: str) -> None:
            ...

        def handle_webhook(self, request: HTTPRequest) -> NonSharedTriggerResponse[GitHubEvent]:
            response = HTTPResponse(status=200, headers={}, body=b'{"status": "ok"}')
            event = GitHubEvent(...)
            return NonSharedTriggerResponse(http_response=response, event=event)
    """

    trigger_instance_reference: Optional[str] = field(default=None, init=False)


@dataclass
class SharedEndpointTriggerResponse(TriggerResponse[T]):
    """
    Response container for shared endpoint trigger resolvers.

    Used when is_shared_endpoint=True. Requires trigger_instance_reference to identify
    which trigger instance this event belongs to.

    Attributes:
        trigger_instance_reference: Required reference to identify the trigger instance.
            Must match the value returned from the trigger setup function.
        http_response: The HTTP response to return to the caller
        event: The trigger event data

    Example:
        @trigger_event
        @dataclass
        class SlackMessage:
            channel: str
            message: str

        @trigger(name="Slack Message", resolver="handle_message", is_shared_endpoint=True)
        def setup_slack(self, endpoint: str, channel: str) -> str:
            return channel  # This is the trigger_instance_reference

        def handle_message(self, request: HTTPRequest) -> SharedEndpointTriggerResponse[SlackMessage]:
            channel = request.json().get("channel")
            response = HTTPResponse(status=200, headers={}, body=b'{"status": "ok"}')
            event = SlackMessage(channel=channel, message="...")
            return SharedEndpointTriggerResponse(
                trigger_instance_reference=channel,
                http_response=response,
                event=event
            )
    """

    # trigger_instance_reference is inherited and required as first parameter
