import asyncio
from queue import PriorityQueue

from pipeline_potato.exceptions import AbortException
from pipeline_potato.que.potato_queue import PotatoQueue
from pipeline_potato.steps.step_tree_traversal.tree_item import TreeItem


class TreeTraversalQueue:
    def __init__(self, buffer_size: int) -> None:
        self._payload_queue     : PotatoQueue   = PotatoQueue(max_size=buffer_size)
        self._traversal_queue   : PriorityQueue = PriorityQueue()
        self._on_has_items      : asyncio.Event = asyncio.Event()
        self._order             : int           = 0
        self._is_aborted        : bool          = False
        self._is_complete       : bool          = False

        self._on_has_items.clear()


    @property
    def is_empty(self) -> bool:
        return self._payload_queue.is_empty and self._traversal_queue.empty()

    @property
    def total_buffer_size(self) -> int:
        return self.buffer_size + self.traversal_buffer_size

    @property
    def max_buffer_size(self) -> int:
        return self._payload_queue.max_size

    @property
    def buffer_size(self) -> int:
        return len(self._payload_queue)

    @property
    def traversal_buffer_size(self) -> int:
        return len(self._traversal_queue.queue)


    def _check_for_abort(self) -> None:
        if self._is_aborted:
            raise AbortException()

    def _reset_has_items(self) -> None:
        if self.is_empty:
            self._on_has_items.clear()

    def _on_new_payload(self) -> None:
        self._on_has_items.set()
        self._is_complete = False


    def push_tree_item(self, item: TreeItem) -> None:
        self._check_for_abort()
        self._traversal_queue.put(item)
        self._on_has_items.set()

    def push_tree_items(self, items: list[TreeItem]) -> None:
        self._check_for_abort()

        if not items:
            return

        for item in items:
            self._traversal_queue.put(item)

        self._on_has_items.set()

    def try_push_items(self, items: list) -> list:
        if not items:
            return []

        self._check_for_abort()
        self._on_new_payload()

        return self._payload_queue.try_enqueue_items(items)

    async def wait_push_items(self, items: list) -> None:
        items = self.try_push_items(items)

        # Because items are read one by one anyway, there is no reason to push more than one item per wait.
        for item in items:
            self._on_new_payload()
            await self._payload_queue.wait_enqueue_items([item])

    def next(self) -> TreeItem | None:
        self._check_for_abort()

        if not self._traversal_queue.empty():
            item = self._traversal_queue.get()
            self._reset_has_items()
            return item

        items = self._payload_queue.try_deque(1)

        if items:
            self._reset_has_items()

            order = self._order
            self._order += 1

            return TreeItem(
                order=order,
                index=[],
                payload=items[0]
            )

        return None

    async def wait_next(self) -> TreeItem | None:
        next_item = self.next()

        while not next_item:
            if self._is_complete and self.is_empty:
                break

            await self._on_has_items.wait()
            next_item = self.next()

        return next_item

    def complete(self) -> None:
        if self._is_complete:
            return

        self._is_complete = True
        self._on_has_items.set()

    def abort(self) -> None:
        self._is_aborted = True

        self._traversal_queue.queue.clear()
        self._payload_queue.abort()

        self.complete()
