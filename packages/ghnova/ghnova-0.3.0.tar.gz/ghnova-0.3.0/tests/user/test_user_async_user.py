"""Unit tests for the asynchronous User resource."""

from unittest.mock import AsyncMock, patch

import pytest

from ghnova.user.async_user import AsyncUser


class TestAsyncUser:
    """Test cases for the AsyncUser class."""

    @pytest.mark.asyncio
    async def test_get_user_authenticated(self):
        """Test get_user for authenticated user."""
        mock_client = AsyncMock()
        user = AsyncUser(client=mock_client)

        with (
            patch.object(user, "_get_user", new_callable=AsyncMock) as mock_get_user,
            patch("ghnova.user.async_user.process_async_response_with_last_modified") as mock_process,
        ):
            mock_get_user.return_value = AsyncMock()
            mock_process.return_value = ({"login": "octocat"}, 200, '"test-etag"', "Wed, 21 Oct 2015 07:28:00 GMT")
            data, status, etag, last_mod = await user.get_user()

        assert data == {"login": "octocat"}
        assert status == 200  # noqa: PLR2004
        assert etag == '"test-etag"'
        assert last_mod == "Wed, 21 Oct 2015 07:28:00 GMT"
        mock_get_user.assert_called_once_with(username=None, account_id=None, etag=None, last_modified=None)

    @pytest.mark.asyncio
    async def test_get_user_by_username(self):
        """Test get_user by username."""
        mock_client = AsyncMock()
        user = AsyncUser(client=mock_client)

        with (
            patch.object(user, "_get_user", new_callable=AsyncMock) as mock_get_user,
            patch("ghnova.user.async_user.process_async_response_with_last_modified") as mock_process,
        ):
            mock_get_user.return_value = AsyncMock()
            mock_process.return_value = ({"login": "octocat"}, 200, None, None)
            data, status, etag, last_mod = await user.get_user(username="octocat")

        assert data == {"login": "octocat"}
        assert status == 200  # noqa: PLR2004
        assert etag is None
        assert last_mod is None
        mock_get_user.assert_called_once_with(username="octocat", account_id=None, etag=None, last_modified=None)

    @pytest.mark.asyncio
    async def test_get_user_not_modified(self):
        """Test get_user with 304 Not Modified."""
        mock_client = AsyncMock()
        user = AsyncUser(client=mock_client)

        with (
            patch.object(user, "_get_user", new_callable=AsyncMock) as mock_get_user,
            patch("ghnova.user.async_user.process_async_response_with_last_modified") as mock_process,
        ):
            mock_get_user.return_value = AsyncMock()
            mock_process.return_value = ({}, 304, '"new-etag"', None)
            data, status, etag, last_mod = await user.get_user(username="octocat", etag='"old-etag"')

        assert data == {}
        assert status == 304  # noqa: PLR2004
        assert etag == '"new-etag"'
        assert last_mod is None

    @pytest.mark.asyncio
    async def test_get_user_with_conditional_headers(self):
        """Test get_user with etag and last_modified."""
        mock_client = AsyncMock()
        user = AsyncUser(client=mock_client)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.json = AsyncMock(return_value={"login": "octocat"})

        with patch.object(user, "_get_user", new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = mock_response
            data, status, etag, last_mod = await user.get_user(
                username="octocat", etag='"test-etag"', last_modified="Wed, 21 Oct 2015 07:28:00 GMT"
            )

        assert data == {"login": "octocat"}
        assert status == 200  # noqa: PLR2004
        assert etag is None
        assert last_mod is None
        mock_get_user.assert_called_once_with(
            username="octocat", account_id=None, etag='"test-etag"', last_modified="Wed, 21 Oct 2015 07:28:00 GMT"
        )

    @pytest.mark.asyncio
    @patch("ghnova.user.async_user.BaseUser._get_user_helper")
    @patch("ghnova.user.async_user.AsyncResource._get")
    async def test_get_user_internal(self, mock_get, mock_helper):
        """Test _get_user method."""
        mock_client = AsyncMock()
        user = AsyncUser(client=mock_client)
        mock_helper.return_value = ("/users/octocat", {"headers": {}})
        mock_get.return_value = AsyncMock()

        result = await user._get_user(username="octocat", etag='"test-etag"')

        mock_helper.assert_called_once_with(username="octocat", account_id=None)
        mock_get.assert_called_once_with(endpoint="/users/octocat", etag='"test-etag"', last_modified=None, headers={})
        assert result == mock_get.return_value

    @pytest.mark.asyncio
    async def test_update_user(self):
        """Test update_user method."""
        mock_client = AsyncMock()
        user = AsyncUser(client=mock_client)

        with (
            patch.object(user, "_update_user", new_callable=AsyncMock) as mock_update_user,
            patch("ghnova.user.async_user.process_async_response_with_last_modified") as mock_process,
        ):
            mock_update_user.return_value = AsyncMock()
            mock_process.return_value = (
                {"login": "octocat", "name": "New Name"},
                200,
                '"new-etag"',
                "Wed, 22 Oct 2015 07:28:00 GMT",
            )
            data, status, etag, last_mod = await user.update_user(name="New Name")

        assert data == {"login": "octocat", "name": "New Name"}
        assert status == 200  # noqa: PLR2004
        assert etag == '"new-etag"'
        assert last_mod == "Wed, 22 Oct 2015 07:28:00 GMT"
        mock_update_user.assert_called_once_with(
            name="New Name",
            email=None,
            blog=None,
            twitter_username=None,
            company=None,
            location=None,
            hireable=None,
            bio=None,
            etag=None,
            last_modified=None,
        )

    @pytest.mark.asyncio
    async def test_list_users(self):
        """Test list_users method."""
        mock_client = AsyncMock()
        user = AsyncUser(client=mock_client)

        with (
            patch.object(user, "_list_users", new_callable=AsyncMock) as mock_list_users,
            patch("ghnova.user.async_user.process_async_response_with_last_modified") as mock_process,
        ):
            mock_list_users.return_value = AsyncMock()
            mock_process.return_value = (
                [{"login": "user1"}, {"login": "user2"}],
                200,
                '"etag"',
                "Wed, 21 Oct 2015 07:28:00 GMT",
            )
            data, status, etag, last_mod = await user.list_users(since=100, per_page=50)

        assert data == [{"login": "user1"}, {"login": "user2"}]
        assert status == 200  # noqa: PLR2004
        assert etag == '"etag"'
        assert last_mod == "Wed, 21 Oct 2015 07:28:00 GMT"
        mock_list_users.assert_called_once_with(since=100, per_page=50, etag=None, last_modified=None)

    @pytest.mark.asyncio
    async def test_get_contextual_information(self):
        """Test get_contextual_information method."""
        mock_client = AsyncMock()
        user = AsyncUser(client=mock_client)

        with (
            patch.object(user, "_get_contextual_information", new_callable=AsyncMock) as mock_get_contextual,
            patch("ghnova.user.async_user.process_async_response_with_last_modified") as mock_process,
        ):
            mock_get_contextual.return_value = AsyncMock()
            mock_process.return_value = ({"contexts": []}, 200, '"etag"', "Wed, 21 Oct 2015 07:28:00 GMT")
            data, status, etag, last_mod = await user.get_contextual_information(
                username="octocat", subject_type="repository", subject_id="123"
            )

        assert data == {"contexts": []}
        assert status == 200  # noqa: PLR2004
        assert etag == '"etag"'
        assert last_mod == "Wed, 21 Oct 2015 07:28:00 GMT"
        mock_get_contextual.assert_called_once_with(username="octocat", subject_type="repository", subject_id="123")
