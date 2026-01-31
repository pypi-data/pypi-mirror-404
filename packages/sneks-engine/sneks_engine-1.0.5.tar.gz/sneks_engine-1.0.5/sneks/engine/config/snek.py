"""Snek configuration for movement, vision, and respawn behavior."""

from dataclasses import dataclass

from sneks.engine.core.bearing import Bearing


@dataclass(frozen=True)
class SnekConfig:
    """Configuration for snek behavior and constraints."""

    vision_range: int = 20
    directional_speed_limit: int = 1
    combined_speed_limit: int = 1
    idle_allowed: bool = False
    initial_bearing: Bearing = Bearing(0, 1)
    respawn: bool = False
