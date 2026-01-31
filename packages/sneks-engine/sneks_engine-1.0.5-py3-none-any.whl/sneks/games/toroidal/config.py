"""Configuration for toroidal game mode."""

from dataclasses import dataclass, field

from sneks.engine.config.base import Config
from sneks.engine.config.world import WorldConfig


@dataclass(frozen=True)
class ToroidalWorldConfig(WorldConfig):
    """World config for toroidal mode without food."""

    food_count: int = 0


@dataclass(frozen=True)
class ToroidalConfig(Config):
    """Configuration for toroidal game mode."""

    title: str = "Sneks on a Toroidal Plane"
    world: ToroidalWorldConfig = field(default_factory=ToroidalWorldConfig)
    turn_limit: int = 10000
