"""SnekEntity wrapping a Snek submission for the game world."""

import itertools
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field

from typing_extensions import override

from sneks.engine.config.base import Config
from sneks.engine.core.action import Action
from sneks.engine.core.bearing import Bearing
from sneks.engine.core.cell import Cell
from sneks.engine.core.snek import Snek
from sneks.engine.entity.dynamic import DynamicEntity
from sneks.engine.manager.cell import CellManager
from sneks.engine.util import SwallowOutput


@dataclass(kw_only=True)
class SnekEntity(DynamicEntity):
    """Entity that manages the state of a Snek."""

    implementation: type[Snek]
    instance: Snek = field(init=False)
    current_food: frozenset[Cell] = field(init=False)

    @override
    def reset(
        self, initial_position: Cell | Sequence[Cell], initial_bearing: Bearing | None
    ) -> None:
        self.instance = self.implementation()
        super().reset(
            initial_position=initial_position, initial_bearing=initial_bearing
        )

    @override
    def before_step(self, occupied: frozenset[Cell], food: frozenset[Cell]) -> None:
        super().before_step(occupied=occupied, food=food)

        self.current_food = food

        if not self.ended:
            # set the state of the instance
            self.instance.bearing = self.bearing_manager.get_bearing()

            # build a grid around the head based on the vision range
            grid = {
                Cell(x, y)
                for x, y in itertools.product(
                    range(
                        self.head.x - Config().snek.vision_range,
                        self.head.x + Config().snek.vision_range,
                    ),
                    range(
                        self.head.y - Config().snek.vision_range,
                        self.head.y + Config().snek.vision_range,
                    ),
                )
            }

            # The sneks can only see obstacles within the vision range
            self.instance.occupied = frozenset(
                CellManager.get_relative_to(cell, self.head)
                for cell in grid.intersection(occupied)
                if cell.get_distance(self.head) < Config().snek.vision_range
            )

            # The snek can always know the locations of all the food
            self.instance.food = frozenset(
                CellManager.get_relative_to(cell, self.head) for cell in food
            )

            self.instance.body = list(
                CellManager.get_relative_to(cell, self.head)
                for cell in self.position_cells
            )

    @override
    def step(self, idle_allowed=True) -> None:
        super().step(idle_allowed=Config().snek.idle_allowed)

    @override
    def get_next_action(self) -> Action:
        with SwallowOutput(debug=Config().debug):
            next_action = self.instance.get_next_action()
        return next_action

    @override
    def after_step(self, occupied: Counter[Cell]) -> None:
        # check if snek should be ended
        if not self.ended:
            for cell in itertools.chain((self.head,), self.head_colliding_cells):
                if occupied[cell] > 1:
                    self.ended = True
                    self.ended_this_step = True
                    self.bearing_manager.update(Bearing(0, 0))
                    break
                if cell in self.current_food:
                    self.size += 1
        super().after_step(occupied=occupied)
