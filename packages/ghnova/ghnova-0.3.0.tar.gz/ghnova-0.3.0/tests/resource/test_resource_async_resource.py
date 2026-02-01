"""Unit tests for the asynchronous Resource base class."""

from unittest.mock import AsyncMock

import pytest

from ghnova.resource.async_resource import AsyncResource


class TestAsyncResource:
    """Test cases for the AsyncResource class."""

    def test_init(self):
        """Test initialization."""
        mock_client = AsyncMock()
        resource = AsyncResource(client=mock_client)
        assert resource.client == mock_client

    @pytest.mark.asyncio
    async def test_get(self):
        """Test _get method."""
        mock_client = AsyncMock()
        resource = AsyncResource(client=mock_client)
        mock_response = AsyncMock()
        mock_client._request.return_value = mock_response

        result = await resource._get("/test", some_kwarg="value")

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="GET", endpoint="/test", some_kwarg="value")

    @pytest.mark.asyncio
    async def test_post(self):
        """Test _post method."""
        mock_client = AsyncMock()
        resource = AsyncResource(client=mock_client)
        mock_response = AsyncMock()
        mock_client._request.return_value = mock_response

        result = await resource._post("/test", data="payload")

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="POST", endpoint="/test", data="payload")

    @pytest.mark.asyncio
    async def test_put(self):
        """Test _put method."""
        mock_client = AsyncMock()
        resource = AsyncResource(client=mock_client)
        mock_response = AsyncMock()
        mock_client._request.return_value = mock_response

        result = await resource._put("/test", json={"key": "value"})

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="PUT", endpoint="/test", json={"key": "value"})

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test _delete method."""
        mock_client = AsyncMock()
        resource = AsyncResource(client=mock_client)
        mock_response = AsyncMock()
        mock_client._request.return_value = mock_response

        result = await resource._delete("/test")

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="DELETE", endpoint="/test")

    @pytest.mark.asyncio
    async def test_patch(self):
        """Test _patch method."""
        mock_client = AsyncMock()
        resource = AsyncResource(client=mock_client)
        mock_response = AsyncMock()
        mock_client._request.return_value = mock_response

        result = await resource._patch("/test", headers={"custom": "header"})

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="PATCH", endpoint="/test", headers={"custom": "header"})
