"""Unit tests for BaseRepository class."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pytest

from ghnova.repository.base import BaseRepository


class TestBaseRepository:
    """Tests for the BaseRepository class."""

    def test_list_repositories_endpoint_no_params(self):
        """Test endpoint determination with no owner or organization."""
        repo = BaseRepository()
        endpoint, description = repo._list_repositories_endpoint()
        assert endpoint == "/user/repos"
        assert description == "authenticated user's repositories"

    def test_list_repositories_endpoint_with_owner(self):
        """Test endpoint determination with owner parameter."""
        repo = BaseRepository()
        endpoint, description = repo._list_repositories_endpoint(owner="octocat")
        assert endpoint == "/users/octocat/repos"
        assert description == "user's repositories"

    def test_list_repositories_endpoint_with_organization(self):
        """Test endpoint determination with organization parameter."""
        repo = BaseRepository()
        endpoint, description = repo._list_repositories_endpoint(organization="github")
        assert endpoint == "/orgs/github/repos"
        assert description == "organization's repositories"

    def test_list_repositories_endpoint_both_owner_and_organization(self):
        """Test that ValueError is raised when both owner and organization are provided."""
        repo = BaseRepository()
        with pytest.raises(ValueError, match=r"Specify either owner or organization, not both."):
            repo._list_repositories_endpoint(owner="octocat", organization="github")

    def test_list_repositories_helper_defaults(self):
        """Test helper method with default parameters."""
        repo = BaseRepository()
        endpoint, params, kwargs = repo._list_repositories_helper()
        assert endpoint == "/user/repos"
        assert params["per_page"] == 30  # noqa: PLR2004
        assert params["page"] == 1
        assert "Accept" in kwargs["headers"]
        assert kwargs["headers"]["X-GitHub-Api-Version"] == "2022-11-28"

    def test_list_repositories_helper_with_owner(self):
        """Test helper method with owner parameter."""
        repo = BaseRepository()
        endpoint, params, _kwargs = repo._list_repositories_helper(owner="octocat")
        assert endpoint == "/users/octocat/repos"
        assert params["per_page"] == 30  # noqa: PLR2004
        assert params["page"] == 1

    def test_list_repositories_helper_with_organization(self):
        """Test helper method with organization parameter."""
        repo = BaseRepository()
        endpoint, params, _kwargs = repo._list_repositories_helper(organization="github")
        assert endpoint == "/orgs/github/repos"
        assert params["per_page"] == 30  # noqa: PLR2004
        assert params["page"] == 1

    def test_list_repositories_helper_with_visibility(self):
        """Test helper method with visibility parameter."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(visibility="public")
        assert params["visibility"] == "public"

    def test_list_repositories_helper_visibility_ignored_for_organization(self, caplog):
        """Test that visibility parameter is ignored for organization repositories."""
        repo = BaseRepository()
        with caplog.at_level(logging.WARNING):
            _endpoint, params, _kwargs = repo._list_repositories_helper(organization="github", visibility="public")
        assert "visibility" not in params
        assert "not applicable" in caplog.text

    def test_list_repositories_helper_with_affiliation(self):
        """Test helper method with affiliation parameter."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(affiliation=["owner", "collaborator"])
        assert params["affiliation"] == "owner,collaborator"

    def test_list_repositories_helper_affiliation_ignored_for_user(self, caplog):
        """Test that affiliation parameter is only used for authenticated user."""
        repo = BaseRepository()
        with caplog.at_level(logging.WARNING):
            _endpoint, params, _kwargs = repo._list_repositories_helper(owner="octocat", affiliation=["owner"])
        assert "affiliation" not in params
        assert "only applicable" in caplog.text

    def test_list_repositories_helper_with_repository_type(self):
        """Test helper method with repository_type parameter."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(repository_type="public")
        assert params["type"] == "public"

    def test_list_repositories_helper_with_sort(self):
        """Test helper method with sort parameter."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(sort="updated")
        assert params["sort"] == "updated"

    def test_list_repositories_helper_with_direction(self):
        """Test helper method with direction parameter."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(direction="desc")
        assert params["direction"] == "desc"

    def test_list_repositories_helper_with_pagination(self):
        """Test helper method with pagination parameters."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(per_page=50, page=2)
        assert params["per_page"] == 50  # noqa: PLR2004
        assert params["page"] == 2  # noqa: PLR2004

    def test_list_repositories_helper_with_since(self):
        """Test helper method with since parameter."""
        repo = BaseRepository()
        since_date = datetime(2024, 1, 1, 12, 0, 0)
        _endpoint, params, _kwargs = repo._list_repositories_helper(since=since_date)
        assert params["since"] == "2024-01-01T12:00:00"

    def test_list_repositories_helper_since_ignored_for_organization(self, caplog):
        """Test that since parameter is ignored for organization repositories."""
        repo = BaseRepository()
        since_date = datetime(2024, 1, 1)
        with caplog.at_level(logging.WARNING):
            _endpoint, params, _kwargs = repo._list_repositories_helper(organization="github", since=since_date)
        assert "since" not in params
        assert "not applicable" in caplog.text

    def test_list_repositories_helper_with_before(self):
        """Test helper method with before parameter."""
        repo = BaseRepository()
        before_date = datetime(2024, 12, 31, 23, 59, 59)
        _endpoint, params, _kwargs = repo._list_repositories_helper(before=before_date)
        assert params["before"] == "2024-12-31T23:59:59"

    def test_list_repositories_helper_before_ignored_for_organization(self, caplog):
        """Test that before parameter is ignored for organization repositories."""
        repo = BaseRepository()
        before_date = datetime(2024, 12, 31)
        with caplog.at_level(logging.WARNING):
            _endpoint, params, _kwargs = repo._list_repositories_helper(organization="github", before=before_date)
        assert "before" not in params
        assert "not applicable" in caplog.text

    def test_list_repositories_helper_with_custom_headers(self):
        """Test helper method preserves and merges custom headers."""
        repo = BaseRepository()
        custom_headers = {"X-Custom-Header": "value"}
        _endpoint, _params, kwargs = repo._list_repositories_helper(headers=custom_headers)
        assert kwargs["headers"]["X-Custom-Header"] == "value"
        assert kwargs["headers"]["Accept"] == "application/vnd.github+json"

    def test_list_repositories_helper_headers_precedence(self):
        """Test that custom headers override default headers."""
        repo = BaseRepository()
        custom_headers = {"Accept": "application/json"}
        _endpoint, _params, kwargs = repo._list_repositories_helper(headers=custom_headers)
        assert kwargs["headers"]["Accept"] == "application/json"

    def test_list_repositories_helper_all_parameters(self):
        """Test helper method with all parameters specified."""
        repo = BaseRepository()
        since_date = datetime.now() - timedelta(days=7)
        before_date = datetime.now()
        endpoint, params, _kwargs = repo._list_repositories_helper(
            visibility="public",
            affiliation=["owner", "collaborator", "organization_member"],
            repository_type="owner",
            sort="updated",
            direction="asc",
            per_page=100,
            page=3,
            since=since_date,
            before=before_date,
        )
        assert endpoint == "/user/repos"
        assert params["visibility"] == "public"
        assert params["affiliation"] == "owner,collaborator,organization_member"
        assert params["type"] == "owner"
        assert params["sort"] == "updated"
        assert params["direction"] == "asc"
        assert params["per_page"] == 100  # noqa: PLR2004
        assert params["page"] == 3  # noqa: PLR2004
        assert "since" in params
        assert "before" in params

    def test_list_repositories_helper_visibility_all(self):
        """Test helper method with visibility set to 'all'."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(visibility="all")
        assert params["visibility"] == "all"

    def test_list_repositories_helper_visibility_private(self):
        """Test helper method with visibility set to 'private'."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(visibility="private")
        assert params["visibility"] == "private"

    def test_list_repositories_helper_repository_type_all(self):
        """Test helper method with repository_type set to 'all'."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(repository_type="all")
        assert params["type"] == "all"

    def test_list_repositories_helper_repository_type_member(self):
        """Test helper method with repository_type set to 'member'."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(repository_type="member")
        assert params["type"] == "member"

    def test_list_repositories_helper_sort_created(self):
        """Test helper method with sort set to 'created'."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(sort="created")
        assert params["sort"] == "created"

    def test_list_repositories_helper_sort_pushed(self):
        """Test helper method with sort set to 'pushed'."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(sort="pushed")
        assert params["sort"] == "pushed"

    def test_list_repositories_helper_sort_full_name(self):
        """Test helper method with sort set to 'full_name'."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(sort="full_name")
        assert params["sort"] == "full_name"

    def test_list_repositories_helper_direction_asc(self):
        """Test helper method with direction set to 'asc'."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(direction="asc")
        assert params["direction"] == "asc"

    def test_list_repositories_helper_multiple_affiliations(self):
        """Test helper method with multiple affiliation values."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(
            affiliation=["owner", "collaborator", "organization_member"]
        )
        assert params["affiliation"] == "owner,collaborator,organization_member"

    def test_list_repositories_helper_single_affiliation(self):
        """Test helper method with single affiliation value."""
        repo = BaseRepository()
        _endpoint, params, _kwargs = repo._list_repositories_helper(affiliation=["owner"])
        assert params["affiliation"] == "owner"
