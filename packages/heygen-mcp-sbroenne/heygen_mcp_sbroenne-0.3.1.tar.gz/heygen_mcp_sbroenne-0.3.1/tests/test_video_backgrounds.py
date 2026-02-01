"""Tests for video background functionality."""

import pytest

from heygen_mcp.models import (
    Background,
    Character,
    Dimension,
    VideoGenerateRequest,
    VideoInput,
    Voice,
)


class TestBackgroundModel:
    """Test Background model validation and serialization."""

    def test_color_background(self):
        """Test color background creation."""
        background = Background(type="color", value="#008000")
        assert background.type == "color"
        assert background.value == "#008000"
        assert background.video_asset_id is None
        assert background.image_asset_id is None

    def test_image_background(self):
        """Test image background creation with asset ID."""
        background = Background(type="image", image_asset_id="img_123")
        assert background.type == "image"
        assert background.image_asset_id == "img_123"
        assert background.video_asset_id is None
        assert background.value is None

    def test_video_background(self):
        """Test video background creation with asset ID and play style."""
        background = Background(
            type="video", video_asset_id="vid_456", play_style="fit_to_scene"
        )
        assert background.type == "video"
        assert background.video_asset_id == "vid_456"
        assert background.play_style == "fit_to_scene"
        assert background.value is None
        assert background.image_asset_id is None

    def test_video_background_loop_style(self):
        """Test video background with loop play style."""
        background = Background(
            type="video", video_asset_id="vid_789", play_style="loop"
        )
        assert background.play_style == "loop"

    def test_background_serialization(self):
        """Test that Background serializes correctly for API."""
        background = Background(
            type="video", video_asset_id="test_asset_id", play_style="fit_to_scene"
        )
        data = background.model_dump(exclude_none=True)
        assert data == {
            "type": "video",
            "video_asset_id": "test_asset_id",
            "play_style": "fit_to_scene",
        }


class TestVideoInputWithBackground:
    """Test VideoInput with background integration."""

    def test_video_input_without_background(self):
        """Test VideoInput creation without background (backward compatibility)."""
        video_input = VideoInput(
            character=Character(avatar_id="test_avatar"),
            voice=Voice(input_text="Hello", voice_id="test_voice"),
        )
        assert video_input.background is None

    def test_video_input_with_color_background(self):
        """Test VideoInput with color background."""
        background = Background(type="color", value="#FF0000")
        video_input = VideoInput(
            character=Character(avatar_id="test_avatar"),
            voice=Voice(input_text="Hello", voice_id="test_voice"),
            background=background,
        )
        assert video_input.background is not None
        assert video_input.background.type == "color"
        assert video_input.background.value == "#FF0000"

    def test_video_input_with_video_background(self):
        """Test VideoInput with video background."""
        background = Background(
            type="video",
            video_asset_id="screen_recording_123",
            play_style="fit_to_scene",
        )
        video_input = VideoInput(
            character=Character(avatar_id="Annie_expressive6_public"),
            voice=Voice(input_text="Welcome to this tutorial", voice_id="voice_id_123"),
            background=background,
        )
        assert video_input.background.type == "video"
        assert video_input.background.video_asset_id == "screen_recording_123"
        assert video_input.background.play_style == "fit_to_scene"

    def test_video_input_serialization_with_background(self):
        """Test that VideoInput with background serializes correctly."""
        background = Background(
            type="video", video_asset_id="vid_test", play_style="loop"
        )
        video_input = VideoInput(
            character=Character(avatar_id="test_avatar"),
            voice=Voice(input_text="Test", voice_id="test_voice"),
            background=background,
        )
        data = video_input.model_dump(exclude_none=True)

        assert "background" in data
        assert data["background"]["type"] == "video"
        assert data["background"]["video_asset_id"] == "vid_test"
        assert data["background"]["play_style"] == "loop"


