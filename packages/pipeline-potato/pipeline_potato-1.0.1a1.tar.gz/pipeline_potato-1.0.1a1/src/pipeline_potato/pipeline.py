from typing import Callable, Any

from pipeline_potato.core import TasksWaiter, StepId, get_step_id, AJob
from pipeline_potato.engine import (
    PipelineBridge,
    StepsRegistry,
    AStepDefinition,
    create_step
)
from pipeline_potato.enums import PipelineState
from pipeline_potato.exceptions import AbortException
from pipeline_potato.graph.steps_graph import StepsGraph
from pipeline_potato.steps.entry_point import EntryPointStep


class Pipeline(PipelineBridge.AParentPipeline):
    def __init__(self) -> None:
        self._sub_tasks : TasksWaiter       = TasksWaiter()
        self._graph     : StepsGraph        = StepsGraph()
        self._steps     : StepsRegistry     = StepsRegistry()
        self._state     : PipelineState     = PipelineState.IDLE
        self._jobs      : dict[int, AJob]   = {}

        self._args      : tuple = ()
        self._kwargs    : dict = {}


    @property
    def args(self) -> tuple:
        return self._args

    @property
    def kwargs(self) -> dict:
        return self._kwargs

    @property
    def graph(self) -> StepsGraph:
        return self._graph

    @property
    def steps(self) -> StepsRegistry:
        return self._steps

    @property
    def state(self) -> PipelineState:
        return self._state

    @property
    def sub_tasks(self) -> TasksWaiter:
        return self._sub_tasks

    @property
    def jobs(self) -> list[AJob]:
        return list(self._jobs.values())


    def _create_step(self, target: object) -> None:
        step_id = get_step_id(target)
        bridge = PipelineBridge(step_id, self)
        step = create_step(target, bridge)

        self._steps[step_id] = step

    def _get_step(self, target: object | StepId) -> AStepDefinition:
        tid = get_step_id(target)

        if tid not in self._steps:
            self._create_step(target)

        step = self._steps[tid]

        assert step is not None, "_create_step did not set _setup dict or used incorrect key"

        return step

    def _handle_exception(self) -> None:
        if self._state == PipelineState.ABORTED:
            return

        self._state = PipelineState.ABORTED

        for job in self._jobs.values():
            job.abort()

        for step in self._steps.values():
            step.abort()

    async def _run_loop(self, entry_point: EntryPointStep, *args: Any, **kwargs: Any) -> None:
        self._state = PipelineState.RUNNING

        with self._sub_tasks:
            entry_point.run(*args, **kwargs)

            try:
                await self._sub_tasks.all()

                if self._state == PipelineState.RUNNING:
                    self._state = PipelineState.COMPLETED

            except BaseException:
                self._state = PipelineState.ABORTED
                raise


    def run_job(self, job: AJob, on_complete: Callable[[AJob], None]) -> None:
        job_id = id(job)

        if self._state == PipelineState.ABORTED:
            job.abort()
        elif self._state != PipelineState.RUNNING:
            raise RuntimeError(f"Pipeline in invalid state: {self._state}")

        if job_id in self._jobs:
            raise RuntimeError(f"Job already spawned! For: {job.job_name}")

        self._jobs[id(job)] = job

        async def run_job() -> None:
            try:
                await job.run()
            except AbortException:
                pass
            except BaseException:
                self._handle_exception()
                raise
            finally:
                del self._jobs[job_id]
                on_complete(job)

        self._sub_tasks.add_task(run_job())

    def complete(self, step_id: StepId) -> None:
        step = self._get_step(step_id)

        connections = self._graph.get_connections_from(step)

        for connection in connections.values():
            is_all_complete = True

            for source_connection in self._graph.get_connections_to(connection.target).values():
                if source_connection.source.is_complete:
                    continue

                is_all_complete = False
                break

            if is_all_complete:
                connection.target.no_more_data()

    async def emit(self, step_id: StepId, target: Any, items: list) -> None:
        from_step = self._get_step(step_id)
        target_step = self._get_step(target)

        self._graph.create_connection(from_step, target_step)

        await target_step.digest(items)

    async def run(self, entry_point: object, *args: Any, **kwargs: Any) -> None:
        self._args      = args
        self._kwargs    = kwargs

        if self._state != PipelineState.IDLE:
            raise RuntimeError("Pipeline is not idle!")

        step = self._get_step(entry_point)

        if not isinstance(step, EntryPointStep):
            raise RuntimeError(f"Expecting {EntryPointStep.__name__}, got {type(step)}!")

        await self._run_loop(step, *args, **kwargs)

    def report(self) -> dict:
        return {
            'state': str(self._state),
            'steps': [step.report() for step in self._steps.values()],
        }


async def pipeline(entry_point: object, *args: Any, **kwargs: Any) -> None:
    await Pipeline().run(entry_point, *args, **kwargs)
