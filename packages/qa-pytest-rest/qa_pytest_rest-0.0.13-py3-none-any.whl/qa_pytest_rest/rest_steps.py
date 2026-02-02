# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Self, final

import requests
from hamcrest import is_  # type: ignore
from hamcrest.core.matcher import Matcher
from qa_pytest_commons.generic_steps import GenericSteps
from qa_pytest_rest.rest_configuration import RestConfiguration
from qa_testing_utils.logger import Context
from requests import Request, Response


class HttpMethod(str, Enum):
    """
    Enum representing HTTP methods for REST requests.
    """
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class RestSteps[TConfiguration: RestConfiguration](
        GenericSteps[TConfiguration]):
    """
    BDD-style step definitions for REST API operations.

    Type Parameters:
        TConfiguration: The configuration type, must be a RestConfiguration.

    Attributes:
        _rest_session (requests.Session): The HTTP session used for sending REST requests.
    """
    _rest_session: requests.Session

    @final
    def _invoke(self, request: Request) -> Response:
        """
        Sends the given HTTP request using the configured session.

        Args:
            request (Request): The HTTP request to send.
        Returns:
            Response: The HTTP response.
        """
        return self._rest_session.send(
            self._rest_session.prepare_request(request))

    @Context.traced
    @final
    def invoking(self, request: Request) -> Self:
        """
        Send a REST request and assert that the response is OK.

        Args:
            request (Request): The HTTP request to send.
        Returns:
            Self: Enables method chaining.
        Raises:
            AssertionError: If the response is not OK.
        """
        return self.eventually_assert_that(
            lambda: self._invoke(request).ok, is_(True))

    @Context.traced
    @final
    def the_invocation(
            self, request: Request, by_rule: Matcher[Response]) -> Self:
        """
        Send a REST request and assert that the response matches the given matcher.

        Args:
            request (Request): The HTTP request to send.
            by_rule (Matcher[Response]): The matcher to apply to the response.
        Returns:
            Self: Enables method chaining.
        Raises:
            AssertionError: If the response does not match the rule.
        """
        return self.eventually_assert_that(
            lambda: self._invoke(request),
            by_rule)
