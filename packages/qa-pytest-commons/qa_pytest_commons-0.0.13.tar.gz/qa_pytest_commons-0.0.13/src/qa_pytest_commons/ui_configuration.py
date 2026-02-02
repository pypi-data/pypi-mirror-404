from functools import cached_property
from typing import final

from qa_pytest_commons.base_configuration import BaseConfiguration


class UiConfiguration(BaseConfiguration):
    """
    UI configuration base class exposing the entry_point property.
    """
    @cached_property
    @final
    def entry_point(self) -> str:
        """
        Returns the UI URL from the configuration parser.

        Returns:
            str: The URL string specified under the "ui/entry_point" in the configuration.

        Raises:
            KeyError: If the "ui" section or "entry_point" key is not present in the configuration parser.
        """
        return self.parser["ui"]["entry_point"]
