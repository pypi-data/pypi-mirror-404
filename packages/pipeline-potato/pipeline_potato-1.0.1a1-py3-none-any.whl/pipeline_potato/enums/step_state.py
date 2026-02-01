from enum import StrEnum


class StepState(StrEnum):

    ACTIVE      = 'active'
    COMPLETED   = 'completed'
    ABORTED     = 'aborted'
