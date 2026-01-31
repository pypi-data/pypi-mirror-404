from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class TriggerSetupFunction:
    """
    Wrapper for a trigger setup function that provides a .resolver decorator method.

    This class makes the setup function callable while also providing the .resolver
    attribute for type checkers to understand.
    """

    def __init__(self, func: Callable, resolver_decorator: Callable[[Callable], Callable]):
        """
        Initialize the trigger setup function wrapper.

        Args:
            func: The original setup function
            resolver_decorator: The decorator function for attaching resolvers
        """
        # Set these first before any other attribute access
        object.__setattr__(self, "_func", func)
        object.__setattr__(self, "_resolver_decorator", resolver_decorator)

        # Copy over function attributes for introspection
        object.__setattr__(self, "__name__", func.__name__)
        object.__setattr__(self, "__doc__", func.__doc__)
        object.__setattr__(self, "__module__", func.__module__)
        object.__setattr__(self, "__qualname__", func.__qualname__)
        object.__setattr__(self, "__annotations__", func.__annotations__)

        # Copy trigger metadata
        for attr in dir(func):
            if attr.startswith("__trigger"):
                try:
                    object.__setattr__(self, attr, getattr(func, attr))
                except AttributeError:
                    pass

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the wrapped setup function."""
        func = object.__getattribute__(self, "_func")
        return func(*args, **kwargs)

    def resolver(self, func: F) -> F:
        """
        Decorator to attach a resolver function to this trigger setup.

        Args:
            func: The resolver function

        Returns:
            The resolver function (unchanged)
        """
        resolver_decorator = object.__getattribute__(self, "_resolver_decorator")
        wrapped_func = object.__getattribute__(self, "_func")

        result = resolver_decorator(func)

        # Sync metadata from the underlying function after resolver is attached
        for attr in ("__trigger__", "__trigger_resolver_function_name__"):
            if hasattr(wrapped_func, attr):
                setattr(self, attr, getattr(wrapped_func, attr))
        return result

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        """Support instance methods via descriptor protocol."""
        if obj is None:
            return self
        import functools

        func = object.__getattribute__(self, "_func")
        return functools.partial(func, obj)

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped function for metadata access."""
        # Use object.__getattribute__ to avoid recursion
        try:
            func = object.__getattribute__(self, "_func")
        except AttributeError as exc:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'") from exc
        return getattr(func, name)


def is_trigger_function(x: Any):
    return isinstance(x, TriggerSetupFunction)
