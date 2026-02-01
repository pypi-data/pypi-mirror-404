"""Unit tests for response utilities."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ghnova.utils.response import process_async_response_with_last_modified, process_response_with_last_modified


class TestResponseUtils:
    """Test cases for response processing utilities."""

    def test_process_response_with_last_modified_200(self):
        """Test processing response with status 200."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"ETag": '"test-etag"', "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT"}
        mock_response.json.return_value = {"key": "value"}

        data, status, etag, last_mod = process_response_with_last_modified(mock_response)

        assert data == {"key": "value"}
        assert status == 200  # noqa: PLR2004
        assert etag == '"test-etag"'
        assert last_mod == "Wed, 21 Oct 2015 07:28:00 GMT"

    def test_process_response_with_last_modified_304(self):
        """Test processing response with status 304."""
        mock_response = MagicMock()
        mock_response.status_code = 304
        mock_response.headers = {"ETag": '"new-etag"'}

        data, status, etag, last_mod = process_response_with_last_modified(mock_response)

        assert data == {}
        assert status == 304  # noqa: PLR2004
        assert etag == '"new-etag"'
        assert last_mod is None

    def test_process_response_with_last_modified_204(self):
        """Test processing response with status 204."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.headers = {"ETag": '"test-etag"'}

        data, status, etag, last_mod = process_response_with_last_modified(mock_response)

        assert data == {}
        assert status == 204  # noqa: PLR2004
        assert etag == '"test-etag"'
        assert last_mod is None

    def test_process_response_with_last_modified_404(self):
        """Test processing response with status 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}

        data, status, etag, last_mod = process_response_with_last_modified(mock_response)

        assert data == {}
        assert status == 404  # noqa: PLR2004
        assert etag is None
        assert last_mod is None

    def test_process_response_with_last_modified_json_error(self):
        """Test processing response with JSON parsing error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.side_effect = ValueError("Invalid JSON")

        data, status, etag, last_mod = process_response_with_last_modified(mock_response)

        assert data == {}
        assert status == 200  # noqa: PLR2004
        assert etag is None
        assert last_mod is None

    @pytest.mark.asyncio
    async def test_process_async_response_with_last_modified_200(self):
        """Test processing async response with status 200."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"ETag": '"test-etag"', "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT"}
        mock_response.json = AsyncMock(return_value={"key": "value"})

        data, status, etag, last_mod = await process_async_response_with_last_modified(mock_response)

        assert data == {"key": "value"}
        assert status == 200  # noqa: PLR2004
        assert etag == '"test-etag"'
        assert last_mod == "Wed, 21 Oct 2015 07:28:00 GMT"

    @pytest.mark.asyncio
    async def test_process_async_response_with_last_modified_304(self):
        """Test processing async response with status 304."""
        mock_response = AsyncMock()
        mock_response.status = 304
        mock_response.headers = {"ETag": '"new-etag"'}

        data, status, etag, last_mod = await process_async_response_with_last_modified(mock_response)

        assert data == {}
        assert status == 304  # noqa: PLR2004
        assert etag == '"new-etag"'
        assert last_mod is None

    @pytest.mark.asyncio
    async def test_process_async_response_with_last_modified_204(self):
        """Test processing async response with status 204."""
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.headers = {"ETag": '"test-etag"'}

        data, status, etag, last_mod = await process_async_response_with_last_modified(mock_response)

        assert data == {}
        assert status == 204  # noqa: PLR2004
        assert etag == '"test-etag"'
        assert last_mod is None

    @pytest.mark.asyncio
    async def test_process_async_response_with_last_modified_404(self):
        """Test processing async response with status 404."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.headers = {}

        data, status, etag, last_mod = await process_async_response_with_last_modified(mock_response)

        assert data == {}
        assert status == 404  # noqa: PLR2004
        assert etag is None
        assert last_mod is None

    @pytest.mark.asyncio
    async def test_process_async_response_with_last_modified_json_error(self):
        """Test processing async response with JSON parsing error."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

        data, status, etag, last_mod = await process_async_response_with_last_modified(mock_response)

        assert data == {}
        assert status == 200  # noqa: PLR2004
        assert etag is None
        assert last_mod is None
