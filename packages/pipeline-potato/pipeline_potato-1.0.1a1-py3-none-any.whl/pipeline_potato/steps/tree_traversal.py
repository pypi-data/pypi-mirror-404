from collections.abc import AsyncIterator
from typing import TypeVar, Callable, Any

from pipeline_potato.core import APipeline, StepId
from pipeline_potato.engine import AStepDefinition, register_step
from pipeline_potato.exceptions import InvalidStepDefinitionException
from pipeline_potato.steps.step_tree_traversal.a_tree_traversal import ATreeTraversal
from pipeline_potato.steps.step_tree_traversal.tree_traversal_job import TreeTraversalJob
from pipeline_potato.steps.step_tree_traversal.tree_traversal_queue import TreeTraversalQueue

T = TypeVar("T")

t_traversal_target = type[ATreeTraversal]  # pylint: disable=invalid-name


class TreeTraversalStep(AStepDefinition):
    def __init__(
        self,
        *,
        step_id     : StepId,
        pipeline    : APipeline,
        name        : str,
        instance    : ATreeTraversal,
        buffer_size : int = 1_000,
        concurrency : int = 1,
    ) -> None:
        super().__init__(step_id, pipeline, name)

        if buffer_size <= 0:
            raise ValueError("buffer_size must be positive")
        if concurrency <= 0:
            raise ValueError("concurrency must be positive")

        self._job_id        : int                   = 0
        self._instance      : ATreeTraversal        = instance
        self._queue         : TreeTraversalQueue    = TreeTraversalQueue(buffer_size)
        self._concurrency   : int                   = concurrency


    async def _traverse(self, payload: Any, index: list[int]) -> AsyncIterator[list]:
        with self._potato() as potato:
            iterator = self._instance.traverse(potato, payload, index)

            async for data in iterator:
                self._consumed_total(1)
                yield data

    def _spawn_consumers(self) -> None:
        target_count = min(self._concurrency, self._queue.total_buffer_size)

        while self.jobs_count < target_count:
            self._spawn_job(
                TreeTraversalJob(
                    job_name            = f"{self.step_name} - Traversal #{self._job_id}",
                    step_id             = self.step_id,
                    callback            = self._traverse,
                    queue               = self._queue,
                    on_items_callback   = self._spawn_consumers,
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
                'max_buffer_size'   : self._queue.max_buffer_size,
                'concurrency'       : self.concurrency,
            },
            'current_buffer_size'           : self._queue.buffer_size,
            'current_traversal_buffer_size' : self._queue.traversal_buffer_size,
        })

        return r

    def try_digest(self, items: list) -> list:
        items = self._queue.try_push_items(items)
        self._spawn_consumers()
        return items

    async def digest(self, items: list) -> None:
        await self._queue.wait_push_items(items)
        self._spawn_consumers()

    def no_more_data(self) -> None:
        self._mark_complete()
        self._queue.complete()

    def abort(self) -> None:
        self._queue.abort()
        self.mark_abort()


def __validate_target(target: T) -> T | t_traversal_target:
    if isinstance(target, type) and issubclass(target, ATreeTraversal):
        return target

    raise InvalidStepDefinitionException()


def __create_step(
    *,
    target      : t_traversal_target,
    buffer_size : int,
    concurrency : int,
) -> t_traversal_target:
    def build(a_pipeline: APipeline) -> TreeTraversalStep:
        return TreeTraversalStep(
            step_id     = id(target),
            pipeline    = a_pipeline,
            name        = target.__name__,
            instance    = target(*a_pipeline.args, **a_pipeline.kwargs),  # type: ignore[misc]
            buffer_size = buffer_size,
            concurrency = concurrency,
        )

    register_step(target, build)

    return target


def tree_traversal(
    *,
    buffer_size : int   = 10_000,
    concurrency : int   = 1,
) -> Callable[[t_traversal_target], t_traversal_target]:
    def _step_creator(target: t_traversal_target) -> t_traversal_target:
        target = __validate_target(target)

        return __create_step(
            target      = target,
            buffer_size = buffer_size,
            concurrency = concurrency,
        )

    return _step_creator
