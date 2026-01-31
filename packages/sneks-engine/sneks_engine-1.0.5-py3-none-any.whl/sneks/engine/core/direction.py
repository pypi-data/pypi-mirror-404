"""Direction primitive for cardinal directions."""

from enum import StrEnum, auto

from sneks.engine.core.action import Action


class Direction(StrEnum):
    """
    An enumeration to provide directional values
    """

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

    def get_opposite(self) -> "Direction":
        """
        Gets the opposite direction of this direction

        :return: the opposite direction
        """

        if self == Direction.UP:
            return Direction.DOWN
        elif self == Direction.DOWN:
            return Direction.UP
        elif self == Direction.LEFT:
            return Direction.RIGHT
        else:
            return Direction.LEFT

    def get_action(self) -> Action:
        """
        Gets the corresponding action for the direction

        :return: the action that corresponds to the direction
        """

        return Action(self.value)
