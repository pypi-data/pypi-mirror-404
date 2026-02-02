# SPDX-FileCopyrightText: 2026 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0
"""
Backend-agnostic UI automation protocols for context and element abstraction.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterator,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from qa_pytest_commons.selector import Selector

TElement = TypeVar("TElement", covariant=True)

# Type aliases for UI element suppliers and selectors
type ElementSupplier = Callable[[], UiElement]
type SelectorOrSupplier = Union["Selector", ElementSupplier]


class UiElement(Protocol):
    def click(self) -> None: ...
    def type(self, text: str) -> None: ...
    def clear(self) -> None: ...
    def send_keys(self, *text: str) -> None: ...

    @property
    def text(self) -> str: ...


class UiContext(Protocol[TElement]):
    def find_element(self, by: str, value: Optional[str]) -> TElement: ...

    def find_elements(
        self, by: str, value: Optional[str]) -> Iterator[TElement]: ...

    def get(self, url: str) -> None: ...
    def execute_script(self, script: str, *args: UiElement) -> Any: ...
