"""Unit tests for the asynchronous GitHub client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientSession

from ghnova.client.async_github import AsyncGitHub


class TestAsyncGitHub:
    """Test cases for the AsyncGitHub class."""

    def test_init_with_token(self):
        """Test initialization with a token."""
        client = AsyncGitHub(token="test_token", base_url="https://github.com")
        assert client.token == "test_token"
        assert client.base_url == "https://github.com"
        assert client.headers == {"Authorization": "Bearer test_token"}
        assert client.session is None

    def test_init_without_token(self):
        """Test initialization without a token."""
        client = AsyncGitHub(token=None, base_url="https://github.com")
        assert client.token is None
        assert client.base_url == "https://github.com"
        assert client.headers == {}
        assert client.session is None

    def test_str_representation(self):
        """Test string representation."""
        client = AsyncGitHub(token=None, base_url="https://github.com")
        assert str(client) == "<AsyncGitHub base_url=https://github.com>"

    @pytest.mark.asyncio
    async def test_aenter_context_manager(self):
        """Test entering the async context manager."""
        client = AsyncGitHub(token=None, base_url="https://github.com")
        async with client as c:
            assert c is client
            assert isinstance(client.session, ClientSession)

    @pytest.mark.asyncio
    async def test_aexit_context_manager(self):
        """Test exiting the async context manager."""
        client = AsyncGitHub(token=None, base_url="https://github.com")
        with patch("ghnova.client.async_github.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            async with client:
                pass
            mock_session.close.assert_called_once()

    def test_get_session(self):
        """Test _get_session method."""
        client = AsyncGitHub(token=None, base_url="https://github.com")
        with patch("ghnova.client.async_github.ClientSession") as mock_session_class:
            session = client._get_session(headers={"test": "header"})
            mock_session_class.assert_called_once_with(headers={"test": "header"})
            assert session == mock_session_class.return_value

    @pytest.mark.asyncio
    async def test_request_success(self):
        """Test successful _request."""
        with patch("ghnova.client.async_github.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_session.request.return_value = mock_response

            client = AsyncGitHub(token="test_token", base_url="https://github.com")
            async with client:
                response = await client._request("GET", "repos/octocat/Hello-World", etag="test-etag")

            assert response == mock_response
            mock_session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_without_session(self):
        """Test _request without entering context manager."""
        client = AsyncGitHub(token=None, base_url="https://github.com")
        with pytest.raises(RuntimeError, match="AsyncGitHub must be used as an async context manager"):
            await client._request("GET", "repos/octocat/Hello-World")
