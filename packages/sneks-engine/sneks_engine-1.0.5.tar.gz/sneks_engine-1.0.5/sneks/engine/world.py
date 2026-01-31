"""World base class managing the game loop, entities, and board state."""

import abc
import itertools
import logging
import random
from collections import Counter
from typing import ClassVar

from sneks.engine import registrar
from sneks.engine.config.base import Config
from sneks.engine.core.cell import Cell
from sneks.engine.core.direction import Direction
from sneks.engine.entity.base import Entity
from sneks.engine.entity.food import FoodEntity
from sneks.engine.entity.snek import SnekEntity
from sneks.engine.graphics import Graphics
from sneks.engine.scoring import Criteria, NormalizedScore, Score

logging.basicConfig(
    level=logging.INFO,
    format="{asctime} {levelname} {name}.{funcName}():{lineno} - {message}",
    style="{",
)
log = logging.getLogger(__name__)


class World(abc.ABC):
    """Responsible for maintaining the board and NPC entities."""

    cells: set[Cell]
    entities: list[Entity]
    config: Config
    graphics: Graphics
    halt_flag: bool = False
    steps: int = 0

    #: Worlds need to define their scoring criteria.
    criteria: ClassVar[Criteria] = Criteria(0)

    def __init__(self, config: Config) -> None:
        log.debug("begin")
        self.cells = {
            Cell(x, y)
            for x, y in itertools.product(
                range(config.world.columns), range(config.world.rows)
            )
        }
        self.entities = []
        self.config = config
        self.graphics = Graphics()

    def load_entities(self) -> None:
        sneks = registrar.get_submissions()
        sneks.sort(key=lambda s: s.name)
        color_index = 0
        color_index_delta = max(
            len(Config().graphics.colors.snek_options) // len(sneks), 1
        )
        for snek in sneks:
            starting_position = self.get_random_free_cell()
            if not starting_position:
                raise ValueError
            self.register(
                SnekEntity(
                    name=snek.name,
                    color=Config().graphics.colors.snek_options[color_index],
                    implementation=snek.snek,
                    initial_position=starting_position,
                    initial_bearing=Config().snek.initial_bearing,
                )
            )
            color_index = (color_index + color_index_delta) % len(
                Config().graphics.colors.snek_options
            )

        # Add initial food
        # Perform an optimization here for building the random free cells
        options = list(self.cells.difference(self.get_occupied_cells()))
        random.shuffle(options)
        for i in range(Config().world.food_count):
            if not options:
                break
            self.register(
                FoodEntity(
                    name="Food",
                    color=Config().graphics.colors.food,
                    initial_position=options.pop(),
                ),
            )
        log.debug("end")

    def register(self, entity: Entity) -> None:
        log.debug("begin")
        self.entities.append(entity)
        log.debug("end")

    def start(self) -> None:
        log.debug("begin")
        self.graphics.start()
        log.debug("end")

    def before_step(self) -> None:
        log.debug("begin")
        # Handle ended entities
        free_options = list(
            self.cells.difference(self.get_occupied_cells(include_food=True))
        )
        random.shuffle(free_options)
        for entity in self.entities:
            if not free_options:
                break
            if entity.ended:
                match entity:
                    case SnekEntity():
                        if Config().snek.respawn:
                            entity.ended = False
                            entity.reset(
                                initial_position=free_options.pop(),
                                initial_bearing=Config().snek.initial_bearing,
                            )
                    case FoodEntity():
                        entity.ended = False
                        entity.reset(
                            initial_position=free_options.pop(),
                            initial_bearing=None,
                        )
        # Set the state of the entity
        occupied = self.get_occupied_cells(include_food=False)
        food = self.get_food_cells()
        for entity in self.entities:
            entity.before_step(occupied=occupied, food=food)
        log.debug("end")

    def step(self) -> None:
        log.debug("begin")
        # Check the integrity of the engine
        if self.config is not Config():
            raise RuntimeError
        # Do the step
        for entity in self.entities:
            entity.step()
        log.debug("end")

    def after_step(self) -> None:
        log.debug("begin")
        # Evaluate consequences
        occupied = Counter()
        for entity in (e for e in self.entities if not isinstance(e, FoodEntity)):
            # need to count all the cells from an entity and the extra collision cells
            # first, update the position cells, ensuring duplicates are counted separately
            occupied.update(entity.position_cells)
            # next, update the collision cells, ensuring they're only counted at most once
            # from a particular entity
            collisions = (
                set(entity.head_colliding_cells) | set(entity.tail_colliding_cells)
            ) - set(entity.position_cells)
            occupied.update(collisions)
        for entity in self.entities:
            entity.after_step(occupied=occupied)
        self.graphics.paint(entities=self.entities)
        log.debug("end")

    def end(self) -> None:
        log.debug("begin")
        self.graphics.end()
        log.debug("end")

    def interrupt(self) -> None:
        log.debug("begin")
        self.halt_flag = True
        log.debug("end")

    def should_continue(self) -> bool:
        log.debug("begin")
        if self.halt_flag:
            return False
        if self.steps > Config().turn_limit:
            return False
        all_sneks_ended = all(
            s.ended for s in self.entities if isinstance(s, SnekEntity)
        )
        if not Config().snek.respawn and all_sneks_ended:
            return False
        return True

    def get_occupied_cells(self, include_food: bool = True) -> frozenset[Cell]:
        """Gets the set of occupied cells.

        This is determining a free cell to place a new entity, where
        food would be included in the set. It is also used for passing to the sneks
        when setting their state before a step, in which case food would be excluded.
        """
        return frozenset().union(
            *itertools.chain(
                entity.position_cells
                for entity in self.entities
                if include_food or not isinstance(entity, FoodEntity)
            )
        )

    def get_food_cells(self) -> frozenset[Cell]:
        return frozenset().union(
            *itertools.chain(
                entity.position_cells
                for entity in self.entities
                if isinstance(entity, FoodEntity)
            )
        )

    def get_random_free_cell(self) -> Cell | None:
        options = self.cells.difference(self.get_occupied_cells(include_food=True))
        if options:
            return random.choice(list(options))
        return None

    def get_random_cluster(self, size: int) -> list[Cell] | None:
        options = self.cells.difference(self.get_occupied_cells(include_food=True))
        if options:
            shuffled = list(options)
            random.shuffle(shuffled)
            for candidate in shuffled:
                attempts = 0
                potential = set()
                potential.add(candidate)

                while attempts < 100 and len(potential) < size:
                    attempts += 1
                    next_candidates = set()
                    for p in potential:
                        next_candidates.update(p.get_neighbor(d) for d in Direction)
                    next_candidates.intersection_update(options)
                    next_candidates.difference_update(potential)
                    if next_candidates:
                        shuffled_next_candidates = list(next_candidates)
                        random.shuffle(shuffled_next_candidates)
                        remaining_size = size - len(potential)
                        potential.update(shuffled_next_candidates[:remaining_size])

                if len(potential) == size:
                    return list(potential)
        return None

    def perform_step(self) -> None:
        self.before_step()
        self.step()
        self.after_step()
        self.steps += 1

    def run(self) -> None:
        if Config().profile:
            import cProfile
            import pstats

            pr = cProfile.Profile()
            pr.enable()

            self._run()

            pr.disable()
            stats = pstats.Stats(pr)
            stats.sort_stats("tottime").print_stats(20)
        else:
            self._run()

    def _run(self) -> None:
        log.debug("begin")
        self.load_entities()
        self.start()

        while self.should_continue():
            self.perform_step()

        self.end()
        log.debug("end")

    def score(self) -> list[NormalizedScore]:
        scores = []
        for entity in self.entities:
            if isinstance(entity, SnekEntity):
                scores.append(
                    Score(
                        name=entity.name,
                        age=entity.steps,
                        crashes=entity.count_ended,
                        length=entity.size,
                        distance=entity.distance,
                    )
                )
        min_score = Score(
            name="min",
            age=min(s.age for s in scores),
            crashes=max(s.crashes for s in scores),
            length=min(s.length for s in scores),
            distance=min(s.distance for s in scores),
        )
        max_score = Score(
            name="min",
            age=max(s.age for s in scores),
            crashes=min(s.crashes for s in scores),
            length=max(s.length for s in scores),
            distance=max(s.distance for s in scores),
        )
        return [s.normalize(min_score=min_score, max_score=max_score) for s in scores]
