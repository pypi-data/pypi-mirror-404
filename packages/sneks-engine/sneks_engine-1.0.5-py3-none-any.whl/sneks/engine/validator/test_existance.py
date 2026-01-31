import pathlib

from sneks.engine import registrar
from sneks.engine.config.base import Config
from sneks.engine.core.snek import Snek


def test_import():
    prefix = pathlib.Path(Config().registrar_prefix)
    submission_files = registrar.get_submission_files(prefix)
    print(submission_files)
    assert len(submission_files) == 1
    name = registrar.get_submission_name(submission_files[0])
    assert pathlib.Path(prefix, name, "submission.py").exists()
    registrar.load_module(prefix)

    submissions = registrar.get_submissions()
    assert len(submissions) == 1
    assert name == submissions[0].name


def test_class_exists():
    _, snek = registrar.get_custom_snek(pathlib.Path(Config().registrar_prefix))
    assert snek is not None
    assert issubclass(snek, Snek)
