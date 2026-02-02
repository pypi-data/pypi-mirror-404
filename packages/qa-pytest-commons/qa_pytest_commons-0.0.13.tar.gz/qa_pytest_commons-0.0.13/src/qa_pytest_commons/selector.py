from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Selector:
    """
    Represents an element selector as a (by, value) pair.

    Attributes:
        by (str): The locator strategy (e.g., "id", "xpath", "css selector").
        value (str): The selector value.
    """
    by: str
    value: str

    def as_tuple(self) -> Tuple[str, str]:
        """
        Returns the selector as a tuple (by, value), suitable for backend adapters.
        """
        return (self.by, self.value)


class By:
    """
    Backend-agnostic factory for element selectors.
    Provides static methods to create Selector objects for each locator strategy.
    """

    @staticmethod
    def id(value: str) -> Selector:
        return Selector("id", value)

    @staticmethod
    def xpath(value: str) -> Selector:
        return Selector("xpath", value)

    @staticmethod
    def link_text(value: str) -> Selector:
        return Selector("link text", value)

    @staticmethod
    def partial_link_text(value: str) -> Selector:
        return Selector("partial link text", value)

    @staticmethod
    def name(value: str) -> Selector:
        return Selector("name", value)

    @staticmethod
    def tag_name(value: str) -> Selector:
        return Selector("tag name", value)

    @staticmethod
    def class_name(value: str) -> Selector:
        return Selector("class name", value)

    @staticmethod
    def css_selector(value: str) -> Selector:
        return Selector("css selector", value)
