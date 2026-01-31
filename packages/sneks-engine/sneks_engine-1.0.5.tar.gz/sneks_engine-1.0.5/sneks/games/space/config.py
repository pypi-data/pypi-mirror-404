"""Configuration for space game mode."""

from dataclasses import dataclass, field

from sneks.engine.config.base import Config
from sneks.engine.config.graphics import GraphicsConfig, TailDecorationBehavior
from sneks.engine.config.snek import SnekConfig
from sneks.engine.config.world import WorldConfig
from sneks.engine.core.bearing import Bearing


@dataclass(frozen=True)
class SpaceSnekConfig(SnekConfig):
    """Snek config for space mode with higher speed limits."""

    idle_allowed: bool = True
    directional_speed_limit: int = 2
    combined_speed_limit: int = 4
    initial_bearing: Bearing = Bearing(0, 0)
    respawn: bool = True


@dataclass(frozen=True)
class SpaceGraphicsConfig(GraphicsConfig):
    """Graphics config for space mode with decorative tails and stars."""

    tail_decoration: TailDecorationBehavior = (
        TailDecorationBehavior.POSITION_AND_DECORATIVE
    )
    draw_stars: bool = True


@dataclass(frozen=True)
class SpaceWorldConfig(WorldConfig):
    """World config for space mode with asteroids."""

    asteroid_count: int = 20
    food_count: int = 0


@dataclass(frozen=True)
class SpaceConfig(Config):
    """Configuration for space game mode."""

    title: str = "Sneks in SPACE"
    snek: SpaceSnekConfig = field(default_factory=SpaceSnekConfig)
    graphics: SpaceGraphicsConfig = field(default_factory=SpaceGraphicsConfig)
    world: SpaceWorldConfig = field(default_factory=SpaceWorldConfig)
