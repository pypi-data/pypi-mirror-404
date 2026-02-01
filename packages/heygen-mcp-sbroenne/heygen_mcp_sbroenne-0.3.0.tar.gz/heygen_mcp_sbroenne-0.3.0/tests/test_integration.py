"""Integration tests for the HeyGen API client.

These tests make real API calls to the HeyGen API.
Requires HEYGEN_API_KEY environment variable to be set.
"""

import pytest

from heygen_mcp.client import HeyGenApiClient
from heygen_mcp.models import (
    MCPAssetDeleteResponse,
    MCPAssetListResponse,
    MCPAssetUploadResponse,
    MCPAvatarDetailsResponse,
    MCPAvatarGroupResponse,
    MCPAvatarIVVideoResponse,
    MCPAvatarsInGroupResponse,
    MCPFolderCreateResponse,
    MCPFolderListResponse,
    MCPFolderRestoreResponse,
    MCPFolderTrashResponse,
    MCPFolderUpdateResponse,
    MCPGetCreditsResponse,
    MCPListAvatarsResponse,
    MCPListTemplatesResponse,
    MCPTemplateDetailsResponse,
    MCPTemplateVideoGenerateResponse,
    MCPUserInfoResponse,
    MCPVideoGenerateResponse,
    MCPVideoListResponse,
    MCPVideoStatusResponse,
    MCPVoicesResponse,
)


