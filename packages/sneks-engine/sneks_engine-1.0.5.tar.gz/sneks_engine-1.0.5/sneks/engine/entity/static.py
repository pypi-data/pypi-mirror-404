"""StaticEntity for entities that maintain their shape."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from sneks.engine.core.action import Action
from sneks.engine.core.bearing import Bearing
from sneks.engine.core.cell import Cell
from sneks.engine.entity.base import Entity
from sneks.engine.manager.cell import CellManager


@dataclass(kw_only=True)
class StaticEntity(Entity):
    """An entity whose shape stays the same."""

    position_set: set[Cell] = field(init=False)
    collision_set: set[Cell] = field(default_factory=set, init=False)

    @override
    def reset(
        self, initial_position: Cell | Sequence[Cell], initial_bearing: Bearing | None
    ) -> None:
        super().reset(
            initial_position=initial_position, initial_bearing=initial_bearing
        )

        self.position_set = set(self.position_cells)

    @override
    def get_next_action(self) -> Action:
        return Action.MAINTAIN

    @override
    def step(self, idle_allowed: bool = True) -> None:
        """Default behavior for static entities.

        The default is to have the collision box trail behind the position
        based on the speed at which the entity is traveling.

        The decorative cells will contain a history of where the other cells
        have traveled previously. How they're rendered is delegated to the
        graphics configuration.
        """

        components = list(self.bearing_manager.get_direction_components())

        # Check if there's no movement, and shortcut the rest
        if len(components) == 0:
            self.tail_colliding_cells.clear()
            return

        # Set an index for the collision cells and position cells
        # If the speed is 1, we ignore the collision cells
        stop_index = 0
        if len(components) > 1:
            stop_index = -1

        # Add the new positions and collisions for each cell's path
        new_positions = set()
        new_collisions = set()
        for cell in self.position_cells:
            previous = cell
            # add new collisions
            for direction in components[:stop_index]:
                next_cell = CellManager.get_absolute_neighbor(previous, direction)
                new_collisions.add(next_cell)
                previous = next_cell
            # add new positions
            for direction in components[stop_index:]:
                next_cell = CellManager.get_absolute_neighbor(previous, direction)
                new_positions.add(next_cell)
                previous = next_cell

        new_collisions -= new_positions

        self.position_cells.clear()
        self.position_cells.extend(new_positions)
        self.tail_colliding_cells.clear()
        self.tail_colliding_cells.extend(new_collisions)
