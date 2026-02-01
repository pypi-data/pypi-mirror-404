"""Unit tests for AsyncRepository class."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientResponse

from ghnova.repository.async_repository import AsyncRepository


class TestAsyncRepository:
    """Tests for the AsyncRepository class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = AsyncMock()
        self.repository = AsyncRepository(client=self.mock_client)

    def test_init(self):
        """Test AsyncRepository initialization."""
        repo = AsyncRepository(client=self.mock_client)
        assert repo.client == self.mock_client

    @pytest.mark.asyncio
    async def test_list_repositories_with_no_params(self):
        """Test _list_repositories with default parameters."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories()

        assert result == mock_response
        self.mock_client._request.assert_called_once()
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["endpoint"] == "/user/repos"

    @pytest.mark.asyncio
    async def test_list_repositories_with_owner(self):
        """Test _list_repositories with owner parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(owner="octocat")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["endpoint"] == "/users/octocat/repos"

    @pytest.mark.asyncio
    async def test_list_repositories_with_organization(self):
        """Test _list_repositories with organization parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(organization="github")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["endpoint"] == "/orgs/github/repos"

    @pytest.mark.asyncio
    async def test_list_repositories_with_visibility(self):
        """Test _list_repositories with visibility parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(visibility="public")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["visibility"] == "public"

    @pytest.mark.asyncio
    async def test_list_repositories_with_affiliation(self):
        """Test _list_repositories with affiliation parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(affiliation=["owner", "collaborator"])

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["affiliation"] == "owner,collaborator"

    @pytest.mark.asyncio
    async def test_list_repositories_with_repository_type(self):
        """Test _list_repositories with repository_type parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(repository_type="public")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["type"] == "public"

    @pytest.mark.asyncio
    async def test_list_repositories_with_sort(self):
        """Test _list_repositories with sort parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(sort="updated")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["sort"] == "updated"

    @pytest.mark.asyncio
    async def test_list_repositories_with_direction(self):
        """Test _list_repositories with direction parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(direction="asc")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["direction"] == "asc"

    @pytest.mark.asyncio
    async def test_list_repositories_with_pagination(self):
        """Test _list_repositories with pagination parameters."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(per_page=50, page=2)

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["per_page"] == 50  # noqa: PLR2004
        assert call_kwargs["params"]["page"] == 2  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_list_repositories_with_since(self):
        """Test _list_repositories with since parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response
        since_date = datetime(2024, 1, 1, 12, 0, 0)

        result = await self.repository._list_repositories(since=since_date)

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["since"] == "2024-01-01T12:00:00"

    @pytest.mark.asyncio
    async def test_list_repositories_with_before(self):
        """Test _list_repositories with before parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response
        before_date = datetime(2024, 12, 31, 23, 59, 59)

        result = await self.repository._list_repositories(before=before_date)

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["before"] == "2024-12-31T23:59:59"

    @pytest.mark.asyncio
    async def test_list_repositories_with_etag(self):
        """Test _list_repositories with etag parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(etag="test-etag")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["etag"] == "test-etag"

    @pytest.mark.asyncio
    async def test_list_repositories_with_last_modified(self):
        """Test _list_repositories with last_modified parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        result = await self.repository._list_repositories(last_modified="Wed, 21 Oct 2024 07:28:00 GMT")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["last_modified"] == "Wed, 21 Oct 2024 07:28:00 GMT"

    @pytest.mark.asyncio
    async def test_list_repositories_with_all_parameters(self):
        """Test _list_repositories with all parameters."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response
        since_date = datetime.now()
        before_date = datetime.now()

        result = await self.repository._list_repositories(
            owner=None,
            organization=None,
            visibility="private",
            affiliation=["owner", "collaborator"],
            repository_type="private",
            sort="created",
            direction="desc",
            per_page=100,
            page=3,
            since=since_date,
            before=before_date,
            etag="etag-value",
            last_modified="last-modified-value",
        )

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["endpoint"] == "/user/repos"
        assert call_kwargs["params"]["visibility"] == "private"
        assert call_kwargs["params"]["affiliation"] == "owner,collaborator"
        assert call_kwargs["params"]["type"] == "private"
        assert call_kwargs["params"]["sort"] == "created"
        assert call_kwargs["params"]["direction"] == "desc"
        assert call_kwargs["params"]["per_page"] == 100  # noqa: PLR2004
        assert call_kwargs["params"]["page"] == 3  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_default(self):
        """Test list_repositories public method with default parameters."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "repo1"}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, "etag-value", "last-modified-value")
            result = await self.repository.list_repositories()

            assert result[0] == mock_data
            assert result[1] == 200  # noqa: PLR2004
            assert result[2] == "etag-value"
            assert result[3] == "last-modified-value"
            mock_process.assert_called_once_with(mock_response)

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_with_owner(self):
        """Test list_repositories public method with owner parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "repo1"}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)
            result = await self.repository.list_repositories(owner="octocat")

            assert result[0] == mock_data
            assert result[1] == 200  # noqa: PLR2004
            assert result[2] is None
            assert result[3] is None

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_with_organization(self):
        """Test list_repositories public method with organization parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "repo1"}, {"id": 2, "name": "repo2"}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, "etag", "last-mod")
            result = await self.repository.list_repositories(organization="github")

            assert len(result[0]) == 2  # noqa: PLR2004
            assert result[0][0]["name"] == "repo1"
            assert result[0][1]["name"] == "repo2"
            assert result[1] == 200  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_with_visibility(self):
        """Test list_repositories public method with visibility parameter."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "public_repo", "private": False}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)
            result = await self.repository.list_repositories(visibility="public")

            assert result[0][0]["private"] is False
            call_kwargs = self.mock_client._request.call_args[1]
            assert call_kwargs["params"]["visibility"] == "public"

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_with_pagination(self):
        """Test list_repositories public method with pagination."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": i, "name": f"repo{i}"} for i in range(1, 51)]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)
            result = await self.repository.list_repositories(per_page=50, page=2)

            assert len(result[0]) == 50  # noqa: PLR2004
            call_kwargs = self.mock_client._request.call_args[1]
            assert call_kwargs["params"]["per_page"] == 50  # noqa: PLR2004
            assert call_kwargs["params"]["page"] == 2  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_response_status_204(self):
        """Test list_repositories public method with 204 No Content response."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = ({}, 204, None, None)
            result = await self.repository.list_repositories()

            assert result[0] == {}
            assert result[1] == 204  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_response_status_not_found(self):
        """Test list_repositories public method with 404 response."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = ({}, 404, None, None)
            result = await self.repository.list_repositories()

            assert result[0] == {}
            assert result[1] == 404  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_with_sort_and_direction(self):
        """Test list_repositories public method with sort and direction."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "repo1", "updated_at": "2024-01-15"}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)
            result = await self.repository.list_repositories(sort="updated", direction="desc")

            assert result[1] == 200  # noqa: PLR2004
            call_kwargs = self.mock_client._request.call_args[1]
            assert call_kwargs["params"]["sort"] == "updated"
            assert call_kwargs["params"]["direction"] == "desc"

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_with_affiliation(self):
        """Test list_repositories public method with affiliation."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "owned_repo"}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)
            result = await self.repository.list_repositories(affiliation=["owner"])

            assert result[1] == 200  # noqa: PLR2004
            call_kwargs = self.mock_client._request.call_args[1]
            assert call_kwargs["params"]["affiliation"] == "owner"

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_with_since_and_before(self):
        """Test list_repositories public method with since and before."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data: list[dict] = []
        self.mock_client._request.return_value = mock_response
        since = datetime(2024, 1, 1)
        before = datetime(2024, 12, 31)

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)
            result = await self.repository.list_repositories(since=since, before=before)

            assert result[1] == 200  # noqa: PLR2004
            call_kwargs = self.mock_client._request.call_args[1]
            assert "since" in call_kwargs["params"]
            assert "before" in call_kwargs["params"]

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_with_etag_and_last_modified(self):
        """Test list_repositories public method with etag and last_modified."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "repo1"}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 304, "new-etag", "new-last-mod")
            result = await self.repository.list_repositories(etag="old-etag", last_modified="old-last-mod")

            assert result[1] == 304  # noqa: PLR2004
            assert result[2] == "new-etag"
            assert result[3] == "new-last-mod"
            call_kwargs = self.mock_client._request.call_args[1]
            assert call_kwargs["etag"] == "old-etag"
            assert call_kwargs["last_modified"] == "old-last-mod"

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_all_parameters(self):
        """Test list_repositories public method with all parameters."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "repo1"}]
        self.mock_client._request.return_value = mock_response
        since_date = datetime(2024, 1, 1)
        before_date = datetime(2024, 12, 31)

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, "etag", "last-mod")
            result = await self.repository.list_repositories(
                owner=None,
                organization=None,
                visibility="private",
                affiliation=["owner", "collaborator"],
                repository_type="private",
                sort="created",
                direction="desc",
                per_page=100,
                page=1,
                since=since_date,
                before=before_date,
                etag="etag-value",
                last_modified="last-modified-value",
            )

            assert result[0] == mock_data
            assert result[1] == 200  # noqa: PLR2004
            assert result[2] == "etag"
            assert result[3] == "last-mod"

    @pytest.mark.asyncio
    async def test_list_repositories_inherits_from_base_repository(self):
        """Test that AsyncRepository class inherits from BaseRepository."""
        from ghnova.repository.base import BaseRepository  # noqa: PLC0415

        assert issubclass(AsyncRepository, BaseRepository)

    @pytest.mark.asyncio
    async def test_list_repositories_inherits_from_async_resource(self):
        """Test that AsyncRepository class inherits from AsyncResource."""
        from ghnova.resource.async_resource import AsyncResource  # noqa: PLC0415

        assert issubclass(AsyncRepository, AsyncResource)

    @pytest.mark.asyncio
    async def test_list_repositories_public_method_empty_response(self):
        """Test list_repositories with empty response."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data: list[dict] = []
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)
            result = await self.repository.list_repositories()

            assert result[0] == []
            assert result[1] == 200  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_list_repositories_private_method_calls_helper(self):
        """Test that _list_repositories calls the helper method correctly."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        with patch.object(self.repository, "_list_repositories_helper") as mock_helper:
            mock_helper.return_value = ("/user/repos", {"per_page": 30, "page": 1}, {})
            await self.repository._list_repositories(owner="test", visibility="public")

            mock_helper.assert_called_once()
            call_args = mock_helper.call_args
            assert call_args[1]["owner"] == "test"
            assert call_args[1]["visibility"] == "public"

    @pytest.mark.asyncio
    async def test_list_repositories_is_awaitable(self):
        """Test that list_repositories returns an awaitable."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "repo1"}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)
            output = self.repository.list_repositories()
            assert hasattr(output, "__await__")
            result = await output
            assert result[0] == mock_data

    @pytest.mark.asyncio
    async def test_list_repositories_private_is_awaitable(self):
        """Test that _list_repositories returns an awaitable."""
        mock_response = AsyncMock(spec=ClientResponse)
        self.mock_client._request.return_value = mock_response

        output = self.repository._list_repositories()
        assert hasattr(output, "__await__")
        result = await output
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_list_repositories_with_multiple_visibility_types(self):
        """Test list_repositories with different visibility types."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "repo1"}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)

            # Test with "all"
            await self.repository.list_repositories(visibility="all")
            assert self.mock_client._request.call_args[1]["params"]["visibility"] == "all"

            # Test with "private"
            await self.repository.list_repositories(visibility="private")
            assert self.mock_client._request.call_args[1]["params"]["visibility"] == "private"

    @pytest.mark.asyncio
    async def test_list_repositories_with_multiple_repository_types(self):
        """Test list_repositories with different repository types."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_data = [{"id": 1, "name": "repo1"}]
        self.mock_client._request.return_value = mock_response

        with patch("ghnova.repository.async_repository.process_async_response_with_last_modified") as mock_process:
            mock_process.return_value = (mock_data, 200, None, None)

            # Test with "all"
            await self.repository.list_repositories(repository_type="all")
            assert self.mock_client._request.call_args[1]["params"]["type"] == "all"

            # Test with "member"
            await self.repository.list_repositories(repository_type="member")
            assert self.mock_client._request.call_args[1]["params"]["type"] == "member"
