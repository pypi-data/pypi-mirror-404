"""Response processing utilities with Last-Modified handling."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientResponse, ContentTypeError
from requests import Response

logger = logging.getLogger("ghnova")


def process_response_with_last_modified(
    response: Response,
) -> tuple[dict[str, Any] | list[dict[str, Any]], int, str | None, str | None]:
    """Process an HTTP response and extract data, status, ETag, and Last-Modified.

    Args:
        response: The HTTP response object.

    Returns:
        A tuple containing the response data, status code, ETag, and Last-Modified.

    """
    status_code = response.status_code
    etag = response.headers.get("ETag", None)
    last_modified = response.headers.get("Last-Modified", None)
    if status_code == 204:  # noqa: PLR2004
        data = {}
    elif 200 <= status_code < 300:  # noqa: PLR2004
        try:
            data = response.json()
        except ValueError as e:
            logger.error("Failed to parse JSON response: %s", e)
            data = {}
    else:
        data = {}
    return data, status_code, etag, last_modified


async def process_async_response_with_last_modified(
    response: ClientResponse,
) -> tuple[dict[str, Any] | list[dict[str, Any]], int, str | None, str | None]:
    """Process an asynchronous HTTP response and extract data, status, ETag, and Last-Modified.

    Args:
        response: The asynchronous HTTP response object.

    Returns:
        A tuple containing the response data, status code, ETag, and Last-Modified.

    """
    status_code = response.status
    etag = response.headers.get("ETag", None)
    last_modified = response.headers.get("Last-Modified", None)
    if status_code == 204:  # noqa: PLR2004
        data = {}
    elif 200 <= status_code < 300:  # noqa: PLR2004
        try:
            data = await response.json()
        except (ValueError, ContentTypeError) as e:
            logger.error("Failed to parse JSON response: %s", e)
            data = {}
    else:
        data = {}
    return data, status_code, etag, last_modified
