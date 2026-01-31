"""Base configuration dataclass for game settings."""

from dataclasses import dataclass, field

from sneks.engine.config.entity import EntityConfig
from sneks.engine.config.graphics import GraphicsConfig
from sneks.engine.config.snek import SnekConfig
from sneks.engine.config.world import WorldConfig
from sneks.engine.util import Singleton


@dataclass(frozen=True)
class Config(metaclass=Singleton):
    title: str = "Sneks"
    world: WorldConfig = field(default_factory=WorldConfig)
    entity: EntityConfig = field(default_factory=EntityConfig)
    snek: SnekConfig = field(default_factory=SnekConfig)
    graphics: GraphicsConfig = field(default_factory=GraphicsConfig)
    runs: int = 1
    turn_limit: int = 1000
    registrar_prefix: str = "src"
    registrar_submission_sneks: int = 1
    profile: bool = False
    debug: bool = True
