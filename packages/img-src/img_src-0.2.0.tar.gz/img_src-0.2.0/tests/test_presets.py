"""Tests for the Presets.delete_preset resource method with name parameter."""

import pytest

from img_src import errors
from img_src.models import DeletePresetResponse1
from tests.conftest import make_mock_response


class TestDeletePreset:
    def test_uses_name_param(self, make_sdk, mock_client):
        mock_client.response = make_mock_response(200, {
            "success": True,
            "message": "Preset deleted",
        })

        result = make_sdk.presets.delete_preset(name="thumbnail")

        assert isinstance(result, DeletePresetResponse1)
        assert result.delete_preset_response is not None
        assert result.delete_preset_response.success is True

    def test_path_contains_name(self, make_sdk, mock_client):
        mock_client.response = make_mock_response(200, {
            "success": True,
            "message": "Preset deleted",
        })

        make_sdk.presets.delete_preset(name="my-preset")

        assert mock_client.last_request is not None
        assert mock_client.last_request.method == "DELETE"
        assert "/api/v1/settings/presets/my-preset" in str(mock_client.last_request.url)

    def test_success_response(self, make_sdk, mock_client):
        mock_client.response = make_mock_response(200, {
            "success": True,
            "message": "Preset 'avatar' has been deleted",
        })

        result = make_sdk.presets.delete_preset(name="avatar")

        assert result.delete_preset_response is not None
        assert result.delete_preset_response.message == "Preset 'avatar' has been deleted"

    def test_error_404(self, make_sdk, mock_client):
        mock_client.response = make_mock_response(404, {
            "error": {
                "code": "NOT_FOUND",
                "message": "Preset not found",
                "status": 404,
            },
        })

        with pytest.raises(errors.ErrorResponse):
            make_sdk.presets.delete_preset(name="nonexistent")


class TestDeletePresetAsync:
    @pytest.mark.asyncio
    async def test_uses_name_param(self, make_sdk, mock_async_client):
        mock_async_client.response = make_mock_response(200, {
            "success": True,
            "message": "Preset deleted",
        })

        result = await make_sdk.presets.delete_preset_async(name="thumbnail")

        assert isinstance(result, DeletePresetResponse1)
        assert result.delete_preset_response is not None
        assert result.delete_preset_response.success is True
