# Sneks Engine

A Python game engine for creating snake-like games with customizable rules, graphics, and AI submissions.

## Architecture

```
src/sneks/
├── engine/           # Core engine components
│   ├── core/         # Primitives: Cell, Bearing, Direction, Action
│   ├── entity/       # Game entities: Snek, Food, Static/Dynamic
│   ├── config/       # Configuration dataclasses
│   ├── manager/      # Cell and bearing calculations
│   ├── validator/    # Submission validation tests
│   ├── world.py      # Base World class (game loop)
│   ├── graphics.py   # Pygame rendering
│   ├── recorder.py   # Frame capture and video encoding
│   ├── runner.py     # Game execution and scoring
│   └── scoring.py    # Score normalization
└── games/            # Game variants
    ├── classic/      # Traditional snek
    ├── space/        # Asteroids + snek
    ├── toroidal/     # Infinite growth mode
    └── example/      # Example submission
```

### Key Components

- **World**: Manages the game loop, entities, and board state. Subclass this to create new game modes.
- **Entity**: Base class for all game objects. `DynamicEntity` moves and grows; `StaticEntity` maintains shape.
- **Snek**: The AI interface that submissions implement. Receives game state and returns an `Action`.
- **Config**: Singleton configuration system. Each game mode extends `Config` with custom settings.

## Creating a New Game Mode

1. Create a config class extending `Config`:

```python
from dataclasses import dataclass
from sneks.engine.config.base import Config


@dataclass(frozen=True)
class MyGameConfig(Config):
    title: str = "My Game"
    turn_limit: int = 5000
```

2. Create a world class extending `World`:

```python
from sneks.engine.world import World
from sneks.engine.scoring import Criteria


class MyGame(World):
    criteria = Criteria.AGE | Criteria.LENGTH  # Scoring criteria

    def __init__(self, config: MyGameConfig) -> None:
        super().__init__(config=config)

    # Override hooks as needed:
    # - load_entities(): Add custom entities
    # - before_step(): Pre-step logic
    # - after_step(): Post-step logic (collisions, growth)
```

## Core Concepts

### Bearing vs Direction vs Action

The engine uses a velocity-based movement model:

- **Bearing**: Current velocity as `Bearing(x, y)` — cells moved per tick in each axis. A snek at `Bearing(2, -1)` moves 2 cells right and 1 cell down each tick.
- **Direction**: Cardinal directions (`UP`, `DOWN`, `LEFT`, `RIGHT`) used for querying neighbors and obstacles.
- **Action**: Acceleration input returned by `get_next_action()`. Actions modify the bearing — `Action.UP` increments `bearing.y` by 1.

Sneks start stationary at `Bearing(0, 0)`. Returning `Action.RIGHT` twice results in `Bearing(2, 0)`, moving 2 cells right per tick.

### Toroidal Board

The game board wraps — moving off the right edge appears on the left. This affects:
- Cell neighbors (e.g., `Cell(0, 0).get_left()` wraps to the rightmost column)
- Distance calculations (shortest path may cross edges)
- Collision detection

### Relative Coordinates

Submissions receive positions relative to their head, which is always `Cell(0, 0)`:
- `self.occupied` contains obstacles offset from the head
- `self.food` contains food positions offset from the head
- `self.body[0]` is always `Cell(0, 0)` (the head)

This simplifies AI logic — you don't need to know absolute board position.

### Vision Range

Sneks can only see obstacles within `Config().snek.vision_range` cells. Food is always visible regardless of distance.

## Recording

Install the recording dependency:

```bash
pip install -e ".[record]"
```

Enable recording in your config:

```python
from sneks.engine.config.graphics import GraphicsConfig

MyGameConfig(
    graphics=GraphicsConfig(
        record=True,
        record_prefix="./output",  # Output directory
        record_fps=12,             # Video framerate
    )
)
```

Frames are saved to `output/pics/` during gameplay. Call `recorder.animate_game()` after the run to encode to MP4 in `output/movies/`. The encoder uses ffmpeg via `imageio_ffmpeg`.
