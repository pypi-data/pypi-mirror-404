import asyncio
from asyncio import Task
from typing import Awaitable

from pipeline_potato.exceptions import ActionOutOfContextException


class TasksWaiter:
    def __init__(self):
        self._is_complete   : bool          = False
        self._is_awaited    : bool          = False
        self._tasks_count   : int           = 0
        self._total_tasks   : int           = 0
        self._tasks         : list[Task]    = []
        self._in_context    : bool          = False

    def __enter__(self) -> None:
        self._in_context = True

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None
    ) -> None:
        self._in_context = False

        if self._tasks and not self._is_awaited:
            raise RuntimeError("TasksAwaiter never awaited!")

    @property
    def in_flight_tasks(self) -> int:
        return self._tasks_count

    @property
    def is_complete(self) -> bool:
        return self._is_complete

    @property
    def total_tasks(self) -> int:
        return self._total_tasks


    def _handle_task_complete(self) -> None:
        self._tasks_count -= 1

        if self._tasks_count == 0:
            self._is_complete = True
        elif self._tasks_count < 0:
            raise RuntimeError(f"Tasks count {self._tasks_count} is negative")


    def add_task(self, task: Awaitable[None]) -> None:
        if not self._in_context:
            raise ActionOutOfContextException()
        if self._is_complete:
            raise ActionOutOfContextException()

        self._tasks_count += 1
        self._total_tasks += 1

        async def _task_wrapper() -> None:
            try:
                await task
            finally:
                self._handle_task_complete()

        self._tasks.append(asyncio.create_task(_task_wrapper()))

    async def all(self) -> None:
        """
        Wait for all tasks to complete.

        This method will also throw an exception if any tasks failed.
        """
        if self._is_awaited:
            raise RuntimeError("Tasks queue was already awaited")

        self._is_awaited = True

        if not self._tasks:
            self._is_complete = True
            return

        while self._tasks:
            task = self._tasks.pop()
            await task

        if not self._is_complete:
            raise RuntimeError("Tasks in flight is zero, but queue not marked as complete!")
