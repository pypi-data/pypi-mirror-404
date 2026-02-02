# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import random
from datetime import timedelta
from typing import final

import pytest
import tenacity
from hamcrest import is_  # type: ignore
from qa_pytest_commons.abstract_tests_base import *
from qa_pytest_commons.generic_steps import *
from qa_testing_utils.exceptions import *


@final
class BddScenarioTests(
        AbstractTestsBase[GenericSteps[BaseConfiguration], Configuration]):
    _steps_type = GenericSteps
    _configuration = Configuration()

    def should_work(self):
        (self.steps
            .given.nothing
            .when.waiting(timedelta(seconds=1))
            .then.it_works(is_(True)))

    def should_fail(self):
        with pytest.raises(TestException):
            (self.steps
                .given.nothing
                .when.failing(TestException("just failing")))

    def should_swallow_exception(self):
        (self.steps
            .given.nothing
            .when.safely(lambda: self.steps.when.failing(TestException("boom")))
            .then.it_works(is_(True)))

    def should_retry(self):
        with pytest.raises(tenacity.RetryError):
            (self.steps .given.nothing .when.retrying(
                lambda: self.steps.when.failing(TestException("boom"))))

    def should_repeat(self):
        (self.steps
            .given.nothing
            .when.repeating(
                range(1, 4),
                lambda rep: self.steps.when.waiting(timedelta(seconds=rep)))
            .then.it_works(is_(True)))

    @pytest.mark.flaky
    def should_eventually_work(self):
        def do_something_unreliable() -> str:
            if random.randint(0, 10) > 2:
                raise TestException("failed")
            else:
                return "ok"

        # NOTE the retries policy is defined in GenericSteps
        (self.steps
            .given.nothing
            .then.eventually_assert_that(
                lambda: do_something_unreliable(),
                is_("ok")))
