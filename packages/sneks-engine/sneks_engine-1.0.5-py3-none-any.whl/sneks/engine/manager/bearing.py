"""BearingManager for mutable bearing state and velocity calculations."""

from collections.abc import Generator
from dataclasses import dataclass

from sneks.engine.config.base import Config
from sneks.engine.core.action import Action
from sneks.engine.core.bearing import Bearing
from sneks.engine.core.cell import Cell
from sneks.engine.core.direction import Direction


@dataclass
class BearingManager:
    """Manager for controlling the state of a bearing."""

    x: int = 0
    y: int = 0

    def get_bearing(self) -> Bearing:
        return Bearing(x=self.x, y=self.y)

    def update(self, bearing: Bearing) -> None:
        self.x = bearing.x
        self.y = bearing.y

    def apply(self, action: Action) -> None:
        """Apply the action to the bearing."""
        match action:
            case Action.UP:
                self.y = min(Config().snek.directional_speed_limit, self.y + 1)
            case Action.RIGHT:
                self.x = min(Config().snek.directional_speed_limit, self.x + 1)
            case Action.DOWN:
                self.y = max(-Config().snek.directional_speed_limit, self.y - 1)
            case Action.LEFT:
                self.x = max(-Config().snek.directional_speed_limit, self.x - 1)
        # Adjust the bearing based on the absolute speed limit
        while abs(self.x) + abs(self.y) > Config().snek.combined_speed_limit:
            # Remove from the vector not in the latest action
            # In theory, this should only remove a single unit per call,
            # so we're okay with ignoring the edge cases. If they get hit,
            # it's an indication of a configuration problem with the game
            match action:
                case Action.UP | Action.DOWN:
                    if self.x > 0:
                        self.x -= 1
                    elif self.x < 0:
                        self.x += 1
                    else:
                        break
                case Action.LEFT | Action.RIGHT:
                    if self.y > 0:
                        self.y -= 1
                    elif self.y < 0:
                        self.y += 1
                    else:
                        break
                case _:
                    break

    def get_distance(self) -> float:
        return Cell(0, 0).get_distance(Cell(self.x, self.y))

    def get_direction_components(self) -> Generator[Direction, None, None]:
        """
        Orders the directional components to make a path for the velocity
        """

        options = []
        if self.y > 0:
            options.append(Direction.UP)
        elif self.y < 0:
            options.append(Direction.DOWN)
        if self.x > 0:
            options.append(Direction.RIGHT)
        elif self.x < 0:
            options.append(Direction.LEFT)

        origin = Cell(0, 0)
        target = Cell(self.x, self.y)
        while origin != target:
            component = min(
                options,
                key=lambda direction: origin.get_neighbor(direction).get_distance(
                    target
                ),
            )
            origin = origin.get_neighbor(component)
            yield component
