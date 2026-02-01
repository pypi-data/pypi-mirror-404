import asyncio
from abc import ABC, abstractmethod
from typing import Any

from pipeline_potato.core.types import StepId
from pipeline_potato.enums import JobState
from pipeline_potato.exceptions import AbortException


class AJob(ABC):
    class BlockedJob:
        def __init__(self, parent: "AJob") -> None:
            self._parent : AJob = parent

        def __enter__(self) -> None:
            self._parent._set_state(JobState.BLOCKED)

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: object | None
        ) -> None:
            self._parent._set_state(JobState.RUNNING)


    def __init__(self, job_name: str, step_id: StepId) -> None:
        self._step_id   : StepId    = step_id
        self._job_name  : str       = job_name
        self._state     : JobState  = JobState.IDLE


    def _set_state(self, state: JobState) -> None:
        if self._state == state:
            return
        elif self.is_aborted:
            raise AbortException()
        else:
            self._state = state


    @property
    def step_id(self) -> StepId:
        return self._step_id

    @property
    def job_name(self) -> str:
        return self._job_name

    @property
    def state(self) -> JobState:
        return self._state

    @property
    def is_aborted(self) -> bool:
        return self._state == JobState.ABORTED

    @property
    def is_blocked(self) -> bool:
        return self._state == JobState.BLOCKED

    @property
    def is_idle(self) -> bool:
        return self._state == JobState.IDLE

    @property
    def is_running(self) -> bool:
        return self._state == JobState.RUNNING


    @abstractmethod
    def _try_wait_for_work(self) -> Any | None:
        ...

    @abstractmethod
    async def _wait_for_work(self) -> Any | None:
        ...

    @abstractmethod
    async def _do_work(self, payload: Any) -> None:
        ...


    def report(self) -> dict:
        return {
            'name'  : self.job_name,
            'state' : str(self._state),
        }

    def abort(self) -> None:
        self._set_state(JobState.ABORTED)

    def blocked(self) -> "AJob.BlockedJob":
        return AJob.BlockedJob(self)

    async def run(self) -> None:
        while not self.is_aborted:
            payload = self._try_wait_for_work()

            if payload is None:
                self._set_state(JobState.IDLE)

                payload = await self._wait_for_work()

                if payload is None:
                    return

            self._set_state(JobState.RUNNING)

            # This extra step prevents non-async steps from hogging the cpu-time
            # See: test_non_async_steps_do_no_block
            task = asyncio.create_task(self._do_work(payload))

            await task
