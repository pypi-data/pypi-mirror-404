"""Space game mode with asteroids and multi-directional movement."""

import random
from typing import ClassVar, override

from sneks.engine import runner
from sneks.engine.core.bearing import Bearing
from sneks.engine.entity.static import StaticEntity
from sneks.engine.scoring import Criteria, NormalizedScore
from sneks.engine.world import World
from sneks.games.space.config import SpaceConfig


class Space(World):
    """Snek game with moving asteroids and respawning."""

    criteria: ClassVar[Criteria] = Criteria.CRASHES | Criteria.DISTANCE

    def __init__(self, config: SpaceConfig) -> None:
        super().__init__(config=config)

    @override
    def load_entities(self) -> None:
        super().load_entities()

        bearing_options = list(
            range(
                -SpaceConfig().snek.directional_speed_limit,
                SpaceConfig().snek.directional_speed_limit + 1,
            )
        )

        for _ in range(SpaceConfig().world.asteroid_count):
            up = random.choice(bearing_options)
            right = random.choice(bearing_options)
            if up == 0 and right == 0:
                # ensure all asteroids are moving
                increment = 1 if random.getrandbits(1) else -1
                if random.getrandbits(1):
                    up += increment
                else:
                    right += increment
            cluster = self.get_random_cluster(size=random.randint(3, 12))
            if not cluster:
                # Stop making asteroids if there's no longer room
                break
            self.register(
                StaticEntity(
                    name="Asteroid",
                    color=SpaceConfig().graphics.colors.asteroid,
                    initial_position=cluster,
                    initial_bearing=Bearing(right, up),
                ),
            )


def main(
    group_scores: bool = True, return_scores: bool = False
) -> list[NormalizedScore] | None:
    scores = runner.run(
        world=Space,
        config=SpaceConfig(),
        group_scores=group_scores,
    )
    if return_scores:
        return scores
    return None
