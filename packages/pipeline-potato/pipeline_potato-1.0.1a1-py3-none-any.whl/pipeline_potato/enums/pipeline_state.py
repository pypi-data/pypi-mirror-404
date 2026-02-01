from enum import StrEnum


class PipelineState(StrEnum):

    IDLE        = 'idle'
    RUNNING     = 'running'
    COMPLETED   = 'completed'
    ABORTED     = 'aborted'
