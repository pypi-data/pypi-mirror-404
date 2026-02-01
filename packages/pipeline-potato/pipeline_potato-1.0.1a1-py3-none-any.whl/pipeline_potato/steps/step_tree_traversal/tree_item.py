from collections.abc import AsyncIterator
from typing import Any


class TreeItem:
    def __init__(self, order: int, index: list[int], payload: Any) -> None:
        self._order     : int                          = order
        self._payload   : Any                          = payload
        self._index     : list[int]                    = index
        self._offset    : int                          = 0
        self._generator : AsyncIterator[list] | None   = None


    @property
    def order(self) -> int:
        return self._order

    @property
    def index(self) -> list[int]:
        return self._index

    @property
    def depth(self) -> int:
        return len(self.index)

    @property
    def payload(self) -> Any:
        return self._payload

    @property
    def generator(self) -> AsyncIterator[list] | None:
        return self._generator

    @property
    def is_root(self) -> bool:
        return len(self.index) == 0

    @property
    def was_called(self) -> bool:
        return self.generator is not None


    def __lt__(self, other: "TreeItem") -> bool:
        if self.order < other.order:
            return True
        elif self.order > other.order:
            return False

        for i in range(len(self.index)):
            if len(other.index) <= i:
                return True
            elif self.index[i] < other.index[i]:
                return True
            elif self.index[i] > other.index[i]:
                return False

        return len(self.index) > len(other.index)


    def set_generator(self, generator: AsyncIterator[list] | None) -> None:
        if self.was_called:
            raise RuntimeError("Generator was already set")

        self._generator = generator

    def create_children(self, items: list) -> list["TreeItem"]:
        tree_items: list[TreeItem] = []

        for i in range(len(items)):
            tree_items.append(
                TreeItem(
                    order   = self.order,
                    index   = self.index + [self._offset + i],
                    payload = items[i],
                )
            )

        self._offset += len(items)

        return tree_items
