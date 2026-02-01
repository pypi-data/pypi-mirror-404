from abc import ABC, abstractmethod
from typing import Any, TypeVar, Callable
from typing import Awaitable

from pipeline_potato.core import APipeline, APotato, StepId
from pipeline_potato.engine import AStepDefinition, register_step
from pipeline_potato.engine.generics import Generics
from pipeline_potato.engine.jobs.callback_job import CallbackJob
from pipeline_potato.exceptions import InvalidStepDefinitionException


class AEntryPoint(ABC):
    @abstractmethod
    async def begin(self, potato: APotato) -> None:
        ...


class EntryPointStep(AStepDefinition):
    def __init__(
        self,
        *,
        callback: Callable[..., Awaitable],
        step_id: StepId,
        pipeline: APipeline,
        name: str
    ) -> None:
        super().__init__(step_id, pipeline, name)

        self._callback: Callable[..., Awaitable]   = callback


    def run(self, *args: Any, **kwargs: Any) -> None:
        async def _run_wrapper() -> bool:
            self._mark_complete()

            with self._potato() as potato:
                await self._callback(potato, *args, **kwargs)

            self._consumed_total(1)

            return False

        self._spawn_job(CallbackJob(self.step_name, _run_wrapper))

    def try_digest(self, items: list) -> list:
        raise NotImplementedError()

    async def digest(self, items: list) -> None:
        raise NotImplementedError()

    def no_more_data(self) -> None:
        self._mark_complete()

    def abort(self) -> None:
        self.mark_abort()


T = TypeVar("T")


def __validate_callback_for_target(target: object) -> Callable[..., Awaitable[None]]:
    if isinstance(target, type) and issubclass(target, AEntryPoint):
        async def callback(potato: APotato, *args: Any, **kwargs: Any) -> None:
            assert callable(target), "Target must be callable after isinstance check - this is a type narrowing issue"

            # noinspection PyCallingNonCallable
            instance: AEntryPoint = target(*args, **kwargs)
            await instance.begin(potato)

    elif Generics.is_callable_coroutine_function(target):
        callback = target  # pyright: ignore[reportAssignmentType]

    else:
        raise InvalidStepDefinitionException()

    return callback


def entry_point(target: T) -> T:
    callback = __validate_callback_for_target(target)

    def build(a_pipeline: APipeline) -> AStepDefinition:
        return EntryPointStep(
            callback=callback,
            step_id=id(target),
            pipeline=a_pipeline,
            name=target.__name__,  # pyright: ignore[reportAttributeAccessIssue]
        )

    register_step(target, build)

    return target
