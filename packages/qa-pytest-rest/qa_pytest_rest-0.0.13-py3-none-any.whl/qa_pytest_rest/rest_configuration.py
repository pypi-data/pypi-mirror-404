# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from functools import cached_property
from typing import final
from urllib.parse import urljoin

from qa_pytest_commons.base_configuration import BaseConfiguration
from qa_testing_utils.string_utils import EMPTY_STRING


class RestConfiguration(BaseConfiguration):
    """
    Configuration class for REST API endpoints.

    Inherits from:
        BaseConfiguration
    """

    @final
    @cached_property
    def base_url(self) -> str:
        """
        Returns the base URL for the endpoint from the configuration parser.

        Returns:
            str: The base URL specified in the configuration under the 'rest/base_url' key.
        """
        return self.parser["rest"]["base_url"]

    def resource_uri(self, path: str = EMPTY_STRING) -> str:
        """
        Constructs and returns the full endpoint URL by joining the base endpoint URL with the specified path.

        Args:
            path (str, optional): The path to append to the base endpoint URL. Defaults to EMPTY_STRING.

        Returns:
            str: The complete URL formed by joining the base endpoint and the provided path.
        """
        return urljoin(self.base_url, path)
