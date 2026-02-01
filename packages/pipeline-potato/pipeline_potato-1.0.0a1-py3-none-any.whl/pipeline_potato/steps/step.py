from abc import ABC, abstractmethod
from typing import Callable, Protocol, Any

from pipeline_potato.core import APipeline, APotato, StepId
from pipeline_potato.engine import AStepDefinition, register_step
from pipeline_potato.que.potato_queue import PotatoQueue
from pipeline_potato.steps.step_step.consume_queue_job import ConsumeQueueJob


class TDigestCallback(Protocol):
    __name__: str

    def __init__(self, **kwargs: Any) -> None:
        pass


    async def __call__(
        self,
        potato: APotato,
        items: list,
        *args: Any,
        **kwargs: Any
    ) -> None:
        ...


class AStep(ABC):
    @abstractmethod
    async def digest(self, potato: APotato, items: list) -> None:
        ...


TStepTarget = TDigestCallback | type[AStep]


class Step(AStepDefinition):
    def __init__(
        self,
        *,
        step_id     : StepId,
        pipeline    : APipeline,
        name        : str,
        instance    : AStep | None,
        callback    : TDigestCallback | None,
        buffer_size : int,
        page_size   : int,
        concurrency : int,
    ) -> None:
        super().__init__(step_id, pipeline, name)

        if buffer_size <= 0:
            raise ValueError("buffer_size must be positive")
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        if concurrency <= 0:
            raise ValueError("concurrency must be positive")
        if page_size > buffer_size:
            raise ValueError("page_size must be less than buffer_size")

        self._func          : TDigestCallback | None = callback
        self._inst          : AStep | None            = instance
        self._started       : bool                    = False
        self._queue         : PotatoQueue             = PotatoQueue(max_size=buffer_size)
        self._page_size     : int                     = page_size
        self._concurrency   : int                     = concurrency
        self._job_id        : int                     = 0


    async def _consume_payload(self, items: list) -> None:
        with self._potato() as potato:
            if self._inst:
                await self._inst.digest(
                    potato,
                    items,
                )
            else:
                assert self._func is not None, "Either _inst or _func must be set"

                await self._func(
                    potato,
                    items,
                    *self._pipeline.args,
                    **self._pipeline.kwargs,
                )

        self._consumed_items(items)

    def _spawn_consumers(self) -> None:
        while self.jobs_count < self._concurrency:
            self._spawn_job(
                ConsumeQueueJob(
                    name                = f"{self.step_name} - Consumer #{self._job_id}",
                    step_id             = self.step_id,
                    consume_callback    = self._consume_payload,
                    page_size           = self._page_size,
                    queue               = self._queue,
                )
            )

            self._job_id += 1


    @property
    def concurrency(self) -> int:
        return self._concurrency


    def report(self) -> dict:
        r = super().report()

        r.update({
            'config': {
                'page_size'         : self._page_size,
                'max_buffer_size'   : self._queue.max_size,
                'concurrency'       : self.concurrency,
            },
            'current_buffer_size':  len(self._queue),
        })

        return r

    def try_digest(self, items: list) -> list:
        if not items:
            return []

        self._spawn_consumers()

        return self._queue.try_enqueue_items(items)

    async def digest(self, items: list) -> None:
        if not items:
            return

        self._spawn_consumers()

        await self._queue.wait_enqueue_items(items)

    def abort(self) -> None:
        self._queue.abort()
        self.mark_abort()

    def no_more_data(self) -> None:
        self._mark_complete()
        self._queue.complete()


def __create_step(
    *,
    target      : TStepTarget,
    buffer_size : int,
    page_size   : int,
    concurrency : int,
) -> TStepTarget:
    def build(a_pipeline: APipeline) -> Step:
        if isinstance(target, type) and issubclass(target, AStep):
            instance = target(*a_pipeline.args, **a_pipeline.kwargs)  # type: ignore[misc]
            callback = None
        else:
            instance = None
            callback = target

        return Step(
            step_id     = id(target),
            pipeline    = a_pipeline,
            name        = target.__name__,
            instance    = instance,
            callback    = callback,
            buffer_size = buffer_size,
            page_size   = page_size,
            concurrency = concurrency,
        )

    register_step(target, build)

    return target


def step(
    *,
    buffer_size : int   = 10_000,
    page_size   : int   = 100,
    concurrency : int   = 1,
) -> Callable[[TStepTarget], TStepTarget]:
    def _step_creator(target: TStepTarget) -> TStepTarget:
        return __create_step(
            target      = target,
            buffer_size = buffer_size,
            page_size   = page_size,
            concurrency = concurrency,
        )

    return _step_creator
