"""World configuration for board dimensions and food count."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldConfig:
    """Configuration for the game world."""

    rows: int = 60
    columns: int = 90
    food_count: int = 40
