from pipeline_potato.core import AJob, StepId, ConsumeCallback
from pipeline_potato.que.potato_queue import PotatoQueue


class ConsumeQueueJob(AJob):
    def __init__(
        self,
        *,
        name                : str,
        step_id             : StepId,
        consume_callback    : ConsumeCallback,
        page_size           : int,
        queue               : PotatoQueue,
    ) -> None:
        super().__init__(name, step_id)

        self._consume_callback      : ConsumeCallback   = consume_callback
        self._page_size             : int               = page_size
        self._queue                 : PotatoQueue       = queue
        self._current_batch_size    : int               = 0


    def report(self) -> dict:
        r = super().report()

        r.update({
            'current_batch_size': self._current_batch_size,
        })

        return r


    def _try_wait_for_work(self) -> list | None:
        data = self._queue.try_deque(self._page_size)
        return data or None

    async def _wait_for_work(self) -> list | None:
        data = await self._queue.wait_deque(self._page_size)
        return data or None

    async def _do_work(self, payload: list) -> None:
        self._current_batch_size = len(payload)

        try:
            await self._consume_callback(payload)
        finally:
            self._current_batch_size = 0
