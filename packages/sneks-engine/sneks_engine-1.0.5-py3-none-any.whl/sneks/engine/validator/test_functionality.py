import pytest

from sneks.engine import registrar, runner
from sneks.engine.config.base import Config
from sneks.engine.config.graphics import GraphicsConfig
from sneks.engine.core.action import Action
from sneks.engine.core.cell import Cell
from sneks.engine.core.snek import Snek
from sneks.engine.scoring import NormalizedScore
from sneks.engine.util import Singleton
from sneks.games.classic.config import ClassicConfig
from sneks.games.classic.world import Classic


@pytest.fixture
def existing_config() -> Config:
    # Capture any set registrar prefix and wipe the saved config
    existing = Config()
    Singleton._instances = {}
    return existing


def test_basic_functionality(existing_config: Config) -> None:
    Config(
        debug=existing_config.debug,
        registrar_prefix=existing_config.registrar_prefix,
        registrar_submission_sneks=1,
        graphics=GraphicsConfig(display=False),
    )
    submissions = registrar.get_submissions()
    assert len(submissions) == Config().registrar_submission_sneks
    snek: Snek = submissions[0].snek()
    snek.occupied = frozenset((Cell(1, 1),))
    assert snek.get_next_action() in Action


def test_extended_functionality(existing_config: Config) -> None:
    scores = runner.run(
        world=Classic,
        config=ClassicConfig(
            debug=existing_config.debug,
            registrar_prefix=existing_config.registrar_prefix,
            registrar_submission_sneks=1,
            turn_limit=100,
            graphics=GraphicsConfig(display=False),
        ),
    )
    assert scores is not None
    assert len(scores) == 1
    for score in scores:
        assert isinstance(score, NormalizedScore)
        assert score.crashes == 0
        assert score.distance == 0
        assert score.raw.crashes >= 0
        assert score.raw.distance >= 0


def test_multiple_functionality(existing_config: Config) -> None:
    scores = runner.run(
        world=Classic,
        config=ClassicConfig(
            debug=existing_config.debug,
            registrar_prefix=existing_config.registrar_prefix,
            registrar_submission_sneks=10,
            turn_limit=200,
            graphics=GraphicsConfig(display=False),
        ),
    )
    assert scores is not None
    assert len(scores) == 10
    for score in scores:
        assert isinstance(score, NormalizedScore)
        assert 0 <= score.crashes <= 1
        assert 0 <= score.distance <= 1
        assert score.raw.crashes >= 0
        assert score.raw.distance >= 0
