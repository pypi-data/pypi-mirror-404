"""Base Snek class that submissions extend to implement behavior."""

import abc
from collections.abc import Sequence

from sneks.engine.config.base import Config
from sneks.engine.core.action import Action
from sneks.engine.core.bearing import Bearing
from sneks.engine.core.cell import Cell
from sneks.engine.core.direction import Direction


class Snek(abc.ABC):
    """
    Base snek from which submission sneks derive. This snek has no behavior,
    but derivations should implement ``get_next_action()`` to provide it.
    """

    #: Head snek represented as Cell
    head: Cell = Cell(0, 0)
    #: Body of the snek represented as a list of cells, with index 0 being the head
    body: list[Cell] = []
    #: Bearing of the snek
    bearing: Bearing = Bearing(0, 0)
    #: Set of currently occupied cells on the game board that the snek can see
    occupied: frozenset[Cell] = frozenset()
    #: Set of cells that contain food on the game board
    food: frozenset[Cell] = frozenset()

    @abc.abstractmethod
    def get_next_action(self) -> Action:
        """
        Method that determines which action the snek should take next.

        :return: the next action for the snek to take
        """
        raise NotImplementedError

    def get_head(self) -> Cell:
        """
        Helper method to return the head of the snek.

        :return: the cell representing the head of the snek
        """
        return self.head

    def get_body(self) -> list[Cell]:
        """
        Helper method to return the snek's body.

        :return: the list of cells making up the snek, including the head
        """
        return self.body

    def get_bearing(self) -> Bearing:
        """
        Helper method to return the bearing of the snek.

        :return: the bearing representing the directional speeds of the snek
        """
        return self.bearing

    def get_occupied(self) -> frozenset[Cell]:
        """
        Helper method to return all occupied cells that the snek can see.
        This includes both your snek's position, all other sneks'
        positions, and space occupied by asteroids.

        This can be used in your ``get_next_action()`` to check if a cell
        you are planning on moving to is already taken. Example::

            potential_next_cell = self.get_head().get_up()
            if potential_next_cell in self.get_occupied():
                # potential_next_cell is already taken
            else:
                # potential_next_cell is free

        :return: the set of occupied cells on the game board
        """
        return self.occupied

    def get_food(self) -> frozenset[Cell]:
        """
        Helper method to return the current food on the board.

        :return: the set of food on the game board
        """
        return self.food

    def get_closest_food(self) -> Cell:
        """
        Get the closest food to the head of the snek from the current set.

        :return: the Cell representing the location of the nearest food
        """
        return min(self.get_food(), key=lambda food: food.get_distance(self.get_head()))

    def look(self, direction: Direction) -> int:
        """
        Look in a direction from the snek's head and get the distance to the closest obstacle.
        An obstacle could either be an occupied cell or the game board's border.

        >>> self.get_head()
        Cell(0, 0)
        >>> self.look(Direction.LEFT)
        0

        :param direction: the direction to look
        :return: the distance until the closest obstacle in the specified direction
        """

        current = self.get_head().get_neighbor(direction)
        current_distance = 1

        while (
            current not in self.get_occupied()
            and current_distance <= Config().snek.vision_range
        ):
            current = current.get_neighbor(direction)
            current_distance += 1

        return current_distance - 1

    def get_direction_to_destination(
        self,
        destination: Cell,
        directions: Sequence[Direction] = (
            Direction.UP,
            Direction.DOWN,
            Direction.LEFT,
            Direction.RIGHT,
        ),
    ) -> Direction:
        """
        Get the next direction to travel in order to reach the destination
        from a set of specified directions (default: all directions).

        When multiple directions have the same resulting distance, the chosen
        direction is determined by the order provided, with directions coming
        first having precedence.

        For example, to get the direction the snek should travel to close the
        most distance between itself and a cell 5 columns and 9 rows away,
        this method could be used like::

            self.get_direction_to_destination(Cell(5, 9))

        :param destination: the cell to travel towards
        :param directions: the directions to evaluate in order
        :return: the direction to travel that will close the most distance
        """

        return min(
            directions,
            key=lambda direction: self.get_head()
            .get_neighbor(direction)
            .get_distance(destination),
        )
