from abc import ABC, abstractmethod

from pipeline_potato.core import APipeline, APotato, StepId, AJob
from pipeline_potato.enums.step_state import StepState
from pipeline_potato.exceptions import AbortException


class AStepDefinition(ABC):
    def __init__(self, step_id: StepId, pipeline: APipeline, name: str) -> None:
        self._step_id           : StepId         = step_id
        self._state             : StepState         = StepState.ACTIVE
        self._name              : str               = name
        self._pipeline          : APipeline         = pipeline
        self._complete_set      : bool              = False
        self._jobs              : dict[int, AJob]   = {}
        self._consumed_count    : int               = 0

    def __repr__(self):
        return f'{self.__class__.__name__}<name={self._name}, step_id={self._step_id}>'


    def __complete(self) -> None:
        if self._state == StepState.ACTIVE:
            self._state = StepState.COMPLETED

        self._pipeline.complete()

    def __handle_job_complete(self, job: AJob) -> None:
        if id(job) not in self._jobs:
            raise RuntimeError(f'Missing job ID {id(job)} in job\'s list')

        del self._jobs[id(job)]

        if self.jobs_count == 0 and self._complete_set:
            self.__complete()


    def _potato(self) -> APotato:
        return self._pipeline.potato()

    def _mark_complete(self) -> None:
        if self.jobs_count > 0:
            self._complete_set = True
        else:
            self.__complete()

    def _spawn_job(self, job: AJob) -> None:
        if id(job) in self._jobs:
            raise RuntimeError(f'Job with ID {id(job)} was already spawned')
        elif self.is_aborted:
            raise AbortException()
        elif self.is_complete:
            self._state = StepState.ACTIVE

        self._jobs[id(job)] = job

        self._pipeline.run_job(job, self.__handle_job_complete)

    def _consumed_items(self, items: list) -> None:
        self._consumed_count += len(items)

    def _consumed_total(self, count: int) -> None:
        self._consumed_count += count


    @property
    def total_consumed(self) -> int:
        return self._consumed_count

    @property
    def step_name(self) -> str:
        return self._name

    @property
    def jobs_count(self) -> int:
        return len(self._jobs)

    @property
    def is_complete_set(self) -> bool:
        return self._complete_set

    @property
    def step_id(self) -> StepId:
        return self._step_id

    @property
    def state(self) -> StepState:
        return self._state

    @property
    def is_active(self) -> bool:
        return self.state == StepState.ACTIVE

    @property
    def is_complete(self) -> bool:
        return self.state == StepState.COMPLETED

    @property
    def is_aborted(self) -> bool:
        return self.state == StepState.ABORTED

    @property
    def jobs(self) -> list[AJob]:
        return list(self._jobs.values())

    def mark_abort(self) -> None:
        self._state = StepState.ABORTED

    def report(self) -> dict:
        return {
            'step'  : str(self),
            'state' : str(self._state),
            'stats' : {
                'total_consumed' : self.total_consumed,
            },
            'jobs'  : [j.report() for j in self._jobs.values()],
        }

    @abstractmethod
    def try_digest(self, items: list) -> list:
        ...

    @abstractmethod
    async def digest(self, items: list) -> None:
        ...

    @abstractmethod
    def no_more_data(self) -> None:
        ...

    @abstractmethod
    def abort(self) -> None:
        ...
