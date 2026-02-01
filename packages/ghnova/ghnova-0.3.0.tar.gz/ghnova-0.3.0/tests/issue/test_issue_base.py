"""Unit tests for the base issue class."""

import logging
from unittest.mock import patch

import pytest

from ghnova.issue.base import BaseIssue


class TestBaseIssue:
    """Test cases for the BaseIssue class."""

    def test_list_issues_endpoint_authenticated_user(self):
        """Test _list_issues_endpoint for authenticated user issues."""
        base_issue = BaseIssue()
        endpoint, issue_type = base_issue._list_issues_endpoint()
        assert endpoint == "/issues"
        assert issue_type == "authenticated user issues"

    def test_list_issues_endpoint_organization(self):
        """Test _list_issues_endpoint for organization issues."""
        base_issue = BaseIssue()
        endpoint, issue_type = base_issue._list_issues_endpoint(organization="test-org")
        assert endpoint == "/orgs/test-org/issues"
        assert issue_type == "organization issues"

    def test_list_issues_endpoint_repository_with_owner(self):
        """Test _list_issues_endpoint for repository issues with owner."""
        base_issue = BaseIssue()
        endpoint, issue_type = base_issue._list_issues_endpoint(owner="test-owner", repository="test-repo")
        assert endpoint == "/repos/test-owner/test-repo/issues"
        assert issue_type == "repository issues"

    def test_list_issues_endpoint_repository_with_organization(self):
        """Test _list_issues_endpoint for repository issues with organization."""
        base_issue = BaseIssue()
        endpoint, issue_type = base_issue._list_issues_endpoint(organization="test-org", repository="test-repo")
        assert endpoint == "/repos/test-org/test-repo/issues"
        assert issue_type == "repository issues"

    def test_list_issues_endpoint_invalid_combination(self):
        """Test _list_issues_endpoint with invalid parameter combination."""
        base_issue = BaseIssue()
        with pytest.raises(ValueError, match=r"Invalid combination of owner, organization, and repository parameters."):
            base_issue._list_issues_endpoint(owner="test-owner")

    def test_list_issues_helper_authenticated_user(self):
        """Test _list_issues_helper for authenticated user issues."""
        from datetime import datetime  # noqa: PLC0415

        base_issue = BaseIssue()
        since_date = datetime(2024, 1, 1, 0, 0, 0)
        endpoint, params, kwargs = base_issue._list_issues_helper(
            filter_by="assigned",
            state="open",
            per_page=50,
            page=2,
            since=since_date,
            collab=True,
            orgs=True,
            owned=True,
            pulls=True,
        )
        assert endpoint == "/issues"
        assert params == {
            "filter": "assigned",
            "state": "open",
            "per_page": 50,
            "page": 2,
            "since": "2024-01-01T00:00:00",
            "collab": True,
            "orgs": True,
            "owned": True,
            "pulls": True,
        }
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_list_issues_helper_authenticated_user_collab(self):
        """Test _list_issues_helper for authenticated user with collab parameter."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(collab=True)
        assert endpoint == "/issues"
        assert params["collab"] is True

    def test_list_issues_helper_authenticated_user_collab_false(self):
        """Test _list_issues_helper for authenticated user with collab=False."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(collab=False)
        assert endpoint == "/issues"
        assert params["collab"] is False

    def test_list_issues_helper_authenticated_user_orgs(self):
        """Test _list_issues_helper for authenticated user with orgs parameter."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(orgs=True)
        assert endpoint == "/issues"
        assert params["orgs"] is True

    def test_list_issues_helper_authenticated_user_orgs_false(self):
        """Test _list_issues_helper for authenticated user with orgs=False."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(orgs=False)
        assert endpoint == "/issues"
        assert params["orgs"] is False

    def test_list_issues_helper_authenticated_user_owned(self):
        """Test _list_issues_helper for authenticated user with owned parameter."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(owned=True)
        assert endpoint == "/issues"
        assert params["owned"] is True

    def test_list_issues_helper_authenticated_user_owned_false(self):
        """Test _list_issues_helper for authenticated user with owned=False."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(owned=False)
        assert endpoint == "/issues"
        assert params["owned"] is False

    def test_list_issues_helper_authenticated_user_filter_by_none(self):
        """Test _list_issues_helper for authenticated user without filter_by parameter."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper()
        assert endpoint == "/issues"
        assert "filter" not in params

    def test_list_issues_helper_authenticated_user_since_none(self):
        """Test _list_issues_helper for authenticated user without since parameter."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(state="open")
        assert endpoint == "/issues"
        assert "since" not in params

    def test_list_issues_helper_authenticated_user_per_page_none(self):
        """Test _list_issues_helper for authenticated user without per_page parameter."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(per_page=None)
        assert endpoint == "/issues"
        assert "per_page" not in params

    def test_list_issues_helper_authenticated_user_page_none(self):
        """Test _list_issues_helper for authenticated user without page parameter."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(page=None)
        assert endpoint == "/issues"
        assert "page" not in params

    def test_list_issues_helper_organization(self):
        """Test _list_issues_helper for organization issues."""
        base_issue = BaseIssue()
        endpoint, params, kwargs = base_issue._list_issues_helper(
            organization="test-org", filter_by="created", state="closed", issue_type="issue"
        )
        assert endpoint == "/orgs/test-org/issues"
        assert params == {
            "filter": "created",
            "state": "closed",
            "type": "issue",
            "page": 1,
            "per_page": 30,
        }
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_list_issues_helper_repository(self):
        """Test _list_issues_helper for repository issues."""
        base_issue = BaseIssue()
        endpoint, params, kwargs = base_issue._list_issues_helper(
            owner="test-owner",
            repository="test-repo",
            state="all",
            labels=["bug", "enhancement"],
            sort="created",
            direction="desc",
            milestone="v1.0",
            assignee="test-user",
            creator="test-creator",
            mentioned="test-mentioned",
        )
        assert endpoint == "/repos/test-owner/test-repo/issues"
        assert params == {
            "state": "all",
            "labels": "bug,enhancement",
            "sort": "created",
            "direction": "desc",
            "milestone": "v1.0",
            "assignee": "test-user",
            "creator": "test-creator",
            "mentioned": "test-mentioned",
            "page": 1,
            "per_page": 30,
        }
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_list_issues_helper_authenticated_user_invalid_params(self):
        """Test _list_issues_helper for authenticated user with invalid parameters."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(
            milestone="v1.0", assignee="user", creator="creator", mentioned="mentioned"
        )
        assert endpoint == "/issues"
        # Invalid params should not be in params
        assert "milestone" not in params
        assert "assignee" not in params
        assert "creator" not in params
        assert "mentioned" not in params
        assert params["page"] == 1
        assert params["per_page"] == 30  # noqa: PLR2004

    def test_list_issues_helper_organization_invalid_params(self):
        """Test _list_issues_helper for organization with invalid parameters."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(
            organization="test-org",
            collab=True,
            orgs=True,
            owned=True,
            pulls=True,
            milestone="v1.0",
            assignee="user",
            creator="creator",
            mentioned="mentioned",
        )
        assert endpoint == "/orgs/test-org/issues"
        # Invalid params should not be in params
        assert "collab" not in params
        assert "orgs" not in params
        assert "owned" not in params
        assert "pulls" not in params
        assert "milestone" not in params
        assert "assignee" not in params
        assert "creator" not in params
        assert "mentioned" not in params

    def test_list_issues_helper_repository_invalid_params(self):
        """Test _list_issues_helper for repository with invalid parameters."""
        base_issue = BaseIssue()
        endpoint, params, _kwargs = base_issue._list_issues_helper(
            owner="test-owner",
            repository="test-repo",
            filter_by="assigned",
            collab=True,
            orgs=True,
            owned=True,
            pulls=True,
            issue_type="issue",
        )
        assert endpoint == "/repos/test-owner/test-repo/issues"
        # Invalid params should not be in params
        assert "filter" not in params
        assert "collab" not in params
        assert "orgs" not in params
        assert "owned" not in params
        assert "pulls" not in params
        assert "type" not in params

    def test_create_issue_endpoint(self):
        """Test _create_issue_endpoint."""
        base_issue = BaseIssue()
        endpoint = base_issue._create_issue_endpoint("test-owner", "test-repo")
        assert endpoint == "/repos/test-owner/test-repo/issues"

    def test_create_issue_helper(self):
        """Test _create_issue_helper."""
        base_issue = BaseIssue()
        endpoint, payload, kwargs = base_issue._create_issue_helper(
            owner="test-owner",
            repository="test-repo",
            title="Test Issue",
            body="This is a test issue.",
            assignee="test-user",
            milestone="v1.0",
            labels=["bug"],
            assignees=["user1", "user2"],
            issue_type="bug",
        )
        assert endpoint == "/repos/test-owner/test-repo/issues"
        assert payload == {
            "title": "Test Issue",
            "body": "This is a test issue.",
            "assignee": "test-user",
            "milestone": "v1.0",
            "labels": ["bug"],
            "assignees": ["user1", "user2"],
            "type": "bug",
        }
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_create_issue_helper_minimal(self):
        """Test _create_issue_helper with minimal parameters."""
        base_issue = BaseIssue()
        endpoint, payload, kwargs = base_issue._create_issue_helper(
            owner="test-owner", repository="test-repo", title="Minimal Issue"
        )
        assert endpoint == "/repos/test-owner/test-repo/issues"
        assert payload == {"title": "Minimal Issue"}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_create_issue_helper_with_additional_headers(self):
        """Test _create_issue_helper with additional headers."""
        base_issue = BaseIssue()
        endpoint, payload, kwargs = base_issue._create_issue_helper(
            owner="test-owner",
            repository="test-repo",
            title="Test Issue",
            headers={"Authorization": "Bearer token"},
        )
        assert endpoint == "/repos/test-owner/test-repo/issues"
        assert payload == {"title": "Test Issue"}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer token",
        }

    def test_get_issue_endpoint(self):
        """Test _get_issue_endpoint."""
        base_issue = BaseIssue()
        endpoint = base_issue._get_issue_endpoint("test-owner", "test-repo", 123)
        assert endpoint == "/repos/test-owner/test-repo/issues/123"

    def test_get_issue_helper(self):
        """Test _get_issue_helper."""
        base_issue = BaseIssue()
        endpoint, kwargs = base_issue._get_issue_helper("test-owner", "test-repo", 123)
        assert endpoint == "/repos/test-owner/test-repo/issues/123"
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_get_issue_helper_with_additional_headers(self):
        """Test _get_issue_helper with additional headers."""
        base_issue = BaseIssue()
        endpoint, kwargs = base_issue._get_issue_helper(
            "test-owner", "test-repo", 123, headers={"Authorization": "Bearer token"}
        )
        assert endpoint == "/repos/test-owner/test-repo/issues/123"
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer token",
        }

    def test_update_issue_endpoint(self):
        """Test _update_issue_endpoint."""
        base_issue = BaseIssue()
        endpoint = base_issue._update_issue_endpoint("test-owner", "test-repo", 123)
        assert endpoint == "/repos/test-owner/test-repo/issues/123"

    def test_update_issue_helper(self):
        """Test _update_issue_helper."""
        base_issue = BaseIssue()
        endpoint, payload, kwargs = base_issue._update_issue_helper(
            owner="test-owner",
            repository="test-repo",
            issue_number=123,
            title="Updated Title",
            body="Updated body.",
            state="closed",
            labels=["fixed"],
        )
        assert endpoint == "/repos/test-owner/test-repo/issues/123"
        assert payload == {
            "title": "Updated Title",
            "body": "Updated body.",
            "state": "closed",
            "labels": ["fixed"],
        }
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_update_issue_helper_minimal(self):
        """Test _update_issue_helper with minimal parameters."""
        base_issue = BaseIssue()
        endpoint, payload, kwargs = base_issue._update_issue_helper(
            owner="test-owner", repository="test-repo", issue_number=123
        )
        assert endpoint == "/repos/test-owner/test-repo/issues/123"
        assert payload == {}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_update_issue_helper_full(self):
        """Test _update_issue_helper with all parameters."""
        base_issue = BaseIssue()
        endpoint, payload, kwargs = base_issue._update_issue_helper(
            owner="test-owner",
            repository="test-repo",
            issue_number=123,
            title="Updated Title",
            body="Updated body.",
            assignee="test-assignee",
            state="closed",
            state_reason="completed",
            milestone="v2.0",
            labels=["fixed", "enhancement"],
            assignees=["user1", "user2"],
            issue_type="bug",
        )
        assert endpoint == "/repos/test-owner/test-repo/issues/123"
        assert payload == {
            "title": "Updated Title",
            "body": "Updated body.",
            "assignee": "test-assignee",
            "state": "closed",
            "state_reason": "completed",
            "milestone": "v2.0",
            "labels": ["fixed", "enhancement"],
            "assignees": ["user1", "user2"],
            "type": "bug",
        }
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_lock_issue_endpoint(self):
        """Test _lock_issue_endpoint."""
        base_issue = BaseIssue()
        endpoint = base_issue._lock_issue_endpoint("test-owner", "test-repo", 123)
        assert endpoint == "/repos/test-owner/test-repo/issues/123/lock"

    def test_lock_issue_helper(self):
        """Test _lock_issue_helper."""
        base_issue = BaseIssue()
        endpoint, payload, kwargs = base_issue._lock_issue_helper(
            owner="test-owner", repository="test-repo", issue_number=123, lock_reason="off-topic"
        )
        assert endpoint == "/repos/test-owner/test-repo/issues/123/lock"
        assert payload == {"lock_reason": "off-topic"}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_lock_issue_helper_no_reason(self):
        """Test _lock_issue_helper without lock reason."""
        base_issue = BaseIssue()
        endpoint, payload, kwargs = base_issue._lock_issue_helper(
            owner="test-owner", repository="test-repo", issue_number=123
        )
        assert endpoint == "/repos/test-owner/test-repo/issues/123/lock"
        assert payload == {}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_lock_issue_helper_with_additional_headers(self):
        """Test _lock_issue_helper with additional headers."""
        base_issue = BaseIssue()
        endpoint, payload, kwargs = base_issue._lock_issue_helper(
            owner="test-owner",
            repository="test-repo",
            issue_number=123,
            lock_reason="spam",
            headers={"Authorization": "Bearer token"},
        )
        assert endpoint == "/repos/test-owner/test-repo/issues/123/lock"
        assert payload == {"lock_reason": "spam"}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer token",
        }

    def test_unlock_issue_endpoint(self):
        """Test _unlock_issue_endpoint."""
        base_issue = BaseIssue()
        endpoint = base_issue._unlock_issue_endpoint("test-owner", "test-repo", 123)
        assert endpoint == "/repos/test-owner/test-repo/issues/123/lock"

    def test_unlock_issue_helper(self):
        """Test _unlock_issue_helper."""
        base_issue = BaseIssue()
        endpoint, kwargs = base_issue._unlock_issue_helper("test-owner", "test-repo", 123)
        assert endpoint == "/repos/test-owner/test-repo/issues/123/lock"
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_unlock_issue_helper_with_additional_headers(self):
        """Test _unlock_issue_helper with additional headers."""
        base_issue = BaseIssue()
        endpoint, kwargs = base_issue._unlock_issue_helper(
            "test-owner", "test-repo", 123, headers={"Authorization": "Bearer token"}
        )
        assert endpoint == "/repos/test-owner/test-repo/issues/123/lock"
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer token",
        }

    def test_list_issues_helper_authenticated_user_ignored_params_warnings(self, caplog):
        """Test _list_issues_helper logs warnings for ignored params in authenticated user issues."""
        base_issue = BaseIssue()
        with caplog.at_level(logging.WARNING):
            base_issue._list_issues_helper(
                issue_type="issue",
                milestone="v1.0",
                assignee="user",
                creator="creator",
                mentioned="mentioned",
            )
        assert "The 'issue_type' parameter is ignored for authenticated user issues." in caplog.text
        assert "The 'milestone' parameter is ignored for authenticated user issues." in caplog.text
        assert "The 'assignee' parameter is ignored for authenticated user issues." in caplog.text
        assert "The 'creator' parameter is ignored for authenticated user issues." in caplog.text
        assert "The 'mentioned' parameter is ignored for authenticated user issues." in caplog.text

    def test_list_issues_helper_organization_ignored_params_warnings(self, caplog):
        """Test _list_issues_helper logs warnings for ignored params in organization issues."""
        base_issue = BaseIssue()
        with caplog.at_level(logging.WARNING):
            base_issue._list_issues_helper(
                organization="test-org",
                collab=True,
                orgs=True,
                owned=True,
                pulls=True,
                milestone="v1.0",
                assignee="user",
                creator="creator",
                mentioned="mentioned",
            )
        assert "The 'collab' parameter is ignored for organization issues." in caplog.text
        assert "The 'orgs' parameter is ignored for organization issues." in caplog.text
        assert "The 'owned' parameter is ignored for organization issues." in caplog.text
        assert "The 'pulls' parameter is ignored for organization issues." in caplog.text
        assert "The 'milestone' parameter is ignored for organization issues." in caplog.text
        assert "The 'assignee' parameter is ignored for organization issues." in caplog.text
        assert "The 'creator' parameter is ignored for organization issues." in caplog.text
        assert "The 'mentioned' parameter is ignored for organization issues." in caplog.text

    def test_list_issues_helper_repository_ignored_params_warnings(self, caplog):
        """Test _list_issues_helper logs warnings for ignored params in repository issues."""
        base_issue = BaseIssue()
        with caplog.at_level(logging.WARNING):
            base_issue._list_issues_helper(
                owner="test-owner",
                repository="test-repo",
                filter_by="assigned",
                collab=True,
                orgs=True,
                owned=True,
                pulls=True,
                issue_type="issue",
            )
        assert "The 'filter_by' parameter is ignored for repository issues." in caplog.text
        assert "The 'collab' parameter is ignored for repository issues." in caplog.text
        assert "The 'orgs' parameter is ignored for repository issues." in caplog.text
        assert "The 'owned' parameter is ignored for repository issues." in caplog.text
        assert "The 'pulls' parameter is ignored for repository issues." in caplog.text
        assert "The 'issue_type' parameter is ignored for repository issues." in caplog.text

    def test_list_issues_helper_invalid_endpoint_type(self):
        """Test _list_issues_helper raises ValueError for invalid endpoint type."""
        base_issue = BaseIssue()
        with (
            patch.object(base_issue, "_list_issues_endpoint", return_value=("/issues", "invalid type")),
            pytest.raises(ValueError, match=r"Invalid endpoint type determined: invalid type"),
        ):
            base_issue._list_issues_helper()
