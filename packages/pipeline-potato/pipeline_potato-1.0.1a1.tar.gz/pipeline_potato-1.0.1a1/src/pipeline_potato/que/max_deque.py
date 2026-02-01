from collections import deque
from typing import Any


class MaxDeque:
    def __init__(self, max_size: int):
        if max_size <= 0:
            raise ValueError("max_size must be positive")

        self._max_size = max_size
        self._queue = deque(maxlen=max_size)

    def __len__(self) -> int:
        return len(self._queue)


    @property
    def max_size(self):
        return self._max_size

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    @property
    def is_full(self) -> bool:
        return len(self) >= self._max_size

    @property
    def free_slots(self) -> int:
        return self.max_size - len(self)


    def peek(self, at: int) -> Any:
        return self._queue[at]

    def try_peek(self, at: int, default_value: Any = None) -> Any:
        try:
            return self._queue[at]
        except IndexError:
            return default_value

    def peek_list(self, start: int, end: int) -> list:
        if start > end:
            raise ValueError("start must be smaller than end")

        return [self._queue[i] for i in range(start, end + 1)]

    def can_push(self) -> bool:
        return self.max_size > len(self._queue)

    def try_push_one(self, item: Any) -> bool:
        if not self.can_push():
            return False

        self._queue.append(item)

        return True

    def try_push_some(self, items: list[Any]) -> list[Any]:
        if not items:
            return []

        to_push = min(len(items), self.max_size - len(self._queue))

        if to_push <= 0:
            return items

        self._queue.extend(items[:to_push])

        return items[to_push:]

    def pop_some(self, max_count: int = 1) -> list[Any]:
        if max_count <= 0:
            raise ValueError("max_count must be positive")

        pop_count = min(max_count, len(self._queue))

        return [self._queue.popleft() for _ in range(pop_count)]
