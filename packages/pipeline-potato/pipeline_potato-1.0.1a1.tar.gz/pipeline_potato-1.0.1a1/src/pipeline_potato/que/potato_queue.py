import asyncio

from pipeline_potato.exceptions import AbortException
from pipeline_potato.que.max_deque import MaxDeque


class PotatoQueue:
    def __init__(self, max_size: int) -> None:
        self._queue = MaxDeque(max_size)

        self._on_free_space = asyncio.Event()
        self._on_free_space.set()

        self._on_has_items = asyncio.Event()
        self._on_has_items.clear()

        self._is_aborted = False
        self._is_complete = False

    def __len__(self):
        return len(self._queue)


    @property
    def is_aborted(self) -> bool:
        return self._is_aborted

    @property
    def max_queue(self) -> MaxDeque:
        return self._queue

    @property
    def max_size(self) -> int:
        return self._queue.max_size

    @property
    def is_empty(self) -> bool:
        return self._queue.is_empty


    def _check_for_abort(self) -> None:
        if self._is_aborted:
            raise AbortException()


    def try_enqueue_items(self, items: list) -> list:
        if not items:
            return []

        self._is_complete = False
        self._check_for_abort()

        remaining_items = self._queue.try_push_some(items)

        if len(remaining_items) < len(items):
            if self._queue.is_full:
                self._on_free_space.clear()

            self._on_has_items.set()

        return remaining_items

    async def wait_enqueue_items(self, items: list) -> None:
        while items:
            await self._on_free_space.wait()
            items = self.try_enqueue_items(items)

    def try_deque(self, max_count: int) -> list:
        if max_count <= 0:
            raise ValueError("max_count must be greater than 0")

        self._check_for_abort()

        items = self._queue.pop_some(max_count)

        if items:
            self._on_free_space.set()

        if self._queue.is_empty:
            self._on_has_items.clear()

        return items

    async def wait_deque(self, max_count: int) -> list:
        if max_count <= 0:
            raise ValueError("max_count must be greater than 0")

        items = []

        while not items:
            if self._is_complete and self._queue.is_empty:
                break

            await self._on_has_items.wait()
            items = self.try_deque(max_count)

        return items

    def abort(self) -> None:
        if self._is_aborted:
            return

        self._is_aborted = True
        self._on_free_space.set()
        self._on_has_items.set()

    def complete(self) -> None:
        if self._is_complete:
            return

        self._is_complete = True
        self._on_free_space.set()
        self._on_has_items.set()
