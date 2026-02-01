from abc import ABC, abstractmethod
from typing import Callable

from pipeline_potato.core.a_job import AJob
from pipeline_potato.core.a_potato import APotato


class APipeline(ABC):
    @property
    @abstractmethod
    def args(self) -> tuple:
        ...

    @property
    @abstractmethod
    def kwargs(self) -> dict:
        ...

    @abstractmethod
    def complete(self) -> None:
        ...

    @abstractmethod
    def run_job(self, job: AJob, on_complete: Callable[[AJob], None]) -> None:
        ...

    @abstractmethod
    def potato(self) -> APotato:
        ...
