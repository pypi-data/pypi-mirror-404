"""Toroidal game mode with infinite growth."""

from typing import ClassVar, override

from sneks.engine import runner
from sneks.engine.entity.snek import SnekEntity
from sneks.engine.scoring import Criteria, NormalizedScore
from sneks.engine.world import World
from sneks.games.toroidal.config import ToroidalConfig


class Toroidal(World):
    """Snek game where sneks grow every step without food."""

    criteria: ClassVar[Criteria] = Criteria.AGE

    def __init__(self, config: ToroidalConfig) -> None:
        super().__init__(config=config)

    @override
    def after_step(self) -> None:
        for entity in self.entities:
            if isinstance(entity, SnekEntity) and not entity.ended:
                entity.size += 1

        super().after_step()


def main(
    group_scores: bool = True, return_scores: bool = False
) -> list[NormalizedScore] | None:
    scores = runner.run(
        world=Toroidal,
        config=ToroidalConfig(),
        group_scores=group_scores,
    )
    if return_scores:
        return scores
    return None
