"""Graphics configuration for display, recording, and rendering."""

from dataclasses import dataclass, field
from enum import IntFlag, auto

from sneks.engine.config.color import ColorConfig


class TailDecorationBehavior(IntFlag):
    """Flags controlling which cells are rendered for entity tails."""

    POSITION = auto()
    COLLIDING = auto()
    DECORATIVE = auto()
    POSITION_AND_COLLIDING = POSITION | COLLIDING
    POSITION_AND_COLLIDING_AND_DECORATIVE = POSITION_AND_COLLIDING | DECORATIVE
    POSITION_AND_DECORATIVE = POSITION | DECORATIVE


@dataclass(frozen=True)
class GraphicsConfig:
    """Configuration for rendering and recording."""

    display: bool = True
    headless: bool = False
    cell_size: int = 8
    padding: int = 1
    step_delay: int = 40
    step_keypress_wait: bool = False
    end_delay: int = 1000
    end_keypress_wait: bool = False
    record: bool = False
    record_prefix: str = "./output"
    record_fps: int = 12
    colors: ColorConfig = field(default_factory=ColorConfig)
    tail_decoration: TailDecorationBehavior = TailDecorationBehavior.POSITION
    draw_stars: bool = False
