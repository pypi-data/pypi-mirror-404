import pytest

from sneks.engine.config.base import Config


def main(test_path: str | None = None, debug: bool = True) -> int:
    if test_path is not None:
        Config(debug=debug, registrar_prefix=test_path)
    else:
        Config(debug=debug)
    return pytest.main(["--pyargs", "sneks.engine.validator"])
