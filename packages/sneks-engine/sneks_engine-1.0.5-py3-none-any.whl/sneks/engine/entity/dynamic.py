"""DynamicEntity for entities that move and change shape."""

from abc import ABC
from dataclasses import dataclass

from typing_extensions import override

from sneks.engine.core.cell import Cell
from sneks.engine.entity.base import Entity
from sneks.engine.manager.cell import CellManager


@dataclass(kw_only=True)
class DynamicEntity(Entity, ABC):
    """An entity whose shape changes."""

    @property
    def head(self) -> Cell:
        return self.position_cells[0]

    @override
    def step(self, idle_allowed: bool = True) -> None:
        """Default behavior for dynamic entities.

        The default is to have the collision box trail behind the head
        based on the speed at which the entity is traveling. This is to prevent
        the snek from phasing through other entities at higher speeds.

        The decorative cells will contain a history of where the position cells
        have traveled previously. How they're rendered is delegated to the
        graphics configuration.
        """

        # we need to track the colliding cells from the head separate from the tail
        # because we'll use the head colliding cells to tell if this entity has
        # collided into another entity, and the tail colliding cells to determine
        # what is able to be collided into

        # defer to super to adjust bearing
        super().step(idle_allowed=idle_allowed)

        # update the cells
        components = self.bearing_manager.get_direction_components()
        component_count = 0
        for direction in components:
            component_count += 1
            next_head = CellManager.get_absolute_neighbor(self.head, direction)
            self.position_cells.appendleft(next_head)
            self.head_colliding_cells.appendleft(next_head)

        # trim the position cells to the size, appending to decorative and tail colliding
        while len(self.position_cells) > self.size:
            cell = self.position_cells.pop()
            self.tail_colliding_cells.appendleft(cell)
            self.decorative_cells.appendleft(cell)

        # trim the colliding cells to the speed
        while len(self.head_colliding_cells) > max(0, component_count - 1):
            self.head_colliding_cells.pop()
            if self.tail_colliding_cells:
                self.tail_colliding_cells.pop()

        # trim the decorative cells based on a factor of size * speed
        while len(self.decorative_cells) > 3 * self.size * component_count:
            self.decorative_cells.pop()

        # example movement
        # moving left at speed 2
        # - - - - - x
        # - - - x + -
        # - x + - - -
        # or size bigger
        # - - - - - X x x
        # - - - X x x + -
        # - X x x + - - -
