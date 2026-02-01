import enum


class ExecutionMode(enum.IntEnum):
    """The execution mode of the command."""

    PARALLEL = 0
    """Commands will be executed in parallel."""

    QUEUED = 2
    """Commands will be executed sequentially by queueing them."""

    SINGLE = 1
    """Commands can only be executed one at a time."""
