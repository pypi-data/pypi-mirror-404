from typing import Any, Callable

from pipeline_potato.core import APipeline, StepId
from pipeline_potato.engine.a_step_definition import AStepDefinition

TStepBuilder = Callable[[APipeline], AStepDefinition]


def _as_step_name(step_id: StepId | object) -> str:
    if isinstance(step_id, (str, int)):
        return str(step_id)
    if hasattr(step_id, "__name__"):
        return step_id.__name__  # pyright: ignore[reportAttributeAccessIssue]
    if hasattr(step_id, "__class__"):
        return step_id.__class__.__name__

    raise TypeError("Invalid step id type")


class StepsDefinitionRegistry:
    _instance = None


    def __new__(cls, *args: Any, **kwargs: Any):
        if cls._instance is None:
            cls._instance = super(StepsDefinitionRegistry, cls).__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._builders      : dict[int | str, TStepBuilder] = {}
        self._initialized   : bool                          = True

    def __len__(self) -> int:
        return len(self._builders)


    def register(self, step_item: object, builder: TStepBuilder) -> None:
        sid = id(step_item)

        if sid in self._builders:
            raise RuntimeError(f"Builder for step {_as_step_name(step_item)} already registered")

        self._builders[sid] = builder

    def create_step(self, step_item: object, pipeline: APipeline) -> AStepDefinition:
        sid = id(step_item)
        step_name = _as_step_name(step_item)

        builder = self._builders.get(sid)

        if not builder:
            raise RuntimeError(f"No builder registered for step {step_name}")

        step = builder(pipeline)

        if step.step_id != sid:
            raise RuntimeError(f"Step ID mismatch: expected {sid}, got {step.step_id} ({step_name})")

        return step


def register_step(step_item: object, builder: TStepBuilder) -> None:
    StepsDefinitionRegistry().register(step_item, builder)

def create_step(step_item: object, pipeline: APipeline) -> AStepDefinition:
    return StepsDefinitionRegistry().create_step(step_item, pipeline)


__all__ = [
    "TStepBuilder",
    "register_step",
    "create_step",
    "StepsDefinitionRegistry"
]
