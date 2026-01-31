"""Base Entity class for all game objects."""

import abc
from collections import Counter, deque
from collections.abc import Sequence
from dataclasses import InitVar, dataclass, field

from sneks.engine.core.action import Action
from sneks.engine.core.bearing import Bearing
from sneks.engine.core.cell import Cell
from sneks.engine.manager.bearing import BearingManager


@dataclass(kw_only=True)
class Entity(abc.ABC):
    """An entity that exists in the world."""

    name: str
    color: tuple[int, int, int]
    size: int = field(init=False)
    distance: float = field(default=0.0, init=False)
    steps: int = field(default=0, init=False)
    ended: bool = False
    ended_this_step: bool = False
    count_ended: int = field(default=0, init=False)
    position_cells: deque[Cell] = field(default_factory=deque, init=False)
    head_colliding_cells: deque[Cell] = field(default_factory=deque, init=False)
    tail_colliding_cells: deque[Cell] = field(default_factory=deque, init=False)
    decorative_cells: deque[Cell] = field(default_factory=deque, init=False)
    bearing_manager: BearingManager = field(default_factory=BearingManager)

    initial_position: InitVar[Cell | Sequence[Cell]]
    initial_bearing: InitVar[Bearing | None] = None

    def __post_init__(
        self, initial_position: Cell | Sequence[Cell], initial_bearing: Bearing | None
    ) -> None:
        self.reset(initial_position=initial_position, initial_bearing=initial_bearing)

    def reset(
        self, initial_position: Cell | Sequence[Cell], initial_bearing: Bearing | None
    ) -> None:
        self.position_cells.clear()
        self.head_colliding_cells.clear()
        self.tail_colliding_cells.clear()
        self.decorative_cells.clear()
        # initialize position
        match initial_position:
            case Cell():
                self.position_cells.append(initial_position)
            case _:
                if len(initial_position) < 1:
                    raise ValueError
                for cell in initial_position:
                    self.position_cells.append(cell)

        # initialize bearing
        if initial_bearing is not None:
            self.bearing_manager.x = initial_bearing.x
            self.bearing_manager.y = initial_bearing.y

        # initialize size
        self.size = len(self.position_cells)

    @abc.abstractmethod
    def get_next_action(self) -> Action:
        raise NotImplementedError

    def before_step(self, occupied: frozenset[Cell], food: frozenset[Cell]) -> None:
        if self.ended_this_step:
            self.count_ended += 1
        self.ended_this_step = False

    def step(self, idle_allowed=True) -> None:
        if not self.ended:
            # adjust bearing based on next action
            next_action = self.get_next_action()
            self.bearing_manager.apply(action=next_action)

            # Ensure the entity follows idle configuration
            if not idle_allowed:
                if not list(self.bearing_manager.get_direction_components()):
                    # This means the action stopped the entity, so we apply it again
                    self.bearing_manager.apply(action=next_action)

    def after_step(self, occupied: Counter[Cell]) -> None:
        if not self.ended:
            self.distance += self.bearing_manager.get_distance()
            self.steps += 1
