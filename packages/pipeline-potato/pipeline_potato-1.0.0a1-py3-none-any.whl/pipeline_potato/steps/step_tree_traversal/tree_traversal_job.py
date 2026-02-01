import asyncio
from typing import Any, Callable

from pipeline_potato.core import AJob, CreateTraverseCallback, StepId
from pipeline_potato.steps.step_tree_traversal.tree_item import TreeItem
from pipeline_potato.steps.step_tree_traversal.tree_traversal_queue import TreeTraversalQueue


class TreeTraversalJob(AJob):
    def __init__(
        self,
        *,
        job_name            : str,
        step_id             : StepId,
        callback            : CreateTraverseCallback,
        on_items_callback   : Callable[[], None],
        queue               : TreeTraversalQueue,
    ) -> None:
        super().__init__(job_name, step_id)

        self._callback = callback
        self._queue = queue
        self._on_items_callback = on_items_callback


    def _try_wait_for_work(self) -> Any | None:
        return self._queue.next()

    async def _wait_for_work(self) -> Any | None:
        return await self._queue.wait_next()

    async def _do_work(self, payload: Any) -> None:
        if not isinstance(payload, TreeItem):
            raise TypeError(f"Payload must be of type TreeItem but got {type(payload)}")

        if not payload.was_called:
            generator = self._callback(payload.payload, payload.index)
            payload.set_generator(generator)

        async def get_next() -> list:
            assert payload.generator is not None
            return await anext(payload.generator)

        try:
            items = await asyncio.create_task(get_next())
        except StopAsyncIteration:
            return

        self._queue.push_tree_item(payload)
        self._on_items_callback()

        if items:
            children_items = payload.create_children(items)
            self._queue.push_tree_items(children_items)
