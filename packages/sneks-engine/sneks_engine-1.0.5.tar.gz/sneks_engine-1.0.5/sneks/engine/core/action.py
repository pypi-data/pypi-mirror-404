"""Action primitives for snek movement."""

from enum import StrEnum, auto


class Action(StrEnum):
    """
    An enumeration to provide action values. The action represents how the snek
    should accelerate. The bearing of the snek is the current speed, and an action
    will be applied to the current bearing.
    """

    MAINTAIN = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
