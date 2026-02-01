import inspect
from typing import Any


class Generics:
    @staticmethod
    def is_callable_coroutine_function(f: Any) -> bool:
        if not callable(f):
            return False

        return (
            inspect.iscoroutinefunction(f) or
            (hasattr(f, '__call__') and inspect.iscoroutinefunction(f.__call__))
        )
