"""HeyGen MCP server module providing MCP tools for the HeyGen API."""

import argparse
import logging
import os
import sys
from typing import Literal

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from heygen_mcp.client import HeyGenApiClient
from heygen_mcp.models import (
    AvatarIVVideoRequest,
    Background,
    Character,
    Dimension,
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
    VideoGenerateRequest,
    VideoInput,
    Voice,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("heygen_mcp")

# Load environment variables
load_dotenv()

# Create MCP server instance with instructions for LLMs
# fmt: off
# ruff: noqa: E501
MCP_INSTRUCTIONS = """
# HeyGen MCP Server - AI Video Generation

This server enables AI-powered video generation using HeyGen's platform.

## WORKFLOW: Creating a Video

1. **Get Available Resources First**:
   - Use `avatars(action='list')` to see available avatars
   - Use `voices(action='list')` to see available voices
   - Use `user(action='credits')` to check remaining credits

2. **Generate Video** (choose one approach):
   - **From scratch**: Use `videos(action='generate')` with video_inputs_json (JSON array of scenes with avatar_id, voice_id, input_text per scene)
   - **From template**: Use `templates(action='list')`, then `templates(action='get')` to see variables, then `templates(action='generate')`
   - **From photo (Avatar IV)**: Upload photo with `assets(action='upload')`, then use `videos(action='generate_iv')`

3. **Check Status**: Use `videos(action='status')` - videos take minutes to hours to process

## KEY CONCEPTS

- **Avatar**: The AI person who appears in the video
- **Voice**: The voice that speaks the script (can be different from avatar)
- **Template**: Pre-made video layouts with customizable variables (text, images, avatars)
- **Asset**: Uploaded media files (images, videos, audio) used in videos
- **Avatar IV**: Create videos from any photo with AI-generated motion

## TIPS

- Always check credits before generating videos
- Template-based videos are often easier than building from scratch
- Video generation is async - always poll status until complete
- Use test=True for template videos to preview without using credits
"""
# fmt: on

mcp = FastMCP("HeyGen MCP", instructions=MCP_INSTRUCTIONS)
_api_client: HeyGenApiClient | None = None


async def get_api_client() -> HeyGenApiClient:
    """Get or create the API client singleton.

    Returns:
        HeyGenApiClient instance.

    Raises:
        ValueError: If HEYGEN_API_KEY environment variable is not set.
    """
    global _api_client

    if _api_client is not None:
        return _api_client

    api_key = os.getenv("HEYGEN_API_KEY")
    if not api_key:
        raise ValueError("HEYGEN_API_KEY environment variable not set.")

    _api_client = HeyGenApiClient(api_key)
    logger.info("HeyGen API client initialized")
    return _api_client


async def reset_api_client() -> None:
    """Reset the API client singleton. Used for testing."""
    global _api_client
    if _api_client is not None:
        await _api_client.close()
        _api_client = None


# ==================== User Resource ====================


@mcp.tool(
    name="user",
    description=(
        "Manage HeyGen user account. "
        "RECOMMENDED: Call 'credits' before generating videos to check quota. "
        "Actions: "
        "'info' - get user profile (username, email, plan); "
        "'credits' - get remaining credits (IMPORTANT: check before video generation)."
    ),
)
async def user(
    action: Literal["info", "credits"],
) -> MCPUserInfoResponse | MCPGetCreditsResponse:
    """Manage user account information and credits."""
    logger.info(f"user action={action}")
    try:
        client = await get_api_client()

        if action == "info":
            return await client.get_user_info()
        elif action == "credits":
            return await client.get_remaining_credits()
        else:
            return MCPUserInfoResponse(error=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"user action={action} error: {e}")
        if action == "credits":
            return MCPGetCreditsResponse(error=str(e))
        return MCPUserInfoResponse(error=str(e))


# ==================== Voices Resource ====================


@mcp.tool(
    name="voices",
    description=(
        "Get available voices for video generation. "
        "REQUIRED: You need a voice_id to generate any video. "
        "Actions: 'list' - returns voices with id, name, language, gender. "
        "TIP: Match voice language to your script language."
    ),
)
async def voices(
    action: Literal["list"],
) -> MCPVoicesResponse:
    """Manage voice resources."""
    logger.info(f"voices action={action}")
    try:
        client = await get_api_client()

        if action == "list":
            return await client.get_voices()
        else:
            return MCPVoicesResponse(error=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"voices action={action} error: {e}")
        return MCPVoicesResponse(error=str(e))


# ==================== Avatars Resource ====================


@mcp.tool(
    name="avatars",
    description=(
        "Get available avatars (AI personas) for video generation. "
        "REQUIRED: You need an avatar_id to generate videos. "
        "Actions: "
        "'list' - get all avatars with id, name, gender (START HERE); "
        "'get' - get details for a specific avatar (requires avatar_id); "
        "'list_groups' - get avatar groups (include_public=true for public); "
        "'list_in_group' - get avatars in a group (requires group_id). "
        "TIP: Use 'list' first, then 'get' for details on a chosen avatar."
    ),
)
async def avatars(
    action: Literal["list", "get", "list_groups", "list_in_group"],
    avatar_id: str | None = None,
    group_id: str | None = None,
    include_public: bool = False,
) -> (
    MCPListAvatarsResponse
    | MCPAvatarDetailsResponse
    | MCPAvatarGroupResponse
    | MCPAvatarsInGroupResponse
):
    """Manage avatar resources."""
    logger.info(f"avatars action={action} avatar_id={avatar_id} group_id={group_id}")
    try:
        client = await get_api_client()

        if action == "list":
            return await client.list_avatars()

        elif action == "get":
            if not avatar_id:
                return MCPAvatarDetailsResponse(
                    error="avatar_id is required for 'get' action"
                )
            return await client.get_avatar_details(avatar_id)

        elif action == "list_groups":
            return await client.list_avatar_groups(include_public)

        elif action == "list_in_group":
            if not group_id:
                return MCPAvatarsInGroupResponse(
                    error="group_id is required for 'list_in_group' action"
                )
            return await client.get_avatars_in_group(group_id)

        else:
            return MCPListAvatarsResponse(error=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"avatars action={action} error: {e}")
        return MCPListAvatarsResponse(error=str(e))


# ==================== Videos Resource ====================


@mcp.tool(
    name="videos",
    description=(
        "Generate AI avatar videos and check their status. "
        "WORKFLOW: 1) Get avatar_id, 2) Get voice_id, 3) Call 'generate', "
        "4) Poll 'status' until complete. "
        "Actions: "
        "'list' - get all videos (with status and video_url if complete); "
        "'generate' - create video (REQUIRED: video_inputs_json - JSON array of scenes, "
        "even for single-scene videos. Each scene needs: character.avatar_id, "
        "voice.input_text, voice.voice_id. Optional: background with type/value/asset_id); "
        "'generate_iv' - create video from photo with AI motion "
        "(REQUIRED: image_key, script, voice_id, video_title); "
        "'status' - check if ready (REQUIRED: video_id). "
        "NOTE: Videos take 1-10+ min. Poll status until completed."
    ),
)
async def videos(
    action: Literal["list", "generate", "generate_iv", "status"],
    video_id: str | None = None,
    title: str = "",
    # Pagination parameter
    token: str | None = None,
    # Video inputs (JSON array of scenes - REQUIRED for generate)
    video_inputs_json: str | None = None,
    # Avatar IV specific parameters
    image_key: str | None = None,
    script: str | None = None,
    video_title: str | None = None,
    voice_id: str | None = None,
    audio_url: str | None = None,
    audio_asset_id: str | None = None,
    custom_motion_prompt: str | None = None,
    enhance_custom_motion_prompt: bool | None = None,
) -> (
    MCPVideoListResponse
    | MCPVideoGenerateResponse
    | MCPVideoStatusResponse
    | MCPAvatarIVVideoResponse
):
    """Manage video generation and status."""
    logger.info(f"videos action={action} video_id={video_id}")
    try:
        client = await get_api_client()

        if action == "list":
            return await client.list_videos(token=token)

        elif action == "generate":
            if not video_inputs_json:
                return MCPVideoGenerateResponse(
                    error="video_inputs_json is required for 'generate' action. "
                    "Provide a JSON array of scenes, e.g.: "
                    '[{"character": {"avatar_id": "..."}, '
                    '"voice": {"voice_id": "...", "input_text": "..."}}]'
                )

            import json

            try:
                scenes_data = json.loads(video_inputs_json)
                if not isinstance(scenes_data, list):
                    return MCPVideoGenerateResponse(
                        error="video_inputs_json must be a JSON array of scenes"
                    )
                if len(scenes_data) == 0:
                    return MCPVideoGenerateResponse(
                        error="video_inputs_json must contain at least one scene"
                    )

                video_inputs = []
                for i, scene in enumerate(scenes_data):
                    # Validate required fields per scene
                    if "character" not in scene or "avatar_id" not in scene.get(
                        "character", {}
                    ):
                        return MCPVideoGenerateResponse(
                            error=f"Scene {i + 1}: character.avatar_id is required"
                        )
                    if "voice" not in scene or "input_text" not in scene.get(
                        "voice", {}
                    ):
                        return MCPVideoGenerateResponse(
                            error=f"Scene {i + 1}: voice.input_text is required"
                        )
                    if "voice_id" not in scene.get("voice", {}):
                        return MCPVideoGenerateResponse(
                            error=f"Scene {i + 1}: voice.voice_id is required"
                        )

                    # Build Character
                    char_data = scene["character"]
                    character = Character(
                        avatar_id=char_data["avatar_id"],
                        type=char_data.get("type", "avatar"),
                        avatar_style=char_data.get("avatar_style", "normal"),
                        scale=char_data.get("scale", 1.0),
                    )

                    # Build Voice
                    voice_data = scene["voice"]
                    voice = Voice(
                        input_text=voice_data["input_text"],
                        voice_id=voice_data["voice_id"],
                        type=voice_data.get("type", "text"),
                    )

                    # Build Background (optional)
                    background = None
                    if "background" in scene:
                        bg_data = scene["background"]
                        bg_type = bg_data.get("type")
                        if bg_type == "color":
                            background = Background(
                                type="color",
                                value=bg_data.get("value"),
                                url=None,
                                image_asset_id=None,
                                video_asset_id=None,
                                play_style=None,
                            )
                        elif bg_type == "image":
                            background = Background(
                                type="image",
                                value=None,
                                url=bg_data.get("url"),
                                image_asset_id=bg_data.get("image_asset_id"),
                                video_asset_id=None,
                                play_style=None,
                            )
                        elif bg_type == "video":
                            background = Background(
                                type="video",
                                value=None,
                                url=bg_data.get("url"),
                                image_asset_id=None,
                                video_asset_id=bg_data.get("video_asset_id"),
                                play_style=bg_data.get("play_style", "fit_to_scene"),
                            )

                    video_inputs.append(
                        VideoInput(
                            character=character,
                            voice=voice,
                            background=background,
                        )
                    )

                request = VideoGenerateRequest(
                    title=title,
                    video_inputs=video_inputs,
                    dimension=Dimension(width=1280, height=720),
                )
                return await client.generate_avatar_video(request)

            except json.JSONDecodeError as e:
                return MCPVideoGenerateResponse(
                    error=f"Invalid JSON in video_inputs_json: {e}"
                )

        elif action == "generate_iv":
            if not image_key:
                return MCPAvatarIVVideoResponse(
                    error="image_key is required for 'generate_iv' action "
                    "(upload photo first using assets tool)"
                )
            if not script:
                return MCPAvatarIVVideoResponse(
                    error="script is required for 'generate_iv' action"
                )
            if not voice_id:
                return MCPAvatarIVVideoResponse(
                    error="voice_id is required for 'generate_iv' action"
                )
            if not video_title:
                return MCPAvatarIVVideoResponse(
                    error="video_title is required for 'generate_iv' action"
                )

            request = AvatarIVVideoRequest(
                image_key=image_key,
                video_title=video_title,
                script=script,
                voice_id=voice_id,
                audio_url=audio_url,
                audio_asset_id=audio_asset_id,
                custom_motion_prompt=custom_motion_prompt,
                enhance_custom_motion_prompt=enhance_custom_motion_prompt,
            )
            return await client.generate_avatar_iv_video(request)

        elif action == "status":
            if not video_id:
                return MCPVideoStatusResponse(
                    error="video_id is required for 'status' action"
                )
            return await client.get_video_status(video_id)

        else:
            return MCPVideoGenerateResponse(error=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"videos action={action} error: {e}")
        if action == "list":
            return MCPVideoListResponse(error=str(e))
        if action == "status":
            return MCPVideoStatusResponse(error=str(e))
        if action == "generate_iv":
            return MCPAvatarIVVideoResponse(error=str(e))
        return MCPVideoGenerateResponse(error=str(e))


# ==================== Templates Resource ====================


@mcp.tool(
    name="templates",
    description=(
        "Use pre-made video templates for easier video creation. "
        "EASIER THAN 'videos': Templates have pre-configured layouts. "
        "WORKFLOW: 1) 'list' templates, 2) 'get' to see variables, "
        "3) 'generate' with variables, 4) Check status. "
        "Actions: "
        "'list' - get all templates with id and name; "
        "'get' - get template variables (REQUIRED: template_id); "
        "'generate' - create video (REQUIRED: template_id; "
        "OPTIONAL: variables dict, title, test=True, caption=True). "
        "TIP: Use test=True to preview without using credits."
    ),
)
async def templates(
    action: Literal["list", "get", "generate"],
    template_id: str | None = None,
    variables: dict | None = None,
    title: str | None = None,
    test: bool = False,
    caption: bool = False,
) -> (
    MCPListTemplatesResponse
    | MCPTemplateDetailsResponse
    | MCPTemplateVideoGenerateResponse
):
    """Manage template resources and template-based video generation."""
    logger.info(f"templates action={action} template_id={template_id}")
    try:
        client = await get_api_client()

        if action == "list":
            return await client.list_templates()

        elif action == "get":
            if not template_id:
                return MCPTemplateDetailsResponse(
                    error="template_id is required for 'get' action"
                )
            return await client.get_template_details(template_id)

        elif action == "generate":
            if not template_id:
                return MCPTemplateVideoGenerateResponse(
                    error="template_id is required for 'generate' action"
                )
            return await client.generate_video_from_template(
                template_id=template_id,
                variables=variables,
                title=title,
                test=test,
                caption=caption,
            )

        else:
            return MCPListTemplatesResponse(error=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"templates action={action} error: {e}")
        return MCPListTemplatesResponse(error=str(e))


# ==================== Assets Resource ====================


@mcp.tool(
    name="assets",
    description=(
        "Upload and manage media files (images, videos, audio). "
        "USE CASES: backgrounds, Avatar IV photos, custom audio. "
        "Actions: "
        "'list' - get all assets with id, name, type, and url; "
        "'upload' - upload file (REQUIRED: file_path; returns asset_id); "
        "'delete' - remove asset (REQUIRED: asset_id). "
        "NOTE: For Avatar IV, upload photo first - asset_id is the image_key."
    ),
)
async def assets(
    action: Literal["list", "upload", "delete"],
    file_path: str | None = None,
    asset_id: str | None = None,
) -> MCPAssetListResponse | MCPAssetUploadResponse | MCPAssetDeleteResponse:
    """Manage media asset resources."""
    logger.info(f"assets action={action} file_path={file_path} asset_id={asset_id}")
    try:
        client = await get_api_client()

        if action == "list":
            return await client.list_assets()

        elif action == "upload":
            if not file_path:
                return MCPAssetUploadResponse(
                    error="file_path is required for 'upload' action"
                )
            return await client.upload_asset(file_path)

        elif action == "delete":
            if not asset_id:
                return MCPAssetDeleteResponse(
                    error="asset_id is required for 'delete' action",
                    success=False,
                )
            return await client.delete_asset(asset_id)

        else:
            return MCPAssetListResponse(error=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"assets action={action} error: {e}")
        if action == "upload":
            return MCPAssetUploadResponse(error=str(e))
        if action == "delete":
            return MCPAssetDeleteResponse(error=str(e), success=False)
        return MCPAssetListResponse(error=str(e))


# ==================== Folders Resource ====================


@mcp.tool(
    name="folders",
    description=(
        "Organize videos and assets into folders. "
        "OPTIONAL: Use folders to keep your HeyGen workspace organized. "
        "Actions: "
        "'list' - get all folders with id and name; "
        "'create' - create a new folder (REQUIRED: name); "
        "'rename' - rename a folder (REQUIRED: folder_id, name); "
        "'trash' - move folder to trash (REQUIRED: folder_id); "
        "'restore' - recover folder from trash (REQUIRED: folder_id)."
    ),
)
async def folders(
    action: Literal["list", "create", "rename", "trash", "restore"],
    folder_id: str | None = None,
    name: str | None = None,
) -> (
    MCPFolderListResponse
    | MCPFolderCreateResponse
    | MCPFolderUpdateResponse
    | MCPFolderTrashResponse
    | MCPFolderRestoreResponse
):
    """Manage folder resources for organizing content."""
    logger.info(f"folders action={action} folder_id={folder_id} name={name}")
    try:
        client = await get_api_client()

        if action == "list":
            return await client.list_folders()

        elif action == "create":
            if not name:
                return MCPFolderCreateResponse(
                    error="name is required for 'create' action"
                )
            return await client.create_folder(name)

        elif action == "rename":
            if not folder_id:
                return MCPFolderUpdateResponse(
                    error="folder_id is required for 'rename' action",
                    success=False,
                )
            if not name:
                return MCPFolderUpdateResponse(
                    error="name is required for 'rename' action",
                    success=False,
                )
            return await client.update_folder(folder_id, name)

        elif action == "trash":
            if not folder_id:
                return MCPFolderTrashResponse(
                    error="folder_id is required for 'trash' action",
                    success=False,
                )
            return await client.trash_folder(folder_id)

        elif action == "restore":
            if not folder_id:
                return MCPFolderRestoreResponse(
                    error="folder_id is required for 'restore' action",
                    success=False,
                )
            return await client.restore_folder(folder_id)

        else:
            return MCPFolderListResponse(error=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"folders action={action} error: {e}")
        if action == "create":
            return MCPFolderCreateResponse(error=str(e))
        if action == "rename":
            return MCPFolderUpdateResponse(error=str(e), success=False)
        if action == "trash":
            return MCPFolderTrashResponse(error=str(e), success=False)
        if action == "restore":
            return MCPFolderRestoreResponse(error=str(e), success=False)
        return MCPFolderListResponse(error=str(e))


# ==================== CLI ====================


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="HeyGen MCP Server")
    parser.add_argument(
        "--api-key",
        help="HeyGen API key. Or set HEYGEN_API_KEY environment variable.",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind the server to."
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind the server to."
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def main():
    """Run the MCP server."""
    args = parse_args()

    # Configure debug logging if requested
    if args.debug:
        logging.getLogger("heygen_mcp").setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Check if API key is provided or in environment
    if args.api_key:
        os.environ["HEYGEN_API_KEY"] = args.api_key

    # Verify API key is set
    if not os.getenv("HEYGEN_API_KEY"):
        print("ERROR: HeyGen API key not provided.")
        print(
            "Please set it using --api-key or the HEYGEN_API_KEY environment variable."
        )
        sys.exit(1)

    logger.info("Starting HeyGen MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
