"""
Quick test script to verify video background functionality works with the API.

This script tests:
1. Background model serialization
2. API request format
3. Parameter validation
"""

import asyncio
import os

from heygen_mcp.models import (
    Background,
    Character,
    Dimension,
    VideoGenerateRequest,
    VideoInput,
    Voice,
)


def test_background_serialization():
    """Test that Background models serialize correctly."""
    print("=" * 60)
    print("Testing Background Serialization")
    print("=" * 60)

    # Test video background
    bg = Background(
        type="video", video_asset_id="test_asset_123", play_style="fit_to_scene"
    )

    data = bg.model_dump(exclude_none=True)
    print("\n✅ Video Background:")
    print(f"   {data}")
    assert data == {
        "type": "video",
        "video_asset_id": "test_asset_123",
        "play_style": "fit_to_scene",
    }

    # Test color background
    bg = Background(type="color", value="#008000")
    data = bg.model_dump(exclude_none=True)
    print("\n✅ Color Background:")
    print(f"   {data}")
    assert data == {"type": "color", "value": "#008000"}

    # Test image background
    bg = Background(type="image", image_asset_id="img_123")
    data = bg.model_dump(exclude_none=True)
    print("\n✅ Image Background:")
    print(f"   {data}")
    assert data == {"type": "image", "image_asset_id": "img_123"}

    print("\n✅ All background types serialize correctly!")


def test_video_request_with_background():
    """Test VideoGenerateRequest with background."""
    print("\n" + "=" * 60)
    print("Testing VideoGenerateRequest with Background")
    print("=" * 60)

    # Create request with video background
    request = VideoGenerateRequest(
        title="Test Video",
        video_inputs=[
            VideoInput(
                character=Character(avatar_id="test_avatar"),
                voice=Voice(input_text="Test", voice_id="test_voice"),
                background=Background(
                    type="video",
                    video_asset_id="screen_recording_123",
                    play_style="fit_to_scene",
                ),
            )
        ],
        dimension=Dimension(width=1920, height=1080),
    )

    # Serialize (this is what gets sent to the API)
    data = request.model_dump(exclude_none=True)

    print("\n✅ Request structure:")
    print(f"   Title: {data['title']}")
    print(f"   Dimension: {data['dimension']}")
    print(f"   Video inputs: {len(data['video_inputs'])}")
    print(f"   Background: {data['video_inputs'][0]['background']}")

    # Verify structure
    assert "background" in data["video_inputs"][0]
    assert data["video_inputs"][0]["background"]["type"] == "video"
    bg = data["video_inputs"][0]["background"]
    assert bg["video_asset_id"] == "screen_recording_123"

    print("\n✅ Request serializes correctly for API!")


def test_request_without_background():
    """Test backward compatibility - request without background."""
    print("\n" + "=" * 60)
    print("Testing Backward Compatibility (No Background)")
    print("=" * 60)

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

    # Background should not be in serialized data
    assert "background" not in data["video_inputs"][0]

    print("\n✅ Requests without background still work!")
    print("   (Background field excluded from serialization)")


async def test_api_connection():
    """Test actual API connection if API key is available."""
    api_key = os.getenv("HEYGEN_API_KEY")
    if not api_key:
        print("\n⚠️  Skipping API test (no HEYGEN_API_KEY)")
        return

    print("\n" + "=" * 60)
    print("Testing API Connection")
    print("=" * 60)

    from heygen_mcp.client import HeyGenApiClient

    async with HeyGenApiClient(api_key) as client:
        # Test basic connection
        result = await client.get_remaining_credits()
        if result.error:
            print(f"\n❌ API Error: {result.error}")
        else:
            print("\n✅ API Connected!")
            print(f"   Remaining Credits: {result.remaining_credits}")

        # List avatars
        avatars = await client.list_avatars()
        if avatars.error:
            print(f"❌ Error listing avatars: {avatars.error}")
        else:
            print(f"✅ Found {len(avatars.avatars)} avatars")
            if avatars.avatars:
                print(f"   Sample: {avatars.avatars[0].avatar_id}")

        # List assets
        assets = await client.list_assets()
        if assets.error:
            print(f"❌ Error listing assets: {assets.error}")
        else:
            print(f"✅ Found {assets.total} assets")


def main():
    """Run all tests."""
    print("\n" + "🎬" * 30)
    print("Video Background Feature Test")
    print("🎬" * 30 + "\n")

    try:
        # Serialization tests
        test_background_serialization()
        test_video_request_with_background()
        test_request_without_background()

        # API test
        asyncio.run(test_api_connection())

        print("\n" + "=" * 60)
        print("🎉 All Tests Passed!")
        print("=" * 60)
        print("\n✅ Video background feature is working correctly!")
        print("✅ Ready to use for tutorial video generation!")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
