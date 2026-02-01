"""Smoke tests for the HeyGen MCP server tools.

These tests verify that the MCP server tools work correctly
by calling them directly with the resource-based API pattern.
Requires HEYGEN_API_KEY environment variable to be set.
"""

import pytest

from heygen_mcp.server import (
    assets,
    avatars,
    reset_api_client,
    templates,
    user,
    videos,
    voices,
)


@pytest.fixture(autouse=True)
async def cleanup_api_client():
    """Reset the API client singleton between tests to avoid event loop issues."""
    yield
    # Clean up after test
    await reset_api_client()


class TestUserTool:
    """Smoke tests for the user resource tool."""

    @pytest.mark.asyncio
    async def test_user_info_action(self):
        """Test user(action='info') returns user profile."""
        result = await user(action="info")

        assert result.error is None, f"Tool returned error: {result.error}"
        assert result.username is not None or result.email is not None
        print(f"\n  User: {result.username} ({result.email})")

    @pytest.mark.asyncio
    async def test_user_credits_action(self):
        """Test user(action='credits') returns remaining credits."""
        result = await user(action="credits")

        assert result.error is None, f"Tool returned error: {result.error}"
        assert result.remaining_credits is not None
        assert result.remaining_credits >= 0
        print(f"\n  Remaining credits: {result.remaining_credits}")


class TestVoicesTool:
    """Smoke tests for the voices resource tool."""

    @pytest.mark.asyncio
    async def test_voices_list_action(self):
        """Test voices(action='list') returns available voices."""
        result = await voices(action="list")

        assert result.error is None, f"Tool returned error: {result.error}"
        assert result.voices is not None
        assert len(result.voices) > 0
        print(f"\n  Found {len(result.voices)} voices")
        print(f"  First voice: {result.voices[0].name}")


class TestAvatarsTool:
    """Smoke tests for the avatars resource tool."""

    @pytest.mark.asyncio
    async def test_avatars_list_action(self):
        """Test avatars(action='list') returns all avatars."""
        result = await avatars(action="list")

        assert result.error is None, f"Tool returned error: {result.error}"
        assert result.avatars is not None
        assert result.total_count >= 0
        print(f"\n  Found {result.total_count} avatars")

    @pytest.mark.asyncio
    async def test_avatars_get_action(self):
        """Test avatars(action='get') returns avatar details."""
        # First get an avatar ID
        list_result = await avatars(action="list")
        if not list_result.avatars:
            pytest.skip("No avatars available")

        avatar_id = list_result.avatars[0].avatar_id
        result = await avatars(action="get", avatar_id=avatar_id)

        assert result.error is None, f"Tool returned error: {result.error}"
        assert result.avatar is not None
        assert result.avatar.avatar_id == avatar_id
        print(f"\n  Avatar: {result.avatar.avatar_name}")

    @pytest.mark.asyncio
    async def test_avatars_get_action_missing_id(self):
        """Test avatars(action='get') without avatar_id returns error."""
        result = await avatars(action="get")

        assert result.error is not None
        assert "avatar_id is required" in result.error

    @pytest.mark.asyncio
    async def test_avatars_list_groups_action(self):
        """Test avatars(action='list_groups') returns avatar groups."""
        result = await avatars(action="list_groups", include_public=True)

        assert result.error is None, f"Tool returned error: {result.error}"
        assert result.total_count is not None
        print(f"\n  Found {result.total_count} avatar groups")

    @pytest.mark.asyncio
    async def test_avatars_list_in_group_action(self):
        """Test avatars(action='list_in_group') returns avatars in a group."""
        # First get a group ID
        groups_result = await avatars(action="list_groups", include_public=True)
        if not groups_result.avatar_groups:
            pytest.skip("No avatar groups available")

        group_id = groups_result.avatar_groups[0].id
        result = await avatars(action="list_in_group", group_id=group_id)

        assert result.error is None, f"Tool returned error: {result.error}"
        avatar_count = len(result.avatars) if result.avatars else 0
        print(f"\n  Found {avatar_count} avatars in group {group_id}")

    @pytest.mark.asyncio
    async def test_avatars_list_in_group_missing_id(self):
        """Test avatars(action='list_in_group') without group_id returns error."""
        result = await avatars(action="list_in_group")

        assert result.error is not None
        assert "group_id is required" in result.error


