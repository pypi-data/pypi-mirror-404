from collections.abc import Awaitable
from typing import Callable, Any

from pipeline_potato.core import AJob


class CallbackJob(AJob):
    def __init__(self, name: str, callback: Callable[[], Awaitable[bool]]) -> None:
        super().__init__(name, 1)

        self._callback  : Callable[[], Awaitable[bool]] = callback
        self._continue  : bool                          = True


    def _try_wait_for_work(self) -> Any | None:
        return True if self._continue else None

    async def _wait_for_work(self) -> Any | None:
        return None

    async def _do_work(self, _: Any) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        try:
            self._continue = await self._callback()
        except Exception as e:
            self._continue = False
            raise e
