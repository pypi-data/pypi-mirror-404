"""Asteroid entity for the space game mode."""

from dataclasses import dataclass

from sneks.engine.entity.static import StaticEntity


@dataclass(kw_only=True)
class Asteroid(StaticEntity):
    pass
