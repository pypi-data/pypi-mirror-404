import asyncio
from abc import ABC, abstractmethod
from typing import Callable, Any


class APotato(ABC):
    @staticmethod
    def _validate(func: Any, payload: Any) -> None:
        if not callable(func):
            raise TypeError("emit target is not a callable!")

        if payload is None:
            raise TypeError("Payload not provided for target")

        if not isinstance(payload, list):
            raise TypeError(f"Invalid payload type - {type(payload)}")

    @staticmethod
    def _validate_pair(pair: Any) -> None:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError("Invalid format for emit function")

        APotato._validate(pair[0], pair[1])

    async def _emit_all(self, funcs: list[tuple[Callable, list]]) -> None:
        tasks = [self._emit(func, items) for [func, items] in funcs]

        await asyncio.gather(*tasks)

    @abstractmethod
    def __enter__(self) -> "APotato":
        ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None
    ) -> None:
        ...

    @abstractmethod
    async def _emit(self, target: Any, items: list) -> None:
        ...

    async def __call__(
        self,
        target: Callable | list[tuple[Callable, list]],
        payload: list | None = None
    ) -> None:
        if target is None:
            raise TypeError("emit target not selected")

        if callable(target):
            APotato._validate(target, payload)

            if not payload:
                return

            await self._emit(target, payload)

        elif isinstance(target, list):
            if payload is not None:
                raise TypeError("Invalid emit call. Expected None at `payload` empty when target is a list")

            if not target:
                return

            for item in target:
                APotato._validate_pair(item)

            await self._emit_all(target)

        else:
            raise TypeError("target must be either callable or list of (callable, list) tuples")
