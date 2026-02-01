from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from pipeline_potato import APotato


class ATreeTraversal(ABC):

    @abstractmethod
    def traverse(self, potato: APotato, payload: Any, index: list[int]) -> AsyncGenerator[list, None]:
        ...
