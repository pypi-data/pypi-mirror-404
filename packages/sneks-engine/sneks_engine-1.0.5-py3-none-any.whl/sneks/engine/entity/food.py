"""FoodEntity that sneks consume to grow."""

from collections import Counter
from dataclasses import dataclass
from typing import override

from sneks.engine.core.cell import Cell
from sneks.engine.entity.static import StaticEntity


@dataclass(kw_only=True)
class FoodEntity(StaticEntity):
    """A non-colliding entity that can trigger snek changes."""

    @override
    def after_step(self, occupied: Counter[Cell]) -> None:
        for cell in self.position_cells:
            if cell in occupied:
                self.ended = True
