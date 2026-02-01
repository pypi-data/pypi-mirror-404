from enum import StrEnum


class JobState(StrEnum):
    IDLE    = 'idle'
    RUNNING = 'running'
    BLOCKED = 'blocked'
    ABORTED = 'aborted'