class TestVideosTool:
    """Smoke tests for the videos resource tool."""

    @pytest.mark.asyncio
    async def test_videos_list_action(self):
        """Test videos(action='list') returns video list."""
        result = await videos(action="list")

        assert result.error is None, f"Tool returned error: {result.error}"
        assert result.videos is not None
        assert result.total is not None
        assert result.total >= 0
        print(f"\n  Found {result.total} videos")
        if result.videos:
            vid = result.videos[0]
            print(f"  First video: {vid.video_id} ({vid.status})")

    @pytest.mark.asyncio
    async def test_videos_status_action(self):
        """Test videos(action='status') with invalid ID."""
        result = await videos(action="status", video_id="invalid-video-id")

        # Should return an error or specific status for invalid ID
        print(f"\n  Status result: error={result.error}, status={result.status}")

    @pytest.mark.asyncio
    async def test_videos_status_action_missing_id(self):
        """Test videos(action='status') without video_id returns error."""
        result = await videos(action="status")

        assert result.error is not None
        assert "video_id is required" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_action_missing_params(self):
        """Test videos(action='generate') without video_inputs_json returns error."""
        result = await videos(action="generate")

        assert result.error is not None
        assert "video_inputs_json is required" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_action_invalid_json(self):
        """Test videos(action='generate') with invalid JSON returns error."""
        result = await videos(action="generate", video_inputs_json="not valid json")

        assert result.error is not None
        assert "Invalid JSON" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_action_empty_array(self):
        """Test videos(action='generate') with empty array returns error."""
        result = await videos(action="generate", video_inputs_json="[]")

        assert result.error is not None
        assert "at least one scene" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_action_missing_avatar(self):
        """Test videos(action='generate') without avatar_id in scene returns error."""
        result = await videos(
            action="generate",
            video_inputs_json='[{"voice": {"input_text": "Hello", "voice_id": "v1"}}]',
        )

        assert result.error is not None
        assert "character.avatar_id is required" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_action_missing_voice_text(self):
        """Test videos(action='generate') without input_text in scene returns error."""
        json_input = '[{"character": {"avatar_id": "a1"}, "voice": {"voice_id": "v1"}}]'
        result = await videos(
            action="generate",
            video_inputs_json=json_input,
        )

        assert result.error is not None
        assert "voice.input_text is required" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_action_missing_voice_id(self):
        """Test videos(action='generate') without voice_id in scene returns error."""
        json_input = (
            '[{"character": {"avatar_id": "a1"}, "voice": {"input_text": "Hello"}}]'
        )
        result = await videos(
            action="generate",
            video_inputs_json=json_input,
        )

        assert result.error is not None
        assert "voice.voice_id is required" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_iv_action_missing_image_key(self):
        """Test videos(action='generate_iv') without image_key returns error."""
        result = await videos(action="generate_iv")

        assert result.error is not None
        assert "image_key is required" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_iv_action_missing_script(self):
        """Test videos(action='generate_iv') without script returns error."""
        result = await videos(action="generate_iv", image_key="test-image")

        assert result.error is not None
        assert "script is required" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_iv_action_missing_voice_id(self):
        """Test videos(action='generate_iv') without voice_id returns error."""
        result = await videos(
            action="generate_iv", image_key="test-image", script="Hello world"
        )

        assert result.error is not None
        assert "voice_id is required" in result.error

    @pytest.mark.asyncio
    async def test_videos_generate_iv_action_missing_video_title(self):
        """Test videos(action='generate_iv') without video_title returns error."""
        result = await videos(
            action="generate_iv",
            image_key="test-image",
            script="Hello world",
            voice_id="test-voice",
        )

        assert result.error is not None
        assert "video_title is required" in result.error