class TestGetRemainingCredits:
    """Integration tests for get_remaining_credits."""

    @pytest.mark.asyncio
    async def test_get_remaining_credits(self, api_client: HeyGenApiClient):
        """Test retrieving remaining credits from the API."""
        result = await api_client.get_remaining_credits()

        assert isinstance(result, MCPGetCreditsResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.remaining_credits is not None
        assert result.remaining_credits >= 0
        print(f"\n  Remaining credits: {result.remaining_credits}")


class TestGetVoices:
    """Integration tests for get_voices."""

    @pytest.mark.asyncio
    async def test_get_voices(self, api_client: HeyGenApiClient):
        """Test retrieving available voices from the API."""
        result = await api_client.get_voices()

        assert isinstance(result, MCPVoicesResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.voices is not None
        assert len(result.voices) > 0
        print(f"\n  Found {len(result.voices)} voices")

        # Check first voice has expected fields
        first_voice = result.voices[0]
        assert first_voice.voice_id is not None
        assert first_voice.name is not None
        assert first_voice.language is not None
        print(f"  First voice: {first_voice.name} ({first_voice.language})")


class TestAvatarGroups:
    """Integration tests for avatar group operations."""

    @pytest.mark.asyncio
    async def test_list_avatar_groups_private(self, api_client: HeyGenApiClient):
        """Test listing private avatar groups."""
        result = await api_client.list_avatar_groups(include_public=False)

        assert isinstance(result, MCPAvatarGroupResponse)
        assert result.error is None, f"API returned error: {result.error}"
        # Private groups may be empty, that's okay
        print(f"\n  Found {result.total_count} private avatar groups")

    @pytest.mark.asyncio
    async def test_list_avatar_groups_with_public(self, api_client: HeyGenApiClient):
        """Test listing avatar groups including public ones."""
        result = await api_client.list_avatar_groups(include_public=True)

        assert isinstance(result, MCPAvatarGroupResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.avatar_groups is not None
        assert result.total_count is not None
        assert result.total_count >= 0
        print(f"\n  Found {result.total_count} total avatar groups (including public)")

        if result.avatar_groups and len(result.avatar_groups) > 0:
            first_group = result.avatar_groups[0]
            assert first_group.id is not None
            assert first_group.name is not None
            print(f"  First group: {first_group.name} (id: {first_group.id})")


class TestAvatarsInGroup:
    """Integration tests for getting avatars in a group."""

    @pytest.mark.asyncio
    async def test_get_avatars_in_group(self, api_client: HeyGenApiClient):
        """Test retrieving avatars from a specific group."""
        # First get a group to use
        groups_result = await api_client.list_avatar_groups(include_public=True)

        if not groups_result.avatar_groups or len(groups_result.avatar_groups) == 0:
            pytest.skip("No avatar groups available to test")

        group_id = groups_result.avatar_groups[0].id
        result = await api_client.get_avatars_in_group(group_id)

        assert isinstance(result, MCPAvatarsInGroupResponse)
        assert result.error is None, f"API returned error: {result.error}"
        avatar_count = len(result.avatars) if result.avatars else 0
        print(f"\n  Found {avatar_count} avatars in group {group_id}")

        if result.avatars and len(result.avatars) > 0:
            first_avatar = result.avatars[0]
            assert first_avatar.avatar_id is not None
            assert first_avatar.avatar_name is not None
            print(f"  First avatar: {first_avatar.avatar_name}")
            print(f"    ID: {first_avatar.avatar_id}")


class TestVideoGeneration:
    """Integration tests for video generation.

    Note: These tests are marked with a special marker because they
    consume API credits. Run with: pytest -m "video_generation"
    """

    @pytest.mark.asyncio
    @pytest.mark.video_generation
    async def test_generate_and_check_video_status(self, api_client: HeyGenApiClient):
        """Test generating a video and checking its status.

        WARNING: This test consumes API credits!
        """
        from heygen_mcp.models import (
            Character,
            Dimension,
            VideoGenerateRequest,
            VideoInput,
            Voice,
        )

        # First, get an avatar and voice to use
        groups_result = await api_client.list_avatar_groups(include_public=True)
        if not groups_result.avatar_groups:
            pytest.skip("No avatar groups available")

        avatars_result = await api_client.get_avatars_in_group(
            groups_result.avatar_groups[0].id
        )
        if not avatars_result.avatars:
            pytest.skip("No avatars available in group")

        voices_result = await api_client.get_voices()
        if not voices_result.voices:
            pytest.skip("No voices available")

        avatar_id = avatars_result.avatars[0].avatar_id
        voice_id = voices_result.voices[0].voice_id

        # Create video generation request
        request = VideoGenerateRequest(
            title="Integration Test Video",
            video_inputs=[
                VideoInput(
                    character=Character(avatar_id=avatar_id),
                    voice=Voice(
                        input_text="Hello, this is an integration test.",
                        voice_id=voice_id,
                    ),
                )
            ],
            dimension=Dimension(width=1280, height=720),
            test=True,  # Use test mode if available
        )

        # Generate video
        generate_result = await api_client.generate_avatar_video(request)

        assert isinstance(generate_result, MCPVideoGenerateResponse)
        err = generate_result.error
        assert err is None, f"API returned error: {err}"
        assert generate_result.video_id is not None
        print(f"\n  Generated video ID: {generate_result.video_id}")

        # Check video status
        status_result = await api_client.get_video_status(generate_result.video_id)

        assert isinstance(status_result, MCPVideoStatusResponse)
        assert status_result.error is None, f"API returned error: {status_result.error}"
        assert status_result.video_id == generate_result.video_id
        assert status_result.status is not None
        print(f"  Video status: {status_result.status}")


class TestVideoStatus:
    """Integration tests for video status checking."""

    @pytest.mark.asyncio
    async def test_get_video_status_invalid_id(self, api_client: HeyGenApiClient):
        """Test getting status for a non-existent video ID."""
        result = await api_client.get_video_status("invalid-video-id-12345")

        assert isinstance(result, MCPVideoStatusResponse)
        # Should return an error or a failed status
        # The API behavior may vary - it might return an error or a specific status
        print("\n  Result for invalid ID:")
        print(f"    status={result.status}, error={result.error}")


class TestListAvatars:
    """Integration tests for listing all avatars."""

    @pytest.mark.asyncio
    async def test_list_avatars(self, api_client: HeyGenApiClient):
        """Test retrieving all available avatars."""
        result = await api_client.list_avatars()

        assert isinstance(result, MCPListAvatarsResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.avatars is not None
        assert result.total_count is not None
        assert result.total_count >= 0
        print(f"\n  Found {result.total_count} total avatars")

        if result.avatars and len(result.avatars) > 0:
            first_avatar = result.avatars[0]
            assert first_avatar.avatar_id is not None
            assert first_avatar.avatar_name is not None
            print(f"  First avatar: {first_avatar.avatar_name}")
            print(f"    ID: {first_avatar.avatar_id}")


class TestAvatarDetails:
    """Integration tests for getting avatar details."""

    @pytest.mark.asyncio
    async def test_get_avatar_details(self, api_client: HeyGenApiClient):
        """Test retrieving details for a specific avatar."""
        # First get an avatar to use
        avatars_result = await api_client.list_avatars()

        if not avatars_result.avatars or len(avatars_result.avatars) == 0:
            pytest.skip("No avatars available to test")

        avatar_id = avatars_result.avatars[0].avatar_id
        result = await api_client.get_avatar_details(avatar_id)

        assert isinstance(result, MCPAvatarDetailsResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.avatar is not None
        assert result.avatar.avatar_id == avatar_id
        print(f"\n  Avatar details: {result.avatar.avatar_name}")
        print(f"  Type: {result.avatar.type}")
        print(f"  Gender: {result.avatar.gender}")

    @pytest.mark.asyncio
    async def test_get_avatar_details_invalid_id(self, api_client: HeyGenApiClient):
        """Test getting details for a non-existent avatar ID."""
        result = await api_client.get_avatar_details("invalid-avatar-id-12345")

        assert isinstance(result, MCPAvatarDetailsResponse)
        # Should return an error
        print(f"\n  Result for invalid ID: error={result.error}")


class TestListTemplates:
    """Integration tests for listing templates."""

    @pytest.mark.asyncio
    async def test_list_templates(self, api_client: HeyGenApiClient):
        """Test retrieving templates."""
        result = await api_client.list_templates()

        assert isinstance(result, MCPListTemplatesResponse)
        assert result.error is None, f"API returned error: {result.error}"
        # Templates may be empty for accounts without custom templates
        print(f"\n  Found {result.total_count} templates")

        if result.templates and len(result.templates) > 0:
            first_template = result.templates[0]
            assert first_template.template_id is not None
            assert first_template.name is not None
            print(f"  First template: {first_template.name}")
            print(f"    ID: {first_template.template_id}")


class TestUserInfo:
    """Integration tests for getting user information."""

    @pytest.mark.asyncio
    async def test_get_user_info(self, api_client: HeyGenApiClient):
        """Test retrieving current user information."""
        result = await api_client.get_user_info()

        assert isinstance(result, MCPUserInfoResponse)
        assert result.error is None, f"API returned error: {result.error}"
        # User info fields may vary
        print(f"\n  Username: {result.username}")
        print(f"  Email: {result.email}")
        print(f"  Name: {result.first_name} {result.last_name}")


class TestTemplateDetails:
    """Integration tests for getting template details."""

    @pytest.mark.asyncio
    async def test_get_template_details(self, api_client: HeyGenApiClient):
        """Test retrieving template details."""
        # First get a template to use
        templates_result = await api_client.list_templates()

        if not templates_result.templates or len(templates_result.templates) == 0:
            pytest.skip("No templates available to test")

        template_id = templates_result.templates[0].template_id
        result = await api_client.get_template_details(template_id)

        assert isinstance(result, MCPTemplateDetailsResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.template is not None
        print(f"\n  Template: {result.template.name}")
        print(f"  Variables: {result.template.variables}")
        if result.template.scenes:
            print(f"  Scenes: {len(result.template.scenes)}")

    @pytest.mark.asyncio
    async def test_get_template_details_invalid_id(self, api_client: HeyGenApiClient):
        """Test getting details for a non-existent template ID."""
        result = await api_client.get_template_details("invalid-template-id-12345")

        assert isinstance(result, MCPTemplateDetailsResponse)
        # Should return an error
        print(f"\n  Result for invalid ID: error={result.error}")


class TestGenerateVideoFromTemplate:
    """Integration tests for generating video from template.

    Note: These tests are marked with a special marker because they
    consume API credits. Run with: pytest -m "video_generation"
    """

    @pytest.mark.asyncio
    @pytest.mark.video_generation
    async def test_generate_video_from_template(self, api_client: HeyGenApiClient):
        """Test generating a video from a template.

        WARNING: This test consumes API credits!
        """
        # First get a template to use
        templates_result = await api_client.list_templates()

        if not templates_result.templates or len(templates_result.templates) == 0:
            pytest.skip("No templates available to test")

        template_id = templates_result.templates[0].template_id

        # Get template details to see variables
        details_result = await api_client.get_template_details(template_id)
        if details_result.error:
            pytest.skip(f"Could not get template details: {details_result.error}")

        # Generate video (with test mode if available)
        result = await api_client.generate_video_from_template(
            template_id=template_id,
            title="Integration Test Video from Template",
            test=True,  # Use test mode if available
        )

        assert isinstance(result, MCPTemplateVideoGenerateResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.video_id is not None
        print(f"\n  Generated video ID: {result.video_id}")


class TestListAssets:
    """Integration tests for list_assets."""

    @pytest.mark.asyncio
    async def test_list_assets(self, api_client: HeyGenApiClient):
        """Test listing assets from the API."""
        result = await api_client.list_assets()

        assert isinstance(result, MCPAssetListResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.assets is not None
        print(f"\n  Total assets: {len(result.assets)}")
        if result.assets:
            print(f"  First asset ID: {result.assets[0].asset_id}")


class TestListVideos:
    """Integration tests for list_videos."""

    @pytest.mark.asyncio
    async def test_list_videos(self, api_client: HeyGenApiClient):
        """Test listing videos from the API."""
        result = await api_client.list_videos()

        assert isinstance(result, MCPVideoListResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.videos is not None
        assert result.total is not None
        assert result.total >= 0
        print(f"\n  Total videos: {result.total}")
        if result.videos:
            first = result.videos[0]
            print(f"  First video: {first.video_id} ({first.status})")

    @pytest.mark.asyncio
    async def test_list_videos_with_pagination(self, api_client: HeyGenApiClient):
        """Test listing videos with pagination token."""
        result = await api_client.list_videos()

        assert isinstance(result, MCPVideoListResponse)
        assert result.error is None, f"API returned error: {result.error}"

        if result.token:
            result2 = await api_client.list_videos(token=result.token)
            assert isinstance(result2, MCPVideoListResponse)
            assert result2.error is None, f"API returned error: {result2.error}"
            print(f"\n  Page 2 videos: {len(result2.videos) if result2.videos else 0}")
        else:
            print("\n  No pagination token (fewer than 100 videos)")


class TestFolders:
    """Integration tests for folder operations."""

    @pytest.mark.asyncio
    async def test_list_folders(self, api_client: HeyGenApiClient):
        """Test listing folders from the API."""
        result = await api_client.list_folders()

        assert isinstance(result, MCPFolderListResponse)
        assert result.error is None, f"API returned error: {result.error}"
        assert result.folders is not None
        print(f"\n  Total folders: {len(result.folders)}")
        if result.folders:
            first = result.folders[0]
            print(f"  First folder: {first.name} (id: {first.id})")

    @pytest.mark.asyncio
    @pytest.mark.folder_operations
    async def test_folder_create_update_trash_restore(
        self, api_client: HeyGenApiClient
    ):
        """Test folder lifecycle: create, update, trash, restore.

        Note: This test modifies data in your account.
        Run with: pytest -m folder_operations
        """
        import uuid

        folder_name = f"Test Folder {uuid.uuid4().hex[:8]}"
        create_result = await api_client.create_folder(name=folder_name)

        assert isinstance(create_result, MCPFolderCreateResponse)
        assert create_result.error is None, f"Create error: {create_result.error}"
        assert create_result.folder_id is not None
        folder_id = create_result.folder_id
        print(f"\n  Created folder: {folder_name} (id: {folder_id})")

        new_name = f"Updated {folder_name}"
        update_result = await api_client.update_folder(
            folder_id=folder_id, name=new_name
        )

        assert isinstance(update_result, MCPFolderUpdateResponse)
        assert update_result.error is None, f"Update error: {update_result.error}"
        print(f"  Updated folder name to: {new_name}")

        trash_result = await api_client.trash_folder(folder_id=folder_id)

        assert isinstance(trash_result, MCPFolderTrashResponse)
        assert trash_result.error is None, f"Trash error: {trash_result.error}"
        print(f"  Trashed folder: {folder_id}")

        restore_result = await api_client.restore_folder(folder_id=folder_id)

        assert isinstance(restore_result, MCPFolderRestoreResponse)
        assert restore_result.error is None, f"Restore error: {restore_result.error}"
        print(f"  Restored folder: {folder_id}")

        # Clean up - trash again
        await api_client.trash_folder(folder_id=folder_id)
        print(f"  Cleaned up (trashed): {folder_id}")


class TestAssetUploadDelete:
    """Integration tests for asset upload and delete.

    Note: These tests upload and delete assets.
    Run with: pytest -m asset_operations
    """

    @pytest.mark.asyncio
    @pytest.mark.asset_operations
    async def test_upload_and_delete_asset(self, api_client: HeyGenApiClient):
        """Test uploading an image asset and deleting it.

        WARNING: This test uploads a file to your HeyGen account.
        """
        import base64
        import os
        import tempfile

        # Create a simple test image (1x1 pixel PNG)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(png_data)
            temp_path = f.name

        asset_id = None
        try:
            upload_result = await api_client.upload_asset(file_path=temp_path)

            assert isinstance(upload_result, MCPAssetUploadResponse)
            assert upload_result.error is None, f"Upload error: {upload_result.error}"
            assert upload_result.asset_id is not None
            asset_id = upload_result.asset_id
            print(f"\n  Uploaded asset: {asset_id}")

            delete_result = await api_client.delete_asset(asset_id=asset_id)

            assert isinstance(delete_result, MCPAssetDeleteResponse)
            assert delete_result.error is None, f"Delete error: {delete_result.error}"
            print(f"  Deleted asset: {asset_id}")
            asset_id = None  # Mark as cleaned up

        finally:
            # Clean up local temp file
            os.unlink(temp_path)
            # Clean up HeyGen asset if upload succeeded but test failed before delete
            if asset_id is not None:
                try:
                    await api_client.delete_asset(asset_id=asset_id)
                    print(f"  Cleanup: deleted orphaned asset {asset_id}")
                except Exception as e:
                    print(f"  Cleanup warning: could not delete asset {asset_id}: {e}")


class TestAvatarIVVideo:
    """Integration tests for Avatar IV video generation.

    Note: These tests consume API credits.
    Run with: pytest -m video_generation
    """

    @pytest.mark.asyncio
    @pytest.mark.video_generation
    async def test_generate_avatar_iv_video(self, api_client: HeyGenApiClient):
        """Test generating an Avatar IV video from a photo.

        WARNING: This test consumes API credits!
        """
        import base64
        import os
        import tempfile

        # Create a simple test image (1x1 pixel PNG)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(png_data)
            temp_path = f.name

        try:
            upload_result = await api_client.upload_asset(file_path=temp_path)
            if upload_result.error:
                pytest.skip(f"Could not upload test image: {upload_result.error}")

            image_key = upload_result.asset_id

            voices_result = await api_client.get_voices()
            if not voices_result.voices:
                pytest.skip("No voices available")
            voice_id = voices_result.voices[0].voice_id

            from heygen_mcp.models import AvatarIVVideoRequest

            request = AvatarIVVideoRequest(
                image_key=image_key,
                video_title="Integration Test Avatar IV Video",
                script="Hello, this is an Avatar IV integration test.",
                voice_id=voice_id,
            )

            result = await api_client.generate_avatar_iv_video(request)

            assert isinstance(result, MCPAvatarIVVideoResponse)
            # May fail with 1x1 pixel image, but tests the API call
            if result.error:
                print(f"\n  Avatar IV result: {result.error}")
                if "image" in result.error.lower():
                    print("  (Expected - test image too small)")
            else:
                assert result.video_id is not None
                print(f"\n  Generated Avatar IV video: {result.video_id}")

            await api_client.delete_asset(asset_id=image_key)

        finally:
            os.unlink(temp_path)
