from abc import ABC, abstractmethod
from typing import Any

from pipeline_potato.core import APotato, StepId
from pipeline_potato.exceptions import ActionOutOfContextException


class Potato(APotato):

    class AEmitter(ABC):
        @abstractmethod
        async def emit(self, step_id: StepId, target: Any, items: list) -> None:
            ...


    def __init__(self, step_id : StepId, parent: AEmitter) -> None:
        self._step_id   : StepId         = step_id
        self._parent    : Potato.AEmitter   = parent
        self._is_active : bool              = False


    def __enter__(self) -> APotato:
        self._is_active = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None
    ) -> None:
        self._is_active = False


    async def _emit(self, target: Any, items: list) -> None:
        if not self._is_active:
            raise ActionOutOfContextException()

        await self._parent.emit(self._step_id, target, items)