class TestVideoGenerateRequestWithBackground:
    """Test full VideoGenerateRequest with background."""

    def test_generate_request_with_video_background(self):
        """Test complete video generation request with video background."""
        background = Background(
            type="video",
            video_asset_id="screen_recording_asset_id",
            play_style="fit_to_scene",
        )

        request = VideoGenerateRequest(
            title="Tutorial Video with Screen Recording",
            video_inputs=[
                VideoInput(
                    character=Character(avatar_id="Annie_expressive6_public"),
                    voice=Voice(
                        input_text="In this tutorial, I'll show you "
                        "how to use the software.",
                        voice_id="6fa2fa767bf148fc939c0bbba7306760",
                    ),
                    background=background,
                )
            ],
            dimension=Dimension(width=1920, height=1080),
        )

        assert request.video_inputs[0].background is not None
        assert request.video_inputs[0].background.type == "video"
        assert request.dimension.width == 1920
        assert request.dimension.height == 1080

    def test_generate_request_serialization(self):
        """Test that request serializes correctly for HeyGen API."""
        background = Background(
            type="video", video_asset_id="test_vid_123", play_style="fit_to_scene"
        )

        request = VideoGenerateRequest(
            title="Test Video",
            video_inputs=[
                VideoInput(
                    character=Character(avatar_id="test_avatar"),
                    voice=Voice(input_text="Test", voice_id="test_voice"),
                    background=background,
                )
            ],
        )

        data = request.model_dump(exclude_none=True)

        # Verify structure matches HeyGen API expectations
        assert "video_inputs" in data
        assert len(data["video_inputs"]) == 1
        assert "background" in data["video_inputs"][0]
        assert data["video_inputs"][0]["background"]["type"] == "video"
        assert data["video_inputs"][0]["background"]["video_asset_id"] == "test_vid_123"

    def test_backward_compatibility_without_background(self):
        """Test that requests without background still work (backward compatibility)."""
        request = VideoGenerateRequest(
            title="Simple Video",
            video_inputs=[
                VideoInput(
                    character=Character(avatar_id="test_avatar"),
                    voice=Voice(input_text="Test", voice_id="test_voice"),
                )
            ],
        )

        data = request.model_dump(exclude_none=True)

        # Background should not be in the serialized data when None
        assert "background" not in data["video_inputs"][0]


class TestPlayStyles:
    """Test different video background play styles."""

    @pytest.mark.parametrize(
        "play_style", ["fit_to_scene", "freeze", "loop", "full_video"]
    )
    def test_valid_play_styles(self, play_style):
        """Test all valid play styles."""
        background = Background(
            type="video", video_asset_id="test_vid", play_style=play_style
        )
        assert background.play_style == play_style


class TestUseCaseScenarios:
    """Test real-world use case scenarios."""

    def test_tutorial_video_with_screen_recording(self):
        """Test the main use case: tutorial video with screen recording background."""
        # Scenario: User has uploaded a screen recording and wants to add avatar overlay
        screen_recording_asset_id = "screen_rec_001"

        background = Background(
            type="video",
            video_asset_id=screen_recording_asset_id,
            play_style="fit_to_scene",
        )

        request = VideoGenerateRequest(
            title="Excel Tutorial - Pivot Tables",
            video_inputs=[
                VideoInput(
                    character=Character(
                        avatar_id="Annie_expressive6_public", avatar_style="normal"
                    ),
                    voice=Voice(
                        input_text="Let me show you how to create "
                        "a pivot table in Excel.",
                        voice_id="voice_annie_id",
                    ),
                    background=background,
                )
            ],
            dimension=Dimension(width=1920, height=1080),
        )

        # Verify the request is properly structured
        assert request.title == "Excel Tutorial - Pivot Tables"
        assert request.dimension.width == 1920
        bg = request.video_inputs[0].background
        assert bg.video_asset_id == screen_recording_asset_id
        assert bg.play_style == "fit_to_scene"

    def test_green_screen_effect(self):
        """Test green screen color background for chromakey."""
        background = Background(type="color", value="#008000")

        request = VideoGenerateRequest(
            title="Green Screen Video",
            video_inputs=[
                VideoInput(
                    character=Character(avatar_id="test_avatar"),
                    voice=Voice(
                        input_text="This is on green screen", voice_id="test_voice"
                    ),
                    background=background,
                )
            ],
        )

        assert request.video_inputs[0].background.type == "color"
        assert request.video_inputs[0].background.value == "#008000"

    def test_branded_background_image(self):
        """Test static branded image background."""
        background = Background(type="image", image_asset_id="company_logo_background")

        request = VideoGenerateRequest(
            title="Company Announcement",
            video_inputs=[
                VideoInput(
                    character=Character(avatar_id="professional_avatar"),
                    voice=Voice(
                        input_text="Welcome to our company update",
                        voice_id="professional_voice",
                    ),
                    background=background,
                )
            ],
        )

        assert request.video_inputs[0].background.type == "image"
        bg = request.video_inputs[0].background
        assert bg.image_asset_id == "company_logo_background"
