# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import configparser
import inspect
import os
from functools import cached_property
from pathlib import Path
from typing import final

from qa_testing_utils.logger import LoggerMixin
from qa_testing_utils.object_utils import ImmutableMixin
from qa_testing_utils.pytest_plugin import get_config_overrides
from qa_testing_utils.string_utils import EMPTY_STRING


class Configuration():
    """
    Empty configuration base class for scenarios that do not require configuration.
    """
    pass


class BaseConfiguration(Configuration, LoggerMixin, ImmutableMixin):
    """
    Base class for all types of configurations, providing a parser for a pre-specified configuration file.
    """
    _path: Path

    def __init__(self, path: Path | None = None):
        """
        Initializes the configuration by loading the associated `.ini` file.

        If `path` is not provided, the file is inferred based on the module name
        of the subclass and loaded from a structured configuration directory.

        The default lookup path follows this structure:
            <module_dir>/configurations/${TEST_ENVIRONMENT}/<module_name>.ini

        Where:
            - <module_dir> is the directory where the subclass's module is located
            - ${TEST_ENVIRONMENT} is an optional environment variable that specifies
            the subdirectory (e.g., "dev", "ci", "prod"). If unset, it defaults
            to an empty string (i.e., no subdirectory)
            - <module_name> is the name of the `.py` file defining the subclass

        Args:
            path (Path, optional): Explicit path to the configuration file. If provided,
                                overrides automatic inference.

        Raises:
            FileNotFoundError: If the resolved configuration file does not exist.
        """
        if path is None:
            module_file = Path(inspect.getfile(self.__class__))
            module_stem = module_file.stem
            resources_dir = module_file.parent / "configurations" / \
                os.environ.get("TEST_ENVIRONMENT", EMPTY_STRING)
            ini_file = resources_dir / f"{module_stem}.ini"
            self._path = ini_file
        else:
            self._path = path

        if not self._path.exists():
            raise FileNotFoundError(
                f"configuration file not found: {self._path.resolve()}")

        self.log.debug(f"using configuration from {self._path}")

    # NOTE if properties cannot be cached, this is a red-flag
    # configuration properties should be immutable.
    @final
    @cached_property
    def parser(self) -> configparser.ConfigParser:
        """
        Parser that reads this configuration.
        """
        self.log.debug(f"reading configuration from {self._path}")
        parser = configparser.ConfigParser()
        config_files = parser.read(self._path)
        self.log.debug(f"successfully read {config_files}")

        for section, pairs in get_config_overrides().items():
            if not parser.has_section(section):
                parser.add_section(section)
            for key, value in pairs.items():
                self.log.debug(f"overriding [{section}] {key} = {value}")
                parser.set(section, key, value)

        return parser
