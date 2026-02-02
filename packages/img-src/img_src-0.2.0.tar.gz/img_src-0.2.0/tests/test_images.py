"""Tests for the Images.update_visibility resource method."""

import pytest
import pytest_asyncio

from img_src import errors
from img_src.models import UpdateVisibilityResponse1
from tests.conftest import make_mock_response


class TestUpdateVisibility:
    def test_success(self, make_sdk, mock_client):
        mock_client.response = make_mock_response(200, {
            "id": "img-123",
            "visibility": "private",
            "message": "Visibility updated to private",
        })

        result = make_sdk.images.update_visibility(id="img-123", visibility="private")

        assert isinstance(result, UpdateVisibilityResponse1)
        assert result.update_visibility_response is not None
        assert result.update_visibility_response.id == "img-123"
        assert result.update_visibility_response.visibility == "private"
        assert result.update_visibility_response.message == "Visibility updated to private"

    def test_request_method_and_path(self, make_sdk, mock_client):
        mock_client.response = make_mock_response(200, {
            "id": "img-456",
            "visibility": "public",
            "message": "Visibility updated",
        })

        make_sdk.images.update_visibility(id="img-456", visibility="public")

        assert mock_client.last_request is not None
        assert mock_client.last_request.method == "PATCH"
        assert "/api/v1/images/img-456/visibility" in str(mock_client.last_request.url)

    def test_error_401(self, make_sdk, mock_client):
        mock_client.response = make_mock_response(401, {
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid API key",
                "status": 401,
            },
        })

        with pytest.raises(errors.ErrorResponse):
            make_sdk.images.update_visibility(id="img-123", visibility="private")

    def test_error_404(self, make_sdk, mock_client):
        mock_client.response = make_mock_response(404, {
            "error": {
                "code": "NOT_FOUND",
                "message": "Image not found",
                "status": 404,
            },
        })

        with pytest.raises(errors.ErrorResponse):
            make_sdk.images.update_visibility(id="nonexistent", visibility="private")


class TestUpdateVisibilityAsync:
    @pytest.mark.asyncio
    async def test_success(self, make_sdk, mock_async_client):
        mock_async_client.response = make_mock_response(200, {
            "id": "img-789",
            "visibility": "public",
            "message": "Visibility updated to public",
        })

        result = await make_sdk.images.update_visibility_async(
            id="img-789", visibility="public"
        )

        assert isinstance(result, UpdateVisibilityResponse1)
        assert result.update_visibility_response is not None
        assert result.update_visibility_response.id == "img-789"
        assert result.update_visibility_response.visibility == "public"
