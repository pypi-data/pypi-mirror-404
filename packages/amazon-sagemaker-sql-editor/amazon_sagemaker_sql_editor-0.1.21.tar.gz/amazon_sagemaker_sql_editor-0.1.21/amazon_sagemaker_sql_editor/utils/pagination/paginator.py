# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import binascii
import json
from json.decoder import JSONDecodeError
import base64
from typing import Optional, Tuple

from amazon_sagemaker_sql_editor.utils.exceptions import SagemakerSQLPaginationError


class TokenManager:
    """
    Helper class to maintain storage, creation and retrieval of pagination tokens.
    """

    def __init__(self):
        self._char_encoding = "utf-8"

    def get_payload(self, token: str):
        """
        Decode token from base64 encoding to payload
        :param token: token to decode
        :return: decoded payload
        """
        try:
            token_base64_bytes = token.encode(self._char_encoding)
            token_in_bytes = base64.b64decode(token_base64_bytes)
            payload_string = token_in_bytes.decode(self._char_encoding)
            payload = json.loads(payload_string)
        except (JSONDecodeError, binascii.Error) as err:
            raise SagemakerSQLPaginationError("Invalid or malformed pagination token received")
        return payload

    def generate_token(self, payload: dict) -> str:
        """
        Encode payload to base64 value
        :param payload: payload to encode
        :return: encoded token
        """
        payload_string = json.dumps(payload)
        payload_string_bytes = payload_string.encode(self._char_encoding)

        base64_bytes = base64.b64encode(payload_string_bytes)
        return base64_bytes.decode(self._char_encoding)


class Paginator:
    """
    Class to provide pagination capability for api: POST./api/data-sources
    """

    def __init__(self):
        self._token_manager = TokenManager()

    def next_page(
        self, token: Optional[str], data: list, page_size: int
    ) -> Tuple[Optional[str], list]:
        """
        Method which slices data based on page size and token payload. Token payload is a dict with previous page's
        end index as value.

        :param token: token to retrieve payload
        :param data: list of objects to slice for page
        :param page_size: size of the page
        :return: tuple[str, list]: 2-tuple with 1st element as next page's token and 2nd element as paged data
        """

        # TODO: Consider an alternate approach for pagination using lazy-loading with map data-structure
        #  to load and slice data for improved algorithmic efficiency.

        # if token provided, retrieve previous page's end index. Else, set previous page's end index as 0
        if token:
            prev_payload = self._token_manager.get_payload(token)
            if (
                type(prev_payload) != dict
                or "page_end" not in prev_payload
                or type(prev_payload["page_end"]) != int
            ):
                raise SagemakerSQLPaginationError("Invalid or malformed pagination token received")
            prev_page_end = prev_payload["page_end"]
        else:
            prev_page_end = 0

        next_token = None
        # calculate next page's end index
        page_end = prev_page_end + page_size
        # if next page's end index doesn't exceed data's end index, generate new token and set its payload
        if page_end <= len(data):
            next_token = self._token_manager.generate_token(payload={"page_end": page_end})

        # return new token and sliced data as page
        return next_token, data[prev_page_end : min(len(data), page_end)]
