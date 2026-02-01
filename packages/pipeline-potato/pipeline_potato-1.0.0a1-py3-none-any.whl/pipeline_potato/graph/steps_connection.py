from pipeline_potato.core import StepId
from pipeline_potato.engine import AStepDefinition


class StepsConnection:
    def __init__(self, source: AStepDefinition, target: AStepDefinition):
        self._source        : AStepDefinition = source
        self._target        : AStepDefinition = target
        self._is_complete   : bool  = False
        self._items_count   : int   = 0

    def __repr__(self):
        return f'StepsConnection(source={self._source}, target={self._target})'

    @property
    def source(self) -> AStepDefinition:
        return self._source

    @property
    def target(self) -> AStepDefinition:
        return self._target

    @property
    def source_id(self) -> StepId:
        return self._source.step_id

    @property
    def target_id(self) -> StepId:
        return self._target.step_id

    @property
    def items_count(self) -> int:
        return self._items_count

    @property
    def is_complete(self) -> bool:
        return self._is_complete


    def key(self) -> tuple[StepId, StepId]:
        return (self._source.step_id, self._target.step_id, )

    def increase_items_count(self, by: int) -> None:
        self._items_count += by

    def complete(self) -> None:
        self._is_complete = True
