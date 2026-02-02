# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import timedelta
from typing import Any, Callable, Self, final, override

from functional import seq
from hamcrest import assert_that
from hamcrest.core.matcher import Matcher
from qa_pytest_commons.base_configuration import BaseConfiguration
from qa_pytest_commons.bdd_keywords import BddKeywords
from qa_testing_utils.exception_utils import safely
from qa_testing_utils.logger import Context, LoggerMixin
from qa_testing_utils.object_utils import ImmutableMixin, Valid, valid
from qa_testing_utils.stream_utils import Supplier
from qa_testing_utils.thread_utils import sleep_for
from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class GenericSteps[TConfiguration: BaseConfiguration](
        BddKeywords['GenericSteps'],
        LoggerMixin,
        ImmutableMixin):
    """
    Generic steps base class for BDD-style test implementations.
    Provides retrying, assertion, and step chaining utilities for all step types.

    Type Parameters:
        TConfiguration: The configuration type for the steps implementation.

    Attributes:
        _retrying (Retrying): The tenacity.Retrying instance used for retry logic.
        _configuration (TConfiguration): The configuration instance for these steps.
    """

    _retrying: Retrying
    _configuration: TConfiguration

    def __init__(self, configuration: TConfiguration):
        """
        Initializes the steps with the given configuration and default retry policy.

        Args:
            configuration (TConfiguration): The configuration instance.
        """
        self._configuration = configuration
        # NOTE: waits 1 sec after 1st failure, 2, 4, and 8 secs on subsequent;
        # see BddScenarioTests#should_retry
        self._retrying = Retrying(
            stop=stop_after_attempt(4),
            wait=wait_exponential(min=1, max=10),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(self.log, logging.DEBUG)
        )

    @final
    @property
    def configured(self) -> TConfiguration:
        """
        Returns the configuration instance for these steps.

        Returns:
            TConfiguration: The configuration instance.
        """
        return self._configuration

    @final
    @property
    def retry_policy(self) -> Retrying:
        """
        Returns the retry policy used for retrying steps.

        Returns:
            Retrying: The tenacity.Retrying instance.
        """
        return self._retrying

    @final
    @property
    @override
    def given(self) -> Self:
        Context.set(lambda m: f"Given {m}")
        return self

    @final
    @property
    @override
    def when(self) -> Self:
        Context.set(lambda m: f"When {m}")
        return self

    @final
    @property
    @override
    def then(self) -> Self:
        Context.set(lambda m: f"Then {m}")
        return self

    @final
    @property
    @override
    def and_(self) -> Self:
        Context.set(lambda m: f"And {m}")
        return self

    @final
    @property
    @override
    def with_(self) -> Self:
        Context.set(lambda m: f"With {m}")
        return self

    @final
    @property
    @Context.traced
    def nothing(self) -> Self:
        """
        Intended to support self-testing which does not rely on outer world system.

        Returns:
            Self: these steps
        """
        return self

    # DELETEME
    # # @Context.traced -- nothing to trace here...
    # def configuration(self, configuration: TConfiguration) -> Self:
    #     """
    #     Sets the configuration to use.

    #     Args:
    #         configuration (TConfiguration): the configuration

    #     Returns:
    #         Self: these steps
    #     """
    #     self._configuration = configuration
    #     return self

    def set[T:Valid](self, field_name: str, field_value: T) -> T:
        """
        Sets field to specified value, validating it if possible.

        Args:
            field_name (str): name of field; the field should be defined as annotation
            field_value (T:Valid): value of field that can be validated

        Raises:
            AttributeError: if the field is not defined
            TypeError: if the object does not support the Valid protocol
            InvalidValueException: if the object is invalid

        Returns:
            T: the value of set field
        """
        if field_name not in self.__class__.__annotations__:
            raise AttributeError(
                f"{field_name} is not a valid attribute of "
                f"{self.__class__.__name__}.")

        setattr(self, field_name, valid(field_value))
        return field_value

    @final
    def step(self, *args: Any) -> Self:
        """
        Casts anything to a step.

        Returns:
            Self: these steps
        """
        return self

    @final
    def tracing(self, value: Any) -> Self:
        """
        Logs value at DEBUG level using the logger of this steps class.

        Args:
            value (Any): The value to log.
        Returns:
            Self: these steps
        """
        self.log.debug(f"=== {value}")
        return self

    @final
    @Context.traced
    def waiting(self, duration: timedelta = timedelta(seconds=0)) -> Self:
        """
        Blocks current thread for specified duration.

        Args:
            duration (timedelta, optional): How long to wait. Defaults to 0 seconds.
        Returns:
            Self: these steps
        """
        sleep_for(duration)
        return self

    @final
    @Context.traced
    def failing(self, exception: Exception) -> Self:
        """
        Raises the given exception, for self-testing of retrying and eventually_assert_that.

        Args:
            exception (Exception): The exception to raise.
        Raises:
            exception: That exception.
        Returns:
            Self: these steps
        """
        raise exception

    @final
    @Context.traced
    def repeating(self, range: range, step: Callable[[int], Self]) -> Self:
        """
        Repeats the specified step for each value in the range.

        Args:
            range (range): The range to iterate over.
            step (Callable[[int], Self]): The step to repeat.
        Returns:
            Self: these steps
        """
        seq(range).for_each(step)  # type: ignore
        return self

    # TODO parallel_repeating

    @final
    @Context.traced
    def safely(self, step: Callable[[], Self]) -> Self:
        """
        Executes specified step, swallowing its exceptions.

        Args:
            step (Callable[[], Self]): The step to execute.
        Returns:
            Self: these steps
        """
        return safely(lambda: step()).value_or(self)

    # TODO implement a raises decorator to mark method as raising some exception
    # at run-time the decorator shall check if raised exception matches the declared list.
    # This one would be:
    # @raises(tenacity.RetryError)
    @final
    # @Context.traced
    def retrying(self, step: Callable[[], Self]) -> Self:
        '''
        Retries specified step according to _retry_policy.

        Args:
            step (Callable[[], Self]): The step to retry.
        Returns:
            Self: these steps
        '''
        return self._retrying(step)

    @final
    def eventually_assert_that[T](
            self, supplier: Supplier[T],
            by_rule: Matcher[T]) -> Self:
        '''
        Repeatedly applies specified rule on specified supplier, according to _retry_policy.

        Args:
            supplier (Callable[[], T]): The value supplier.
            by_rule (Matcher[T]): The matcher to apply.
        Returns:
            Self: these steps
        '''
        return self._retrying(lambda: self._assert_that(supplier(), by_rule))

    @final
    @Context.traced
    def it_works(self, matcher: Matcher[bool]) -> Self:
        """
        Intended to support self-testing of reports.

        Args:
            matcher (Matcher[bool]): Matcher for the boolean result.
        Returns:
            Self: these steps
        """
        assert_that(True, matcher)
        return self

    @final
    # NOTE @Context.traced here is redundant
    def _assert_that[T](self, value: T, by_rule: Matcher[T]) -> Self:
        """
        Adapts PyHamcrest's assert_that to the BDD world by returning Self.

        Args:
            value (T): The value to assert upon.
            by_rule (Matcher[T]): The matcher to apply.
        Returns:
            Self: these steps
        """
        assert_that(value, by_rule)
        return self
