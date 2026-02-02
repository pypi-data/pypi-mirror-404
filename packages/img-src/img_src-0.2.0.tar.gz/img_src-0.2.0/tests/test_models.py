"""Tests for new and modified models added in the latest OpenAPI sync."""

from datetime import datetime, timezone

import img_src.models as models
from img_src.models import (
    ActiveSignedUrl,
    Credits,
    DeletePresetRequest,
    ImageListItem,
    MetadataResponse,
    SearchResult,
    UpdateVisibilityRequest,
    UpdateVisibilityRequestBody,
    UpdateVisibilityResponse,
    UpdateVisibilityResponse1,
    UploadImageRequestBody,
    UploadResponse,
    UsageResponse,
    Visibility,
)


# ---------------------------------------------------------------------------
# 1. New model creation tests
# ---------------------------------------------------------------------------


class TestActiveSignedUrl:
    def test_creation(self):
        url = ActiveSignedUrl(
            signed_url="https://cdn.example.com/signed/abc?token=xyz",
            expires_at=1700000000,
        )
        assert url.signed_url == "https://cdn.example.com/signed/abc?token=xyz"
        assert url.expires_at == 1700000000


class TestCredits:
    def test_creation(self):
        credits = Credits(storage_bytes=1024, api_requests=100, transformations=50)
        assert credits.storage_bytes == 1024
        assert credits.api_requests == 100
        assert credits.transformations == 50


class TestVisibility:
    def test_public_value(self):
        v: Visibility = "public"
        assert v == "public"

    def test_private_value(self):
        v: Visibility = "private"
        assert v == "private"


class TestUpdateVisibilityResponse:
    def test_creation(self):
        resp = UpdateVisibilityResponse(
            id="abc123",
            visibility="public",
            message="Visibility updated",
        )
        assert resp.id == "abc123"
        assert resp.visibility == "public"
        assert resp.message == "Visibility updated"


class TestUpdateVisibilityRequestBody:
    def test_creation(self):
        body = UpdateVisibilityRequestBody(visibility="private")
        assert body.visibility == "private"


class TestUpdateVisibilityRequest:
    def test_creation(self):
        req = UpdateVisibilityRequest(
            id="img-123",
            body=UpdateVisibilityRequestBody(visibility="public"),
        )
        assert req.id == "img-123"
        assert req.body is not None
        assert req.body.visibility == "public"


class TestUpdateVisibilityResponse1:
    def test_creation(self):
        inner = UpdateVisibilityResponse(
            id="abc", visibility="private", message="done"
        )
        resp = UpdateVisibilityResponse1(update_visibility_response=inner)
        assert resp.update_visibility_response is not None
        assert resp.update_visibility_response.id == "abc"


# ---------------------------------------------------------------------------
# 2. Modified models — visibility field
# ---------------------------------------------------------------------------


class TestUploadResponseVisibility:
    def test_has_visibility(self):
        """UploadResponse includes the required visibility field."""
        assert "visibility" in UploadResponse.model_fields


class TestImageListItemVisibility:
    def test_has_visibility(self):
        item = ImageListItem(
            id="img-1",
            original_filename="photo.jpg",
            size=1024,
            uploaded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            url="http://test.local/api/v1/images/img-1",
            paths=["/photos/photo.jpg"],
            visibility="public",
        )
        assert item.visibility == "public"


class TestSearchResultVisibility:
    def test_has_visibility(self):
        result = SearchResult(
            id="img-2",
            original_filename="pic.png",
            paths=["/pics/pic.png"],
            size=2048,
            uploaded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            url="http://test.local/api/v1/images/img-2",
            visibility="private",
        )
        assert result.visibility == "private"


class TestMetadataResponseVisibility:
    def test_has_visibility(self):
        assert "visibility" in MetadataResponse.model_fields


# ---------------------------------------------------------------------------
# 3. Optional fields — active_signed_url, credits
# ---------------------------------------------------------------------------


