# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod


class BddKeywords[TSteps:BddKeywords](ABC):
    """
    Base class for defining Behavior-Driven Development (BDD) keywords.

    This class provides a set of properties that represent the common BDD keywords
    such as `given`, `when`, `then`, `and_`, `with_`. Implementations might be
    of two types: step implementations (GenericSteps) or scenario implementations
    (AbstractTestsBase). In both cases, these properties must return an object
    that provides same step implementation, allowing a fluent-style coding.

    Type Parameters:
        TSteps (TSteps:BddKeywords): The actual steps implementation, or partial implementation.
    """

    @property
    @abstractmethod
    def given(self) -> TSteps:
        """
        Use to start definition of given stage.

        The given stage is the start-up point of a test.
        """
        pass

    @property
    @abstractmethod
    def when(self) -> TSteps:
        """
        Use to start definition of operations stage.

        The operations stage is the part that triggers some behavior on the SUT.
        """
        pass

    @property
    @abstractmethod
    def then(self) -> TSteps:
        """
        Use to start definition of verifications stage.

        The verifications stage is the part that samples actual output of the
        SUT and compares it against a predefined condition (a.k.a. rule).
        """
        pass

    @property
    @abstractmethod
    def and_(self) -> TSteps:
        """
        Use to continue definition of previous stage.
        """
        pass

    @property
    @abstractmethod
    def with_(self) -> TSteps:
        """
        Same as `and_`, sometimes it just sounds better.
        """
        pass
