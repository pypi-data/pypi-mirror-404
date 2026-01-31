"""Utility classes for singleton pattern and output suppression."""

import contextlib
import os
from contextlib import ExitStack

from typing_extensions import override


class SwallowOutput(ExitStack):
    """Context manager to suppress stdout when not in debug mode."""

    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug

    @override
    def __enter__(self) -> ExitStack[bool | None]:
        if not self.debug:
            devnull = open(os.devnull, "w")
            self.enter_context(devnull)
            self.enter_context(contextlib.redirect_stdout(devnull))
        return self


class Singleton(type):
    """Metaclass ensuring only one instance exists per class hierarchy."""

    _instances = {}

    @override
    def __call__(cls, *args, **kwargs):
        key = cls

        # Special handling to make all Config subclasses return the same instance
        for c in cls.__mro__:
            if c.__name__ == "Config":
                key = c

        if key not in cls._instances:
            cls._instances[key] = super().__call__(*args, **kwargs)
        return cls._instances[key]
