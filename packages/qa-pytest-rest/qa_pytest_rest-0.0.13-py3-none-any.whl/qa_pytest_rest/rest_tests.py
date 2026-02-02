# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any, override

import requests
from qa_pytest_commons.abstract_tests_base import AbstractTestsBase
from qa_pytest_rest.rest_configuration import RestConfiguration
from qa_pytest_rest.rest_steps import RestSteps


class RestTests[
    TSteps: RestSteps[Any],
    TConfiguration: RestConfiguration
](AbstractTestsBase[TSteps, TConfiguration]):
    """
    Base class for REST API test cases.

    This class provides a reusable test base for REST API testing, managing a `requests.Session`
    for each test method. It is generic over the types of steps and configuration used.

    Attributes:
        _rest_session (requests.Session): The HTTP session used for making REST requests. Not thread-safe.

    Type Parameters:
        TSteps: The type of the steps class, typically derived from RestSteps.
        TConfiguration: The type of the configuration class, typically derived from RestConfiguration.
    """
    _rest_session: requests.Session  # not thread safe

    @property
    def rest_session(self) -> requests.Session:
        """
        Returns the HTTP session used for making REST requests.

        Returns:
            requests.Session: The HTTP session instance.
        """
        return self._rest_session

    @override
    def setup_method(self):
        """
        Initializes a new requests.Session before each test method.
        """
        super().setup_method()
        self._rest_session = requests.Session()

    @override
    def teardown_method(self):
        """
        Closes the requests.Session after each test method.
        """
        try:
            self._rest_session.close()
        finally:
            super().teardown_method()
