from abc import abstractmethod
from typing import Callable

from pipeline_potato.core import APipeline, APotato, StepId, AJob
from pipeline_potato.engine.potato import Potato


class PipelineBridge(APipeline):

    class AParentPipeline(Potato.AEmitter):
        @property
        @abstractmethod
        def args(self) -> tuple:
            ...

        @property
        @abstractmethod
        def kwargs(self) -> dict:
            ...

        @abstractmethod
        def run_job(self, job: AJob, on_complete: Callable[[AJob], None]) -> None:
            ...

        @abstractmethod
        def complete(self, step_id: StepId) -> None:
            ...


    def __init__(self, step_id: StepId, parent: AParentPipeline) -> None:
        self._step_id   : StepId                         = step_id
        self._parent    : PipelineBridge.AParentPipeline    = parent


    @property
    def args(self) -> tuple:
        return self._parent.args

    @property
    def kwargs(self) -> dict:
        return self._parent.kwargs


    def run_job(self, job: AJob, on_complete: Callable[[AJob], None]) -> None:
        self._parent.run_job(job, on_complete)

    def complete(self) -> None:
        self._parent.complete(self._step_id)

    def potato(self) -> APotato:
        return Potato(self._step_id, self._parent)
