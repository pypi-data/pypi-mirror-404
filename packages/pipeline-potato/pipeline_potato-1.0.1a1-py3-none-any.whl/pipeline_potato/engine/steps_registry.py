from pipeline_potato.core import StepId, get_step_id
from pipeline_potato.engine.a_step_definition import AStepDefinition


class StepsRegistry:
    def __init__(self):
        self._steps: dict[int | str, AStepDefinition] = {}

    def __getitem__(self, step_item: object | StepId) -> AStepDefinition | None:
        step_id = get_step_id(step_item)

        return self._steps[step_id] if step_id in self._steps else None

    def __setitem__(self, step_item: object | StepId, step: AStepDefinition) -> None:
        step_id = get_step_id(step_item)

        if step_id in self._steps:
            raise RuntimeError(f"Step {step_id} already registered")

        if step.step_id != step_id:
            raise RuntimeError(f"Step id {step_id} and definition step id {step.step_id} do not match")

        self._steps[step_id] = step

    def __contains__(self, step_item: object | StepId) -> bool:
        return get_step_id(step_item) in self._steps

    def __len__(self) -> int:
        return len(self._steps)

    def __iter__(self):
        return iter(self._steps)

    def values(self):
        return self._steps.values()

    def items(self):
        return self._steps.items()

    def add(self, step: AStepDefinition) -> None:
        self[step.step_id] = step
