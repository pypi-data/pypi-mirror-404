import inspect
from typing import Callable, TypeVar, Union, get_args, get_origin

from kognitos.bdk.api.filter import FilterExpression
from kognitos.bdk.api.trigger_response import (NonSharedTriggerResponse,
                                               SharedEndpointTriggerResponse)
from kognitos.bdk.docstring.parser import DocstringParser
from kognitos.bdk.reflection.factory.trigger import BookTriggerFactory

from .trigger_setup_function import TriggerSetupFunction

T = TypeVar("T")


class trigger:

    @staticmethod
    def shared(name: str, is_manual: bool = False) -> Callable[[Callable[..., str]], TriggerSetupFunction]:
        """
        Decorator for shared endpoint triggers.

        Shared endpoint triggers have all trigger instances share a single endpoint.
        The setup function must return a str (trigger_instance_reference) to identify which
        instance should receive each event.

        Args:
            name: The display name of the trigger
            is_manual: Whether the trigger setup is manual (default: False)

        Returns:
            A decorator that validates and wraps the setup function

        Example:
            @trigger.shared(name="Slack Message")
            def setup_slack(self, endpoint: str, channel: str) -> str:
                '''Setup trigger

                Arguments:
                    channel: The channel to monitor
                '''
                return channel

            @setup_slack.resolver
            def handle_slack(self, request: HTTPRequest) -> SharedEndpointTriggerResponse[Event]:
                return SharedEndpointTriggerResponse(...)
        """
        return trigger._create_trigger_decorator(
            name=name,
            is_manual=is_manual,
            is_shared_endpoint=True,
            expected_setup_return_type=str,
            expected_resolver_response_type=SharedEndpointTriggerResponse,
        )

    @staticmethod
    def non_shared(name: str, is_manual: bool = False) -> Callable[[Callable[..., None]], TriggerSetupFunction]:
        """
        Decorator for non-shared endpoint triggers.

        Non-shared endpoint triggers give each trigger instance its own unique endpoint.
        The setup function must return None.

        Args:
            name: The display name of the trigger
            is_manual: Whether the trigger setup is manual (default: False)

        Returns:
            A decorator that validates and wraps the setup function

        Example:
            @trigger.non_shared(name="GitHub Webhook")
            def setup_github(self, endpoint: str, repo: str) -> None:
                '''Setup trigger

                Arguments:
                    repo: The repository to monitor
                '''
                pass

            @setup_github.resolver
            def handle_github(self, request: HTTPRequest) -> NonSharedTriggerResponse[Event]:
                return NonSharedTriggerResponse(...)
        """
        return trigger._create_trigger_decorator(
            name=name,
            is_manual=is_manual,
            is_shared_endpoint=False,
            expected_setup_return_type=type(None),
            expected_resolver_response_type=NonSharedTriggerResponse,
        )

    @staticmethod
    def _create_trigger_decorator(
        name: str,
        is_manual: bool,
        is_shared_endpoint: bool,
        expected_setup_return_type: type,
        expected_resolver_response_type: type,
    ):
        """Internal helper to create trigger decorators with validation."""

        def decorator(setup_fn):
            if not inspect.isfunction(setup_fn):
                raise TypeError("The trigger decorator can only be applied to functions.")

            # Validate setup function signature
            sig = inspect.signature(setup_fn, eval_str=True)
            params = sig.parameters

            # Validate return type
            return_type = sig.return_annotation
            if return_type == inspect.Signature.empty:
                raise ValueError(
                    f"Function '{setup_fn.__name__}' decorated with @trigger.{'shared' if is_shared_endpoint else 'non_shared'} "
                    f"must have a return type annotation. "
                    f"Expected: -> {expected_setup_return_type.__name__ if expected_setup_return_type is not type(None) else 'None'}"
                )

            # Special handling for None type (annotation is None, not type(None))
            if expected_setup_return_type is type(None):
                if return_type is not None:
                    raise ValueError(f"Function '{setup_fn.__name__}' decorated with @trigger.non_shared " f"must return 'None'. Got '{return_type}' instead.")
            else:
                if return_type is not expected_setup_return_type:
                    raise ValueError(
                        f"Function '{setup_fn.__name__}' decorated with @trigger.shared " f"must return '{expected_setup_return_type.__name__}'. " f"Got '{return_type}' instead."
                    )

            # Check for required 'endpoint' parameter
            if "endpoint" not in params:
                raise ValueError(f"Function '{setup_fn.__name__}' decorated with @trigger must have an 'endpoint: str' parameter.")

            # Validate 'endpoint' is annotated as str
            endpoint_param = params["endpoint"]
            if endpoint_param.annotation not in (str, inspect.Parameter.empty):
                raise ValueError(f"Function '{setup_fn.__name__}' parameter 'endpoint' must be annotated as 'str', " f"got '{endpoint_param.annotation}'.")

            # Validate 'filter_expression' if present
            if "filter_expression" in params:
                filter_param = params["filter_expression"]
                if filter_param.annotation != inspect.Parameter.empty:
                    origin = get_origin(filter_param.annotation)
                    args = get_args(filter_param.annotation)

                    is_union = origin is Union
                    has_filter_expression = FilterExpression in args if args else False
                    has_none = type(None) in args if args else False

                    if not (is_union and has_filter_expression and has_none):
                        raise ValueError(
                            f"Function '{setup_fn.__name__}' parameter 'filter_expression' must be annotated as " f"'Optional[FilterExpression]', got '{filter_param.annotation}'."
                        )

            # Identify configuration parameters
            configuration_params = [param_name for param_name in params.keys() if param_name not in ("endpoint", "filter_expression", "self")]

            # Parse documentation
            if not setup_fn.__doc__:
                raise ValueError(f"Function '{setup_fn.__name__}' decorated with @trigger is missing docstring")

            docstring = DocstringParser.parse(setup_fn.__doc__)

            # Create resolver decorator that will be attached to the setup function
            def resolver_decorator(resolver_fn):
                if not inspect.isfunction(resolver_fn):
                    raise TypeError("The resolver decorator can only be applied to functions.")

                # Validate resolver signature
                resolver_sig = inspect.signature(resolver_fn, eval_str=True)
                resolver_params = resolver_sig.parameters

                # Check that resolver has 'self' and 'request' parameters
                if "request" not in resolver_params:
                    raise ValueError(f"Resolver function '{resolver_fn.__name__}' must have a 'request: HTTPRequest' parameter.")

                # Validate resolver return type at decorator application time
                resolver_return_type = resolver_sig.return_annotation
                if resolver_return_type == inspect.Signature.empty:
                    raise ValueError(
                        f"Resolver function '{resolver_fn.__name__}' must have a return type annotation. " f"Expected: {expected_resolver_response_type.__name__}[EventType]"
                    )

                # Get the origin to check the response type
                return_origin = get_origin(resolver_return_type)
                if return_origin is None:
                    # Not a generic type - check if it's the exact class
                    if resolver_return_type != expected_resolver_response_type:
                        raise ValueError(
                            f"Resolver function '{resolver_fn.__name__}' for @trigger.{'shared' if is_shared_endpoint else 'non_shared'} "
                            f"must return {expected_resolver_response_type.__name__}[EventType]. "
                            f"Got '{resolver_return_type}' instead."
                        )
                else:
                    # Generic type - check if origin is a subclass of expected type
                    if not (inspect.isclass(return_origin) and issubclass(return_origin, expected_resolver_response_type)):
                        raise ValueError(
                            f"Resolver function '{resolver_fn.__name__}' for @trigger.{'shared' if is_shared_endpoint else 'non_shared'} "
                            f"must return {expected_resolver_response_type.__name__}[EventType]. "
                            f"Got '{resolver_return_type}' instead."
                        )

                # Create BookTriggerDescriptor now that we have both functions
                book_trigger = BookTriggerFactory.create(
                    identifier=setup_fn.__name__,
                    name=name,
                    is_manual=is_manual,
                    is_shared_endpoint=is_shared_endpoint,
                    python_signature=sig,
                    docstring=docstring,
                    configuration_params=configuration_params,
                    resolver_function_name=resolver_fn.__name__,
                )

                # Attach metadata to setup function
                setup_fn.__trigger__ = book_trigger
                setup_fn.__trigger_resolver_function_name__ = resolver_fn.__name__

                return resolver_fn

            # Return a TriggerSetupFunction wrapper with the resolver decorator
            return TriggerSetupFunction(setup_fn, resolver_decorator)

        return decorator
