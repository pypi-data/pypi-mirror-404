"""Classic snek game mode."""

from typing import ClassVar

from sneks.engine import runner
from sneks.engine.scoring import Criteria, NormalizedScore
from sneks.engine.world import World
from sneks.games.classic.config import ClassicConfig


class Classic(World):
    """Traditional snek game with food collection."""

    criteria: ClassVar[Criteria] = Criteria.AGE | Criteria.LENGTH

    def __init__(self, config: ClassicConfig) -> None:
        super().__init__(config=config)


def main(
    group_scores: bool = True, return_scores: bool = False
) -> list[NormalizedScore] | None:
    scores = runner.run(
        world=Classic,
        config=ClassicConfig(),
        group_scores=group_scores,
    )
    if return_scores:
        return scores
    return None
