"""Unit tests for the synchronous Resource base class."""

from unittest.mock import MagicMock

from ghnova.resource.resource import Resource


class TestResource:
    """Test cases for the Resource class."""

    def test_init(self):
        """Test initialization."""
        mock_client = MagicMock()
        resource = Resource(client=mock_client)
        assert resource.client == mock_client

    def test_get(self):
        """Test _get method."""
        mock_client = MagicMock()
        resource = Resource(client=mock_client)
        mock_response = MagicMock()
        mock_client._request.return_value = mock_response

        result = resource._get("/test", some_kwarg="value")

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="GET", endpoint="/test", some_kwarg="value")

    def test_post(self):
        """Test _post method."""
        mock_client = MagicMock()
        resource = Resource(client=mock_client)
        mock_response = MagicMock()
        mock_client._request.return_value = mock_response

        result = resource._post("/test", data="payload")

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="POST", endpoint="/test", data="payload")

    def test_put(self):
        """Test _put method."""
        mock_client = MagicMock()
        resource = Resource(client=mock_client)
        mock_response = MagicMock()
        mock_client._request.return_value = mock_response

        result = resource._put("/test", json={"key": "value"})

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="PUT", endpoint="/test", json={"key": "value"})

    def test_delete(self):
        """Test _delete method."""
        mock_client = MagicMock()
        resource = Resource(client=mock_client)
        mock_response = MagicMock()
        mock_client._request.return_value = mock_response

        result = resource._delete("/test")

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="DELETE", endpoint="/test")

    def test_patch(self):
        """Test _patch method."""
        mock_client = MagicMock()
        resource = Resource(client=mock_client)
        mock_response = MagicMock()
        mock_client._request.return_value = mock_response

        result = resource._patch("/test", headers={"custom": "header"})

        assert result == mock_response
        mock_client._request.assert_called_once_with(method="PATCH", endpoint="/test", headers={"custom": "header"})
