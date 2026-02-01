"""Unit tests for Repository class."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

from requests import Response

from ghnova.repository.repository import Repository


class TestRepository:
    """Tests for the Repository class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.repository = Repository(client=self.mock_client)

    def test_init(self):
        """Test Repository initialization."""
        repo = Repository(client=self.mock_client)
        assert repo.client == self.mock_client

    def test_list_repositories_with_no_params(self):
        """Test _list_repositories with default parameters."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories()

        assert result == mock_response
        self.mock_client._request.assert_called_once()
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["endpoint"] == "/user/repos"

    def test_list_repositories_with_owner(self):
        """Test _list_repositories with owner parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(owner="octocat")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["endpoint"] == "/users/octocat/repos"

    def test_list_repositories_with_organization(self):
        """Test _list_repositories with organization parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(organization="github")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["endpoint"] == "/orgs/github/repos"

    def test_list_repositories_with_visibility(self):
        """Test _list_repositories with visibility parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(visibility="public")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["visibility"] == "public"

    def test_list_repositories_with_affiliation(self):
        """Test _list_repositories with affiliation parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(affiliation=["owner", "collaborator"])

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["affiliation"] == "owner,collaborator"

    def test_list_repositories_with_repository_type(self):
        """Test _list_repositories with repository_type parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(repository_type="public")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["type"] == "public"

    def test_list_repositories_with_sort(self):
        """Test _list_repositories with sort parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(sort="updated")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["sort"] == "updated"

    def test_list_repositories_with_direction(self):
        """Test _list_repositories with direction parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(direction="asc")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["direction"] == "asc"

    def test_list_repositories_with_pagination(self):
        """Test _list_repositories with pagination parameters."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(per_page=50, page=2)

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["per_page"] == 50  # noqa: PLR2004
        assert call_kwargs["params"]["page"] == 2  # noqa: PLR2004

    def test_list_repositories_with_since(self):
        """Test _list_repositories with since parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response
        since_date = datetime(2024, 1, 1, 12, 0, 0)

        result = self.repository._list_repositories(since=since_date)

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["since"] == "2024-01-01T12:00:00"

    def test_list_repositories_with_before(self):
        """Test _list_repositories with before parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response
        before_date = datetime(2024, 12, 31, 23, 59, 59)

        result = self.repository._list_repositories(before=before_date)

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["before"] == "2024-12-31T23:59:59"

    def test_list_repositories_with_etag(self):
        """Test _list_repositories with etag parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(etag="test-etag")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["etag"] == "test-etag"

    def test_list_repositories_with_last_modified(self):
        """Test _list_repositories with last_modified parameter."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        result = self.repository._list_repositories(last_modified="Wed, 21 Oct 2024 07:28:00 GMT")

        assert result == mock_response
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["last_modified"] == "Wed, 21 Oct 2024 07:28:00 GMT"

    def test_list_repositories_with_all_parameters(self):
        """Test _list_repositories with all parameters."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response
        since_date = datetime.now()
        before_date = datetime.now()

        result = self.repository._list_repositories(
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

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_default(self, mock_process):
        """Test list_repositories public method with default parameters."""
        mock_response = MagicMock(spec=Response)
        mock_data = [{"id": 1, "name": "repo1"}]
        mock_process.return_value = (mock_data, 200, "etag-value", "last-modified-value")
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories()

        assert result[0] == mock_data
        assert result[1] == 200  # noqa: PLR2004
        assert result[2] == "etag-value"
        assert result[3] == "last-modified-value"
        mock_process.assert_called_once_with(mock_response)

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_with_owner(self, mock_process):
        """Test list_repositories public method with owner parameter."""
        mock_response = MagicMock(spec=Response)
        mock_data = [{"id": 1, "name": "repo1"}]
        mock_process.return_value = (mock_data, 200, None, None)
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories(owner="octocat")

        assert result[0] == mock_data
        assert result[1] == 200  # noqa: PLR2004
        assert result[2] is None
        assert result[3] is None

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_with_organization(self, mock_process):
        """Test list_repositories public method with organization parameter."""
        mock_response = MagicMock(spec=Response)
        mock_data = [{"id": 1, "name": "repo1"}, {"id": 2, "name": "repo2"}]
        mock_process.return_value = (mock_data, 200, "etag", "last-mod")
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories(organization="github")

        assert len(result[0]) == 2  # noqa: PLR2004
        assert result[0][0]["name"] == "repo1"
        assert result[0][1]["name"] == "repo2"
        assert result[1] == 200  # noqa: PLR2004

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_with_visibility(self, mock_process):
        """Test list_repositories public method with visibility parameter."""
        mock_response = MagicMock(spec=Response)
        mock_data = [{"id": 1, "name": "public_repo", "private": False}]
        mock_process.return_value = (mock_data, 200, None, None)
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories(visibility="public")

        assert result[0][0]["private"] is False
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["visibility"] == "public"

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_with_pagination(self, mock_process):
        """Test list_repositories public method with pagination."""
        mock_response = MagicMock(spec=Response)
        mock_data = [{"id": i, "name": f"repo{i}"} for i in range(1, 51)]
        mock_process.return_value = (mock_data, 200, None, None)
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories(per_page=50, page=2)

        assert len(result[0]) == 50  # noqa: PLR2004
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["per_page"] == 50  # noqa: PLR2004
        assert call_kwargs["params"]["page"] == 2  # noqa: PLR2004

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_response_status_204(self, mock_process):
        """Test list_repositories public method with 204 No Content response."""
        mock_response = MagicMock(spec=Response)
        mock_process.return_value = ({}, 204, None, None)
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories()

        assert result[0] == {}
        assert result[1] == 204  # noqa: PLR2004

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_response_status_not_found(self, mock_process):
        """Test list_repositories public method with 404 response."""
        mock_response = MagicMock(spec=Response)
        mock_process.return_value = ({}, 404, None, None)
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories()

        assert result[0] == {}
        assert result[1] == 404  # noqa: PLR2004

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_with_sort_and_direction(self, mock_process):
        """Test list_repositories public method with sort and direction."""
        mock_response = MagicMock(spec=Response)
        mock_data = [{"id": 1, "name": "repo1", "updated_at": "2024-01-15"}]
        mock_process.return_value = (mock_data, 200, None, None)
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories(sort="updated", direction="desc")

        assert result[1] == 200  # noqa: PLR2004
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["sort"] == "updated"
        assert call_kwargs["params"]["direction"] == "desc"

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_with_affiliation(self, mock_process):
        """Test list_repositories public method with affiliation."""
        mock_response = MagicMock(spec=Response)
        mock_data = [{"id": 1, "name": "owned_repo"}]
        mock_process.return_value = (mock_data, 200, None, None)
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories(affiliation=["owner"])

        assert result[1] == 200  # noqa: PLR2004
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["params"]["affiliation"] == "owner"

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_with_since_and_before(self, mock_process):
        """Test list_repositories public method with since and before."""
        mock_response = MagicMock(spec=Response)
        mock_data = []
        mock_process.return_value = (mock_data, 200, None, None)
        self.mock_client._request.return_value = mock_response
        since = datetime(2024, 1, 1)
        before = datetime(2024, 12, 31)

        result = self.repository.list_repositories(since=since, before=before)

        assert result[1] == 200  # noqa: PLR2004
        call_kwargs = self.mock_client._request.call_args[1]
        assert "since" in call_kwargs["params"]
        assert "before" in call_kwargs["params"]

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_with_etag_and_last_modified(self, mock_process):
        """Test list_repositories public method with etag and last_modified."""
        mock_response = MagicMock(spec=Response)
        mock_data = [{"id": 1, "name": "repo1"}]
        mock_process.return_value = (mock_data, 304, "new-etag", "new-last-mod")
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories(etag="old-etag", last_modified="old-last-mod")

        assert result[1] == 304  # noqa: PLR2004
        assert result[2] == "new-etag"
        assert result[3] == "new-last-mod"
        call_kwargs = self.mock_client._request.call_args[1]
        assert call_kwargs["etag"] == "old-etag"
        assert call_kwargs["last_modified"] == "old-last-mod"

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_public_method_all_parameters(self, mock_process):
        """Test list_repositories public method with all parameters."""
        mock_response = MagicMock(spec=Response)
        mock_data = [{"id": 1, "name": "repo1"}]
        mock_process.return_value = (mock_data, 200, "etag", "last-mod")
        self.mock_client._request.return_value = mock_response
        since_date = datetime(2024, 1, 1)
        before_date = datetime(2024, 12, 31)

        result = self.repository.list_repositories(
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

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_inherits_from_base_repository(self, mock_process):
        """Test that Repository class inherits from BaseRepository."""
        from ghnova.repository.base import BaseRepository  # noqa: PLC0415

        assert issubclass(Repository, BaseRepository)

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_inherits_from_resource(self, mock_process):
        """Test that Repository class inherits from Resource."""
        from ghnova.resource.resource import Resource  # noqa: PLC0415

        assert issubclass(Repository, Resource)

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_empty_response(self, mock_process):
        """Test list_repositories with empty response."""
        mock_response = MagicMock(spec=Response)
        mock_data: list[dict] = []
        mock_process.return_value = (mock_data, 200, None, None)
        self.mock_client._request.return_value = mock_response

        result = self.repository.list_repositories()

        assert result[0] == []
        assert result[1] == 200  # noqa: PLR2004

    @patch("ghnova.repository.repository.process_response_with_last_modified")
    def test_list_repositories_private_method_calls_helper(self, mock_process):
        """Test that _list_repositories calls the helper method correctly."""
        mock_response = MagicMock(spec=Response)
        self.mock_client._request.return_value = mock_response

        with patch.object(self.repository, "_list_repositories_helper") as mock_helper:
            mock_helper.return_value = ("/user/repos", {"per_page": 30, "page": 1}, {})
            self.repository._list_repositories(owner="test", visibility="public")

            mock_helper.assert_called_once()
            call_args = mock_helper.call_args
            assert call_args[1]["owner"] == "test"
            assert call_args[1]["visibility"] == "public"
