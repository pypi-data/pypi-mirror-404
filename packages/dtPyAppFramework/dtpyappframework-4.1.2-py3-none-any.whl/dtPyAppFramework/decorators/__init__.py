from functools import wraps
from typing import Any
import threading
import inspect


def _resolve_key_from_args(key_name, class_, args, kwargs):
    """Resolve the singleton key value from function arguments."""
    if key_name is None:
        return "GLOBAL"
    if key_name in kwargs:
        return kwargs[key_name]
    sig = inspect.signature(class_.__init__)
    param_names = list(sig.parameters.keys())[1:]  # Skip 'self'
    if key_name in param_names:
        key_index = param_names.index(key_name)
        if key_index < len(args):
            return args[key_index]
    return "GLOBAL"


def _copy_class_attributes(wrapper, class_):
    """Copy class attributes to the wrapper function."""
    wrapper.__name__ = class_.__name__
    wrapper.__qualname__ = class_.__qualname__
    wrapper.__module__ = class_.__module__
    wrapper.__doc__ = class_.__doc__
    wrapper.__annotations__ = getattr(class_, '__annotations__', {})


def singleton(key_name: str = None) -> Any:
    """
    Decorator to create a singleton class. If a key is passed, it will allow
    for multiple instances of the same singleton to exist.

    :param key_name: The name of the key to monitor for multiple
    instances
    """

    def wrap(class_: Any) -> Any:
        instances = {}
        _lock = threading.Lock()

        @wraps(class_)
        def get_instance(*args, **kwargs):
            key_value = _resolve_key_from_args(key_name, class_, args, kwargs)
            class_key = f"{class_.__name__}_{key_name}_{key_value}"

            if class_key not in instances:
                with _lock:
                    if class_key not in instances:
                        instances[class_key] = class_(*args, **kwargs)

            return instances[class_key]

        _copy_class_attributes(get_instance, class_)

        return get_instance

    return wrap
