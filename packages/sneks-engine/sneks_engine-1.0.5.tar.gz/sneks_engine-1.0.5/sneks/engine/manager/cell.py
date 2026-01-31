"""CellManager for coordinate transformations on the toroidal board."""

import math
from functools import cache

from sneks.engine.config.base import Config
from sneks.engine.core.cell import Cell
from sneks.engine.core.direction import Direction


class CellManager:
    """Utility class for cell coordinate operations."""

    @classmethod
    @cache
    def get_absolute_neighbor(cls, cell: Cell, direction: Direction) -> Cell:
        if direction is Direction.UP:
            return cls.get_absolute_by_offset(cell=cell, y_offset=1)
        elif direction is Direction.DOWN:
            return cls.get_absolute_by_offset(cell=cell, y_offset=-1)
        elif direction is Direction.LEFT:
            return cls.get_absolute_by_offset(cell=cell, x_offset=-1)
        elif direction is Direction.RIGHT:
            return cls.get_absolute_by_offset(cell=cell, x_offset=1)
        else:
            raise ValueError("direction not valid")

    @staticmethod
    @cache
    def get_absolute_by_offset(
        *, cell: Cell, x_offset: int = 0, y_offset: int = 0
    ) -> Cell:
        return Cell(
            (cell.x + x_offset) % Config().world.columns,
            (cell.y + y_offset) % Config().world.rows,
        )

    @staticmethod
    @cache
    def get_relative_to(
        cell: Cell, other: Cell, minimize_coordinates: bool = True
    ) -> Cell:
        """
        Returns the relative cell in relation to "other". Other is likely the head when this is called,
        since that's what the coordinates are referenced on for the snek implementation.

        minimize_coordinates is used only for testing the logic
        """
        relative_x = int(math.fmod((cell.x - other.x), Config().world.columns))
        relative_y = int(math.fmod((cell.y - other.y), Config().world.rows))
        if minimize_coordinates:
            if relative_x > Config().world.columns / 2:
                relative_x -= Config().world.columns
            elif relative_x < -Config().world.columns / 2:
                relative_x += Config().world.columns
            if relative_y > Config().world.rows / 2:
                relative_y -= Config().world.rows
            elif relative_y < -Config().world.rows / 2:
                relative_y += Config().world.rows
        return Cell(relative_x, relative_y)