class TestTemplatesTool:
    """Smoke tests for the templates resource tool."""

    @pytest.mark.asyncio
    async def test_templates_list_action(self):
        """Test templates(action='list') returns templates."""
        result = await templates(action="list")

        assert result.error is None, f"Tool returned error: {result.error}"
        print(f"\n  Found {result.total_count} templates")

    @pytest.mark.asyncio
    async def test_templates_get_action_missing_id(self):
        """Test templates(action='get') without template_id returns error."""
        result = await templates(action="get")

        assert result.error is not None
        assert "template_id is required" in result.error

    @pytest.mark.asyncio
    async def test_templates_generate_action_missing_id(self):
        """Test templates(action='generate') without template_id returns error."""
        result = await templates(action="generate")

        assert result.error is not None
        assert "template_id is required" in result.error

    @pytest.mark.asyncio
    async def test_templates_get_action_invalid_id(self):
        """Test templates(action='get') with invalid template_id."""
        result = await templates(action="get", template_id="invalid-template-id")

        # Should return an error for invalid template
        print(f"\n  Result for invalid ID: error={result.error}")


class TestAssetsTool:
    """Smoke tests for the assets resource tool."""

    @pytest.mark.asyncio
    async def test_assets_list_action(self):
        """Test assets(action='list') returns assets."""
        result = await assets(action="list")

        assert result.error is None, f"Tool returned error: {result.error}"
        asset_count = len(result.assets) if result.assets else 0
        print(f"\n  Found {asset_count} assets")

    @pytest.mark.asyncio
    async def test_assets_upload_action_missing_path(self):
        """Test assets(action='upload') without file_path returns error."""
        result = await assets(action="upload")

        assert result.error is not None
        assert "file_path is required" in result.error

    @pytest.mark.asyncio
    async def test_assets_delete_action_missing_id(self):
        """Test assets(action='delete') without asset_id returns error."""
        result = await assets(action="delete")

        assert result.error is not None
        assert "asset_id is required" in result.error


class TestFoldersTool:
    """Smoke tests for the folders resource tool."""

    @pytest.mark.asyncio
    async def test_folders_list_action(self):
        """Test folders(action='list') returns folders."""
        from heygen_mcp.server import folders

        result = await folders(action="list")

        assert result.error is None, f"Tool returned error: {result.error}"
        folder_count = result.total if result.total else 0
        print(f"\n  Found {folder_count} folders")

    @pytest.mark.asyncio
    async def test_folders_create_action_missing_name(self):
        """Test folders(action='create') without name returns error."""
        from heygen_mcp.server import folders

        result = await folders(action="create")

        assert result.error is not None
        assert "name is required" in result.error

    @pytest.mark.asyncio
    async def test_folders_rename_action_missing_id(self):
        """Test folders(action='rename') without folder_id returns error."""
        from heygen_mcp.server import folders

        result = await folders(action="rename", name="New Name")

        assert result.error is not None
        assert "folder_id is required" in result.error

    @pytest.mark.asyncio
    async def test_folders_rename_action_missing_name(self):
        """Test folders(action='rename') without name returns error."""
        from heygen_mcp.server import folders

        result = await folders(action="rename", folder_id="some-id")

        assert result.error is not None
        assert "name is required" in result.error

    @pytest.mark.asyncio
    async def test_folders_trash_action_missing_id(self):
        """Test folders(action='trash') without folder_id returns error."""
        from heygen_mcp.server import folders

        result = await folders(action="trash")

        assert result.error is not None
        assert "folder_id is required" in result.error

    @pytest.mark.asyncio
    async def test_folders_restore_action_missing_id(self):
        """Test folders(action='restore') without folder_id returns error."""
        from heygen_mcp.server import folders

        result = await folders(action="restore")

        assert result.error is not None
        assert "folder_id is required" in result.error
