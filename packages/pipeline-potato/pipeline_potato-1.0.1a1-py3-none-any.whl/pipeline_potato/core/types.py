from collections.abc import AsyncIterator
from typing import Any, Awaitable, Callable


StepId                  = str | int
ConsumeCallback         = Callable[[list], Awaitable[None]]
CreateTraverseCallback  = Callable[[Any, list[int]], AsyncIterator[list]]


def get_step_id(source: object | StepId) -> StepId:
    if isinstance(source, int | str):
        return source

    return id(source)
