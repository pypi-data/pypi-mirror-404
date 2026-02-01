"""Unit tests for the base user class."""

import pytest

from ghnova.user.base import BaseUser


class TestBaseUser:
    """Test cases for the BaseUser class."""

    def test_get_user_endpoint_authenticated(self):
        """Test _get_user_endpoint for authenticated user."""
        base_user = BaseUser()
        endpoint = base_user._get_user_endpoint(username=None, account_id=None)
        assert endpoint == "/user"

    def test_get_user_endpoint_by_username(self):
        """Test _get_user_endpoint by username."""
        base_user = BaseUser()
        endpoint = base_user._get_user_endpoint(username="octocat", account_id=None)
        assert endpoint == "/users/octocat"

    def test_get_user_endpoint_by_account_id(self):
        """Test _get_user_endpoint by account ID."""
        base_user = BaseUser()
        endpoint = base_user._get_user_endpoint(username=None, account_id=123)
        assert endpoint == "/user/123"

    def test_get_user_endpoint_both_specified(self):
        """Test _get_user_endpoint with both username and account_id raises error."""
        base_user = BaseUser()
        with pytest.raises(ValueError, match=r"Specify either username or account_id, not both."):
            base_user._get_user_endpoint(username="octocat", account_id=123)

    def test_get_user_helper_authenticated(self):
        """Test _get_user_helper for authenticated user."""
        base_user = BaseUser()
        endpoint, kwargs = base_user._get_user_helper(username=None, account_id=None)
        assert endpoint == "/user"
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_get_user_helper_by_username(self):
        """Test _get_user_helper by username."""
        base_user = BaseUser()
        endpoint, kwargs = base_user._get_user_helper(username="octocat", account_id=None)
        assert endpoint == "/users/octocat"
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_get_user_helper_with_additional_headers(self):
        """Test _get_user_helper with additional headers."""
        base_user = BaseUser()
        endpoint, kwargs = base_user._get_user_helper(username="octocat", headers={"Authorization": "Bearer token"})
        assert endpoint == "/users/octocat"
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer token",
        }

    def test_update_user_endpoint(self):
        """Test _update_user_endpoint."""
        base_user = BaseUser()
        endpoint = base_user._update_user_endpoint()
        assert endpoint == "/user"

    def test_update_user_helper(self):
        """Test _update_user_helper with all parameters."""
        base_user = BaseUser()
        endpoint, payload, kwargs = base_user._update_user_helper(
            name="John Doe",
            email="john@example.com",
            blog="https://blog.example.com",
            twitter_username="john_doe",
            company="Example Inc",
            location="San Francisco",
            hireable=True,
            bio="Software Engineer",
        )
        assert endpoint == "/user"
        assert payload == {
            "name": "John Doe",
            "email": "john@example.com",
            "blog": "https://blog.example.com",
            "twitter_username": "john_doe",
            "company": "Example Inc",
            "location": "San Francisco",
            "hireable": True,
            "bio": "Software Engineer",
        }
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_update_user_helper_partial(self):
        """Test _update_user_helper with partial parameters."""
        base_user = BaseUser()
        endpoint, payload, kwargs = base_user._update_user_helper(
            name="Jane Doe",
            email=None,
            blog=None,
            twitter_username=None,
            company=None,
            location=None,
            hireable=False,
            bio=None,
        )
        assert endpoint == "/user"
        assert payload == {
            "name": "Jane Doe",
            "hireable": False,
        }
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_update_user_helper_with_additional_headers(self):
        """Test _update_user_helper with additional headers."""
        base_user = BaseUser()
        endpoint, payload, kwargs = base_user._update_user_helper(
            name="John Doe",
            email="john@example.com",
            blog=None,
            twitter_username=None,
            company=None,
            location=None,
            hireable=None,
            bio=None,
            headers={"Authorization": "Bearer token"},
        )
        assert endpoint == "/user"
        assert payload == {
            "name": "John Doe",
            "email": "john@example.com",
        }
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer token",
        }

    def test_list_users_endpoint(self):
        """Test _list_users_endpoint."""
        base_user = BaseUser()
        endpoint = base_user._list_users_endpoint()
        assert endpoint == "/users"

    def test_list_users_helper(self):
        """Test _list_users_helper with parameters."""
        base_user = BaseUser()
        endpoint, params, kwargs = base_user._list_users_helper(since=100, per_page=50)
        assert endpoint == "/users"
        assert params == {"since": 100, "per_page": 50}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_list_users_helper_no_params(self):
        """Test _list_users_helper without parameters."""
        base_user = BaseUser()
        endpoint, params, kwargs = base_user._list_users_helper(since=None, per_page=None)
        assert endpoint == "/users"
        assert params == {}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_list_users_helper_with_additional_headers(self):
        """Test _list_users_helper with additional headers."""
        base_user = BaseUser()
        endpoint, params, kwargs = base_user._list_users_helper(
            since=200, per_page=25, headers={"Authorization": "Bearer token"}
        )
        assert endpoint == "/users"
        assert params == {"since": 200, "per_page": 25}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer token",
        }

    def test_get_contextual_information_endpoint(self):
        """Test _get_contextual_information_endpoint."""
        base_user = BaseUser()
        endpoint = base_user._get_contextual_information_endpoint()
        assert endpoint == "/users/{username}/hovercard"

    def test_get_contextual_information_helper(self):
        """Test _get_contextual_information_helper with parameters."""
        base_user = BaseUser()
        endpoint, params, kwargs = base_user._get_contextual_information_helper(
            username="octocat", subject_type="repository", subject_id="123"
        )
        assert endpoint == "/users/octocat/hovercard"
        assert params == {"subject_type": "repository", "subject_id": "123"}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_get_contextual_information_helper_no_optional(self):
        """Test _get_contextual_information_helper without optional parameters."""
        base_user = BaseUser()
        endpoint, params, kwargs = base_user._get_contextual_information_helper(
            username="octocat", subject_type=None, subject_id=None
        )
        assert endpoint == "/users/octocat/hovercard"
        assert params == {}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_get_contextual_information_helper_with_additional_headers(self):
        """Test _get_contextual_information_helper with additional headers."""
        base_user = BaseUser()
        endpoint, params, kwargs = base_user._get_contextual_information_helper(
            username="octocat",
            subject_type="issue",
            subject_id="456",
            headers={"Authorization": "Bearer token"},
        )
        assert endpoint == "/users/octocat/hovercard"
        assert params == {"subject_type": "issue", "subject_id": "456"}
        assert kwargs["headers"] == {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer token",
        }
