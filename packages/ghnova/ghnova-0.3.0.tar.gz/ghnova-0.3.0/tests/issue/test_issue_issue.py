"""Unit tests for the synchronous Issue class."""

from unittest.mock import MagicMock, patch

from ghnova.issue.issue import Issue


class TestIssue:
    """Test cases for the Issue class."""

    def test_list_issues(self):
        """Test list_issues method."""
        mock_client = MagicMock()
        issue = Issue(client=mock_client)
        mock_response = MagicMock()
        mock_data = [{"id": 1, "title": "Test Issue"}]
        mock_status = 200
        mock_etag = '"test-etag"'
        mock_last_mod = "Wed, 21 Oct 2015 07:28:00 GMT"

        with (
            patch.object(issue, "_list_issues", return_value=mock_response) as mock_private,
            patch(
                "ghnova.issue.issue.process_response_with_last_modified",
                return_value=(mock_data, mock_status, mock_etag, mock_last_mod),
            ) as mock_process,
        ):
            result = issue.list_issues(owner="test-owner", repository="test-repo", state="open")

            mock_private.assert_called_once_with(
                owner="test-owner",
                organization=None,
                repository="test-repo",
                state="open",
                filter_by=None,
                labels=None,
                sort=None,
                direction=None,
                since=None,
                collab=None,
                orgs=None,
                owned=None,
                pulls=None,
                issue_type=None,
                milestone=None,
                assignee=None,
                creator=None,
                mentioned=None,
                per_page=30,
                page=1,
                etag=None,
                last_modified=None,
            )
            mock_process.assert_called_once_with(mock_response)
            assert result == (mock_data, mock_status, mock_etag, mock_last_mod)

    def test_create_issue(self):
        """Test create_issue method."""
        mock_client = MagicMock()
        issue = Issue(client=mock_client)
        mock_response = MagicMock()
        mock_data = {"id": 1, "title": "New Issue"}
        mock_status = 201
        mock_etag = '"test-etag"'
        mock_last_mod = "Wed, 21 Oct 2015 07:28:00 GMT"

        with (
            patch.object(issue, "_create_issue", return_value=mock_response) as mock_private,
            patch(
                "ghnova.issue.issue.process_response_with_last_modified",
                return_value=(mock_data, mock_status, mock_etag, mock_last_mod),
            ) as mock_process,
        ):
            result = issue.create_issue(
                owner="test-owner",
                repository="test-repo",
                title="New Issue",
                body="Description",
            )

            mock_private.assert_called_once_with(
                owner="test-owner",
                repository="test-repo",
                title="New Issue",
                body="Description",
                assignee=None,
                milestone=None,
                labels=None,
                assignees=None,
                issue_type=None,
            )
            mock_process.assert_called_once_with(mock_response)
            assert result == (mock_data, mock_status, mock_etag, mock_last_mod)

    def test_get_issue(self):
        """Test get_issue method."""
        mock_client = MagicMock()
        issue = Issue(client=mock_client)
        mock_response = MagicMock()
        mock_data = {"id": 1, "title": "Test Issue"}
        mock_status = 200
        mock_etag = '"test-etag"'
        mock_last_mod = "Wed, 21 Oct 2015 07:28:00 GMT"

        with (
            patch.object(issue, "_get_issue", return_value=mock_response) as mock_private,
            patch(
                "ghnova.issue.issue.process_response_with_last_modified",
                return_value=(mock_data, mock_status, mock_etag, mock_last_mod),
            ) as mock_process,
        ):
            result = issue.get_issue(
                owner="test-owner",
                repository="test-repo",
                issue_number=1,
                etag='"old-etag"',
                last_modified="Wed, 20 Oct 2015 07:28:00 GMT",
            )

            mock_private.assert_called_once_with(
                owner="test-owner",
                repository="test-repo",
                issue_number=1,
                etag='"old-etag"',
                last_modified="Wed, 20 Oct 2015 07:28:00 GMT",
            )
            mock_process.assert_called_once_with(mock_response)
            assert result == (mock_data, mock_status, mock_etag, mock_last_mod)

    def test_update_issue(self):
        """Test update_issue method."""
        mock_client = MagicMock()
        issue = Issue(client=mock_client)
        mock_response = MagicMock()
        mock_data = {"id": 1, "title": "Updated Issue"}
        mock_status = 200
        mock_etag = '"test-etag"'
        mock_last_mod = "Wed, 21 Oct 2015 07:28:00 GMT"

        with (
            patch.object(issue, "_update_issue", return_value=mock_response) as mock_private,
            patch(
                "ghnova.issue.issue.process_response_with_last_modified",
                return_value=(mock_data, mock_status, mock_etag, mock_last_mod),
            ) as mock_process,
        ):
            result = issue.update_issue(
                owner="test-owner",
                repository="test-repo",
                issue_number=1,
                title="Updated Issue",
                state="closed",
            )

            mock_private.assert_called_once_with(
                owner="test-owner",
                repository="test-repo",
                issue_number=1,
                title="Updated Issue",
                body=None,
                assignee=None,
                milestone=None,
                labels=None,
                assignees=None,
                state="closed",
            )
            mock_process.assert_called_once_with(mock_response)
            assert result == (mock_data, mock_status, mock_etag, mock_last_mod)

    def test_lock_issue(self):
        """Test lock_issue method."""
        mock_client = MagicMock()
        issue = Issue(client=mock_client)
        mock_response = MagicMock()
        mock_data = {"id": 1, "locked": True}
        mock_status = 204
        mock_etag = '"test-etag"'
        mock_last_mod = "Wed, 21 Oct 2015 07:28:00 GMT"

        with (
            patch.object(issue, "_lock_issue", return_value=mock_response) as mock_private,
            patch(
                "ghnova.issue.issue.process_response_with_last_modified",
                return_value=(mock_data, mock_status, mock_etag, mock_last_mod),
            ) as mock_process,
        ):
            result = issue.lock_issue(
                owner="test-owner",
                repository="test-repo",
                issue_number=1,
                lock_reason="off-topic",
            )

            mock_private.assert_called_once_with(
                owner="test-owner",
                repository="test-repo",
                issue_number=1,
                lock_reason="off-topic",
            )
            mock_process.assert_called_once_with(mock_response)
            assert result == (mock_data, mock_status, mock_etag, mock_last_mod)

    def test_unlock_issue(self):
        """Test unlock_issue method."""
        mock_client = MagicMock()
        issue = Issue(client=mock_client)
        mock_response = MagicMock()
        mock_data = {"id": 1, "locked": False}
        mock_status = 204
        mock_etag = '"test-etag"'
        mock_last_mod = "Wed, 21 Oct 2015 07:28:00 GMT"

        with (
            patch.object(issue, "_unlock_issue", return_value=mock_response) as mock_private,
            patch(
                "ghnova.issue.issue.process_response_with_last_modified",
                return_value=(mock_data, mock_status, mock_etag, mock_last_mod),
            ) as mock_process,
        ):
            result = issue.unlock_issue(
                owner="test-owner",
                repository="test-repo",
                issue_number=1,
            )

            mock_private.assert_called_once_with(
                owner="test-owner",
                repository="test-repo",
                issue_number=1,
            )
            mock_process.assert_called_once_with(mock_response)
            assert result == (mock_data, mock_status, mock_etag, mock_last_mod)
