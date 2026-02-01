from pipeline_potato.core import StepId
from pipeline_potato.engine import AStepDefinition
from pipeline_potato.exceptions import PotatoException
from pipeline_potato.exceptions.circular_dependency_exception import CircularDependencyException
from pipeline_potato.graph.steps_connection import StepsConnection


class StepsGraph:
    def __init__(self) -> None:
        self._connections: dict[tuple, StepsConnection] = {}
        self._source_connections: dict[str | int, dict[str | int, StepsConnection]] = {}
        self._target_connections: dict[str | int, dict[str | int, StepsConnection]] = {}

    def _map_connections(
        self,
        connection: StepsConnection
    ) -> None:
        source_id = connection.source_id
        target_id = connection.target_id

        self._connections[connection.key()] = connection

        if source_id not in self._source_connections:
            self._source_connections[source_id] = {}

        self._source_connections[source_id][target_id] = connection

        if target_id not in self._target_connections:
            self._target_connections[target_id] = {}

        self._target_connections[target_id][source_id] = connection

    def _validate_no_circular_dependency(self, source: AStepDefinition, target: AStepDefinition) -> None:
        def find_cycle(current: StepId, path: list[str | int]) -> list[str | int] | None:
            if current in path:
                cycle_start = path.index(current)
                return path[cycle_start:] + [current]

            path.append(current)

            if current in self._source_connections:
                for next_step in self._source_connections[current]:
                    f_cycle = find_cycle(next_step, path[:])

                    if f_cycle is not None:
                        return f_cycle

            return None

        cycle = find_cycle(target.step_id, [source.step_id])

        if cycle is not None:
            raise CircularDependencyException(f"Circular dependency detected: {cycle}")

    def get_connection(self, source: AStepDefinition, target: AStepDefinition) -> StepsConnection | None:
        return self._connections.get((source.step_id, target.step_id))

    def require_connection(self, source: AStepDefinition, target: AStepDefinition) -> StepsConnection:
        connection = self._connections.get((source.step_id, target.step_id))

        if connection is None:
            raise PotatoException("Connection does not exist")

        return connection

    def get_connections_from(self, source: AStepDefinition) -> dict[str | int, StepsConnection]:
        return self._source_connections.get(source.step_id, {})

    def get_connections_to(self, target: AStepDefinition) -> dict[str | int, StepsConnection]:
        return self._target_connections.get(target.step_id, {})

    def has_connection(self, source: AStepDefinition, target: AStepDefinition) -> bool:
        return (source.step_id, target.step_id) in self._connections

    def create_connection(self, source: AStepDefinition, target: AStepDefinition) -> StepsConnection:
        if self.has_connection(source, target):
            return self.require_connection(source, target)

        self._validate_no_circular_dependency(source, target)

        connection = StepsConnection(source, target)

        self._map_connections(connection)

        return connection
