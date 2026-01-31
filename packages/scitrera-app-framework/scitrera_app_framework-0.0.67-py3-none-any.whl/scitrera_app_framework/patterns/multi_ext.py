import logging
from logging import Logger
from typing import Callable, Coroutine

from scitrera_app_framework import Variables as Variables
from scitrera_app_framework.api import Plugin


def multi_extension_plugin(
        extension_point: str,
        initialize_fn: Callable[[Variables, logging.Logger], object | None],
        async_ready_fn: Callable[[Variables, Logger, object | None], Coroutine[None]] = None,
        async_stopping_fn: Callable[[Variables, Logger, object | None], Coroutine[None]] = None,
) -> type[Plugin]:
    """
    Factory function to create a multi-extension plugin class.

    Args:
        extension_point (str): The name of the extension point.
        initialize_fn (Callable[[Variables, logging.Logger], object | None]): Function to initialize the plugin.
        async_ready_fn (Callable[[Variables, Logger, object | None], Coroutine[None]] | None): Optional async function called when the plugin is ready.
        async_stopping_fn (Callable[[Variables, Logger, object | None], Coroutine[None]] | None): Optional async function called when the plugin is stopping.

    Returns:
        type[Plugin]: A Plugin subclass implementing the multi-extension behavior.
    """

    class PatternMultiExtensionPlugin(Plugin):
        def extension_point_name(self, v: Variables) -> str:
            return extension_point

        def initialize(self, v: Variables, logger: logging.Logger) -> object | None:
            return initialize_fn(v, logger)

        def is_enabled(self, v: Variables) -> bool:
            return False  # disable "single" extension for a multi-extension plugin

        def is_multi_extension(self, v: Variables) -> bool:
            return True

        async def async_ready(self, v: Variables, logger: Logger, value: object | None):
            if async_ready_fn is not None:
                return await async_ready_fn(v, logger, value)

        async def async_stopping(self, v: Variables, logger: Logger, value: object | None):
            if async_stopping_fn is not None:
                return await async_stopping_fn(v, logger, value)

    return PatternMultiExtensionPlugin
