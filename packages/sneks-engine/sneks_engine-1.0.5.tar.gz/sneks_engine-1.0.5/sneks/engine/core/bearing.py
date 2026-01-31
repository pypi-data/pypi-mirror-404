"""Bearing primitive representing velocity in cells per step."""

from dataclasses import dataclass
from functools import cache, cached_property


@dataclass(frozen=True)
class Bearing:
    """
    Represents the directional speeds of a snek. The speeds are represented
    as integers to show the vertical and horizontal speeds in cells per
    game step.

    Sneks start with a bearing of ``(0, 0)``. For example, if the action from
    ``get_next_action()`` is ``Action.UP``, the snek will increase the speed vertically
    by one, so on the next game step the bearing will be ``(0, 1)``, and the snek will
    have moved one cell.
    """

    x: int  #:
    y: int  #:

    @cache  # type: ignore
    def __new__(cls, x: int, y: int) -> "Bearing":
        return super().__new__(cls)

    def __getnewargs__(self):
        return self.x, self.y

    @cached_property
    def _hash(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self._hash == other._hash

    def __hash__(self):
        return self._hash