class TestImageListItemActiveSignedUrl:
    def test_optional_none(self):
        item = ImageListItem(
            id="img-1",
            original_filename="photo.jpg",
            size=1024,
            uploaded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            url="http://test.local/api/v1/images/img-1",
            paths=["/photos/photo.jpg"],
            visibility="public",
        )
        assert item.active_signed_url is None

    def test_present(self):
        signed = ActiveSignedUrl(
            signed_url="https://example.com/signed", expires_at=9999999999
        )
        item = ImageListItem(
            id="img-1",
            original_filename="photo.jpg",
            size=1024,
            uploaded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            url="http://test.local/api/v1/images/img-1",
            paths=["/photos/photo.jpg"],
            visibility="private",
            active_signed_url=signed,
        )
        assert item.active_signed_url is not None
        assert item.active_signed_url.signed_url == "https://example.com/signed"


class TestUsageResponseCredits:
    def test_has_credits_field(self):
        assert "credits" in UsageResponse.model_fields


class TestUploadRequestBodyVisibility:
    def test_optional_none(self):
        body = UploadImageRequestBody()
        assert body.visibility is None

    def test_with_value(self):
        body = UploadImageRequestBody(visibility="private")
        assert body.visibility == "private"


# ---------------------------------------------------------------------------
# 4. DeletePreset uses name parameter
# ---------------------------------------------------------------------------


class TestDeletePresetRequest:
    def test_uses_name(self):
        req = DeletePresetRequest(name="thumbnail")
        assert req.name == "thumbnail"

    def test_no_id_field(self):
        assert "id" not in DeletePresetRequest.model_fields


# ---------------------------------------------------------------------------
# 5. Module exports
# ---------------------------------------------------------------------------

NEW_SYMBOLS = [
    "ActiveSignedUrl",
    "ActiveSignedUrlTypedDict",
    "Credits",
    "CreditsTypedDict",
    "Visibility",
    "UpdateVisibilityRequest",
    "UpdateVisibilityRequestTypedDict",
    "UpdateVisibilityRequestBody",
    "UpdateVisibilityRequestBodyTypedDict",
    "UpdateVisibilityResponse",
    "UpdateVisibilityResponseTypedDict",
    "UpdateVisibilityResponse1",
    "UpdateVisibilityResponse1TypedDict",
]


class TestModuleExports:
    def test_all_new_symbols_importable(self):
        for symbol in NEW_SYMBOLS:
            obj = getattr(models, symbol)
            assert obj is not None, f"{symbol} not importable from img_src.models"

    def test_new_symbols_in_all(self):
        for symbol in NEW_SYMBOLS:
            assert symbol in models.__all__, f"{symbol} not in models.__all__"


# ---------------------------------------------------------------------------
# 6. Serialization
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_image_list_item_excludes_none_optionals(self):
        item = ImageListItem(
            id="img-1",
            original_filename="photo.jpg",
            size=1024,
            uploaded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            url="http://test.local/api/v1/images/img-1",
            paths=["/photos/photo.jpg"],
            visibility="public",
        )
        data = item.model_dump()
        assert "active_signed_url" not in data
        assert "sanitized_filename" not in data
        assert "cdn_url" not in data

    def test_image_list_item_includes_present_optionals(self):
        signed = ActiveSignedUrl(
            signed_url="https://example.com/signed", expires_at=9999999999
        )
        item = ImageListItem(
            id="img-1",
            original_filename="photo.jpg",
            size=1024,
            uploaded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            url="http://test.local/api/v1/images/img-1",
            paths=["/photos/photo.jpg"],
            visibility="private",
            active_signed_url=signed,
            cdn_url="https://cdn.example.com/photo.jpg",
        )
        data = item.model_dump()
        assert "active_signed_url" in data
        assert data["active_signed_url"]["signed_url"] == "https://example.com/signed"
        assert "cdn_url" in data

    def test_update_visibility_request_serialization(self):
        req = UpdateVisibilityRequest(
            id="img-123",
            body=UpdateVisibilityRequestBody(visibility="public"),
        )
        data = req.model_dump()
        assert data["id"] == "img-123"
        assert data["body"]["visibility"] == "public"

    def test_upload_request_body_serialization_with_visibility(self):
        body = UploadImageRequestBody(visibility="private")
        data = body.model_dump()
        assert data["visibility"] == "private"

    def test_upload_request_body_serialization_without_visibility(self):
        body = UploadImageRequestBody()
        data = body.model_dump()
        assert "visibility" not in data
