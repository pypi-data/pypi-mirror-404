"""HeyGen API client for interacting with the HeyGen API."""

import importlib.metadata
import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .models import (
    AssetDeleteResponse,
    AssetListResponse,
    AssetUploadResponse,
    AvatarDetailsResponse,
    AvatarGroupListResponse,
    AvatarIVVideoRequest,
    AvatarIVVideoResponse,
    AvatarsInGroupResponse,
    AvatarsV2Response,
    FolderCreateResponse,
    FolderListResponse,
    FolderTrashRestoreResponse,
    FolderUpdateResponse,
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
    RemainingQuotaResponse,
    TemplateDetailsResponse,
    TemplatesResponse,
    TemplateVideoGenerateResponse,
    UserInfoResponse,
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoListResponse,
    VideoStatusResponse,
    VoicesResponse,
)

logger = logging.getLogger(__name__)


# Retry configuration
RETRY_MAX_ATTEMPTS = 3
RETRY_MIN_WAIT_SECONDS = 1
RETRY_MAX_WAIT_SECONDS = 10

# HTTP status codes that should trigger a retry
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class RetryableHTTPError(Exception):
    """Exception for HTTP errors that should be retried."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


class HeyGenApiClient:
    """Client for interacting with the HeyGen API."""

    DEFAULT_TIMEOUT = 60.0
    BASE_URL = "https://api.heygen.com/v2"

    def __init__(
        self,
        api_key: str,
        max_retries: int = RETRY_MAX_ATTEMPTS,
        retry_min_wait: float = RETRY_MIN_WAIT_SECONDS,
        retry_max_wait: float = RETRY_MAX_WAIT_SECONDS,
    ):
        """Initialize the API client with the API key.

        Args:
            api_key: HeyGen API key for authentication.
            max_retries: Maximum number of retry attempts (default: 3).
            retry_min_wait: Minimum wait time between retries in seconds (default: 1).
            retry_max_wait: Maximum wait time between retries in seconds (default: 10).
        """
        self.api_key = api_key
        self._max_retries = max_retries
        self._retry_min_wait = retry_min_wait
        self._retry_max_wait = retry_max_wait
        self._version = self._get_version()
        self._user_agent = f"heygen-mcp/{self._version}"
        self._client = httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT)

    @staticmethod
    def _get_version() -> str:
        """Get the package version."""
        try:
            return importlib.metadata.version("heygen-mcp")
        except importlib.metadata.PackageNotFoundError:
            return "unknown"

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "HeyGenApiClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    def _get_headers(self) -> Dict[str, str]:
        """Return the headers needed for API requests."""
        return {
            "Accept": "application/json",
            "X-Api-Key": self.api_key,
            "User-Agent": self._user_agent,
        }

    async def _make_request_with_retry(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request with automatic retry on transient failures.

        Uses exponential backoff for retries on timeout and server errors.

        Args:
            endpoint: The API endpoint to call (without the base URL).
            method: HTTP method to use (GET or POST).
            data: JSON payload for POST requests.

        Returns:
            The JSON response from the API.

        Raises:
            httpx.RequestError: If there's a network-related error after all retries.
            httpx.HTTPStatusError: If the API returns a non-retryable error status.
            RetryError: If all retry attempts are exhausted.
        """

        @retry(
            retry=retry_if_exception_type((RetryableHTTPError, httpx.TimeoutException)),
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(
                multiplier=1,
                min=self._retry_min_wait,
                max=self._retry_max_wait,
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        async def _request() -> Dict[str, Any]:
            url = f"{self.BASE_URL}/{endpoint}"
            headers = self._get_headers()

            if method.upper() == "GET":
                response = await self._client.get(url, headers=headers)
            elif method.upper() == "POST":
                headers["Content-Type"] = "application/json"
                response = await self._client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check if this is a retryable error
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise RetryableHTTPError(
                    response.status_code,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                )

            response.raise_for_status()
            return response.json()

        try:
            return await _request()
        except RetryableHTTPError as e:
            # Convert to HTTPStatusError for consistent error handling
            raise httpx.HTTPStatusError(
                str(e),
                request=httpx.Request(method, f"{self.BASE_URL}/{endpoint}"),
                response=httpx.Response(e.status_code),
            ) from e

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the specified API endpoint.

        This method wraps _make_request_with_retry to provide automatic
        retry handling for transient failures (timeouts, 502, 503, etc.).

        Args:
            endpoint: The API endpoint to call (without the base URL).
            method: HTTP method to use (GET or POST).
            data: JSON payload for POST requests.

        Returns:
            The JSON response from the API.

        Raises:
            httpx.RequestError: If there's a network-related error after all retries.
            httpx.HTTPStatusError: If the API returns an error status code.
        """
        return await self._make_request_with_retry(endpoint, method, data)

    async def _handle_api_request(
        self,
        api_call,
        response_model_class,
        mcp_response_class,
        error_msg: str,
        **kwargs,
    ):
        """Generic handler for API requests to reduce code duplication.

        Args:
            api_call: Async function to call the API.
            response_model_class: Pydantic model class for validating the API response.
            mcp_response_class: Pydantic model class for the MCP response.
            error_msg: Error message to return if the validation fails.
            **kwargs: Additional arguments for the response transformation.

        Returns:
            An MCP response object.
        """
        try:
            result = await api_call()
            validated_response = response_model_class.model_validate(result)

            if hasattr(validated_response, "data") and validated_response.data:
                return self._transform_to_mcp_response(
                    validated_response.data, mcp_response_class, **kwargs
                )
            elif validated_response.error:
                return mcp_response_class(error=validated_response.error)
            else:
                return mcp_response_class(error=error_msg)

        except RetryError as exc:
            # All retry attempts exhausted
            return mcp_response_class(
                error=f"Request failed after {self._max_retries} retries: {exc}"
            )
        except httpx.TimeoutException as exc:
            return mcp_response_class(error=f"Request timed out: {exc}")
        except httpx.RequestError as exc:
            return mcp_response_class(error=f"HTTP Request failed: {exc}")
        except httpx.HTTPStatusError as exc:
            return mcp_response_class(
                error=f"HTTP Error: {exc.response.status_code} - {exc.response.text}"
            )
        except Exception as e:
            return mcp_response_class(error=f"An unexpected error occurred: {e}")

    def _transform_to_mcp_response(self, data, mcp_response_class, **kwargs):
        """Transform API response data to MCP response format.

        Args:
            data: The API response data.
            mcp_response_class: The MCP response class to instantiate.
            **kwargs: Additional parameters for the response.

        Returns:
            An instance of the MCP response class.
        """
        if "transform_func" in kwargs:
            transform_func = kwargs.pop("transform_func")
            return transform_func(data, mcp_response_class)

        processed_kwargs = {}
        for key, value in kwargs.items():
            if callable(value):
                processed_kwargs[key] = value(data)
            else:
                processed_kwargs[key] = value

        return mcp_response_class(**processed_kwargs)

    # ==================== Credits & User ====================

    async def get_remaining_credits(self) -> MCPGetCreditsResponse:
        """Get the remaining credits from the API."""

        async def api_call():
            return await self._make_request("user/remaining_quota")

        def transform_data(data, mcp_class):
            return mcp_class(remaining_credits=int(data.remaining_quota / 60))

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=RemainingQuotaResponse,
            mcp_response_class=MCPGetCreditsResponse,
            error_msg="No quota information found.",
            transform_func=transform_data,
        )

    async def get_user_info(self) -> MCPUserInfoResponse:
        """Get the current user's profile information."""

        async def api_call():
            return await self._make_request("../v1/user/me")

        try:
            result = await api_call()
            validated = UserInfoResponse.model_validate(result)

            if validated.data:
                return MCPUserInfoResponse(
                    username=validated.data.username,
                    email=validated.data.email,
                    first_name=validated.data.first_name,
                    last_name=validated.data.last_name,
                )
            return MCPUserInfoResponse(error="No user information found.")

        except httpx.RequestError as exc:
            return MCPUserInfoResponse(error=f"HTTP Request failed: {exc}")
        except httpx.HTTPStatusError as exc:
            return MCPUserInfoResponse(
                error=f"HTTP Error: {exc.response.status_code} - {exc.response.text}"
            )
        except Exception as e:
            return MCPUserInfoResponse(error=f"An unexpected error occurred: {e}")

    # ==================== Voices ====================

    async def get_voices(self) -> MCPVoicesResponse:
        """Get the list of available voices from the API."""

        async def api_call():
            return await self._make_request("voices")

        def transform_data(data, mcp_class):
            return mcp_class(voices=data.voices[:100] if data.voices else None)

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=VoicesResponse,
            mcp_response_class=MCPVoicesResponse,
            error_msg="No voices found.",
            transform_func=transform_data,
        )

    # ==================== Avatar Groups ====================

    async def list_avatar_groups(
        self, include_public: bool = False
    ) -> MCPAvatarGroupResponse:
        """Get the list of avatar groups from the API.

        Args:
            include_public: Whether to include public avatar groups.

        Returns:
            MCPAvatarGroupResponse with avatar groups.
        """

        async def api_call():
            public_param = "true" if include_public else "false"
            endpoint = f"avatar_group.list?include_public={public_param}"
            return await self._make_request(endpoint)

        def transform_data(data, mcp_class):
            return mcp_class(
                avatar_groups=data.avatar_group_list,
                total_count=data.total_count,
            )

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=AvatarGroupListResponse,
            mcp_response_class=MCPAvatarGroupResponse,
            error_msg="No avatar groups found.",
            transform_func=transform_data,
        )

    async def get_avatars_in_group(self, group_id: str) -> MCPAvatarsInGroupResponse:
        """Get the list of avatars in a specific avatar group.

        Args:
            group_id: The ID of the avatar group.

        Returns:
            MCPAvatarsInGroupResponse with avatars.
        """

        async def api_call():
            return await self._make_request(f"avatar_group/{group_id}/avatars")

        def transform_data(data, mcp_class):
            return mcp_class(avatars=data.avatar_list)

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=AvatarsInGroupResponse,
            mcp_response_class=MCPAvatarsInGroupResponse,
            error_msg="No avatars found in the group.",
            transform_func=transform_data,
        )

    # ==================== Avatars ====================

    async def list_avatars(self) -> MCPListAvatarsResponse:
        """Get the list of all available avatars from the API."""

        async def api_call():
            return await self._make_request("avatars")

        def transform_data(data, mcp_class):
            avatars = data.avatars if data.avatars else []
            return mcp_class(avatars=avatars, total_count=len(avatars))

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=AvatarsV2Response,
            mcp_response_class=MCPListAvatarsResponse,
            error_msg="No avatars found.",
            transform_func=transform_data,
        )

    async def get_avatar_details(self, avatar_id: str) -> MCPAvatarDetailsResponse:
        """Get detailed information about a specific avatar.

        Args:
            avatar_id: The ID of the avatar.

        Returns:
            MCPAvatarDetailsResponse with avatar details.
        """

        async def api_call():
            return await self._make_request(f"avatar/{avatar_id}/details")

        def transform_data(data, mcp_class):
            return mcp_class(avatar=data)

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=AvatarDetailsResponse,
            mcp_response_class=MCPAvatarDetailsResponse,
            error_msg="Avatar not found.",
            transform_func=transform_data,
        )

    # ==================== Video Generation ====================

    async def generate_avatar_video(
        self, video_request: VideoGenerateRequest
    ) -> MCPVideoGenerateResponse:
        """Generate an avatar video using the HeyGen API.

        Args:
            video_request: Video generation request parameters.

        Returns:
            MCPVideoGenerateResponse with video generation status.
        """

        async def api_call():
            return await self._make_request(
                "video/generate",
                method="POST",
                data=video_request.model_dump(exclude_none=True),
            )

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=VideoGenerateResponse,
            mcp_response_class=MCPVideoGenerateResponse,
            error_msg="No video generation data returned.",
            video_id=lambda d: d.get("video_id"),
            task_id=lambda d: d.get("task_id"),
            video_url=lambda d: d.get("video_url"),
            status=lambda d: d.get("status"),
        )

    async def get_video_status(self, video_id: str) -> MCPVideoStatusResponse:
        """Get the status of a generated video from the API.

        Args:
            video_id: The ID of the video.

        Returns:
            MCPVideoStatusResponse with video status.
        """

        async def api_call():
            endpoint = f"../v1/video_status.get?video_id={video_id}"
            return await self._make_request(endpoint)

        try:
            result = await api_call()
            validated_response = VideoStatusResponse.model_validate(result)
            data = validated_response.data

            error_details = None
            if data.error:
                error_details = {
                    "code": data.error.code,
                    "message": data.error.message,
                    "detail": data.error.detail,
                }

            return MCPVideoStatusResponse(
                video_id=data.id,
                status=data.status,
                duration=data.duration,
                video_url=data.video_url,
                gif_url=data.gif_url,
                thumbnail_url=data.thumbnail_url,
                created_at=data.created_at,
                error_details=error_details,
            )
        except httpx.RequestError as exc:
            return MCPVideoStatusResponse(error=f"HTTP Request failed: {exc}")
        except httpx.HTTPStatusError as exc:
            return MCPVideoStatusResponse(
                error=f"HTTP Error: {exc.response.status_code} - {exc.response.text}"
            )
        except Exception as e:
            return MCPVideoStatusResponse(error=f"An unexpected error occurred: {e}")

    async def list_videos(self, token: Optional[str] = None) -> MCPVideoListResponse:
        """List all videos in the HeyGen account.

        Args:
            token: Optional pagination token for fetching next page of results.

        Returns:
            MCPVideoListResponse with list of videos.
        """

        async def api_call():
            endpoint = "../v1/video.list"
            if token:
                endpoint = f"{endpoint}?token={token}"
            return await self._make_request(endpoint)

        def transform_data(data, mcp_class):
            videos = data.videos if data.videos else []
            return mcp_class(
                videos=videos,
                total=len(videos),
                token=data.token,
            )

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=VideoListResponse,
            mcp_response_class=MCPVideoListResponse,
            error_msg="Failed to list videos.",
            transform_func=transform_data,
        )

    async def generate_avatar_iv_video(
        self, request: AvatarIVVideoRequest
    ) -> MCPAvatarIVVideoResponse:
        """Generate an Avatar IV video using advanced photorealistic avatar technology.

        Avatar IV uses AI-powered motion and expressions to create videos from photos.

        Args:
            request: Avatar IV video generation request parameters including:
                - image_key: Asset ID of the uploaded photo
                - video_title: Title for the generated video
                - script: Text the avatar will speak
                - voice_id: Voice ID for the avatar
                - audio_url: Optional custom audio URL
                - audio_asset_id: Optional HeyGen asset ID for audio
                - custom_motion_prompt: Optional motion guidance
                - enhance_custom_motion_prompt: Optional AI motion enhancement

        Returns:
            MCPAvatarIVVideoResponse with video_id for status tracking.
        """

        async def api_call():
            # Build request data, excluding None values
            request_data = {
                k: v for k, v in request.model_dump().items() if v is not None
            }
            return await self._make_request(
                "video/av4/generate",
                method="POST",
                data=request_data,
            )

        def transform_data(data, mcp_class):
            return mcp_class(video_id=data.video_id)

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=AvatarIVVideoResponse,
            mcp_response_class=MCPAvatarIVVideoResponse,
            error_msg="Failed to generate Avatar IV video.",
            transform_func=transform_data,
        )

    # ==================== Templates ====================

    async def list_templates(self) -> MCPListTemplatesResponse:
        """Get the list of templates from the API."""

        async def api_call():
            return await self._make_request("templates")

        def transform_data(data, mcp_class):
            templates = data.templates if data.templates else []
            return mcp_class(templates=templates, total_count=len(templates))

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=TemplatesResponse,
            mcp_response_class=MCPListTemplatesResponse,
            error_msg="No templates found.",
            transform_func=transform_data,
        )

    async def get_template_details(
        self, template_id: str
    ) -> MCPTemplateDetailsResponse:
        """Get detailed information about a specific template including variables.

        Args:
            template_id: The ID of the template.

        Returns:
            MCPTemplateDetailsResponse with template details.
        """

        async def api_call():
            return await self._make_request(f"../v3/template/{template_id}")

        def transform_data(data, mcp_class):
            return mcp_class(template=data)

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=TemplateDetailsResponse,
            mcp_response_class=MCPTemplateDetailsResponse,
            error_msg="Template not found.",
            transform_func=transform_data,
        )

    async def generate_video_from_template(
        self,
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        test: bool = False,
        caption: bool = False,
    ) -> MCPTemplateVideoGenerateResponse:
        """Generate a video from a template with variable replacements.

        Args:
            template_id: The ID of the template.
            variables: Variable name to value mapping for replacement.
            title: Title for the generated video.
            test: Whether to generate a test video.
            caption: Whether to include captions.

        Returns:
            MCPTemplateVideoGenerateResponse with video ID.
        """

        async def api_call():
            request_data: Dict[str, Any] = {
                "test": test,
                "caption": caption,
            }
            if title:
                request_data["title"] = title
            if variables:
                request_data["variables"] = variables

            return await self._make_request(
                f"template/{template_id}/generate",
                method="POST",
                data=request_data,
            )

        def transform_data(data, mcp_class):
            return mcp_class(video_id=data.video_id)

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=TemplateVideoGenerateResponse,
            mcp_response_class=MCPTemplateVideoGenerateResponse,
            error_msg="Failed to generate video from template.",
            transform_func=transform_data,
        )

    # ==================== Asset Methods ====================

    async def upload_asset(
        self,
        file_path: str,
    ) -> MCPAssetUploadResponse:
        """Upload a media file (image, video, or audio) to HeyGen.

        Note: The upload API uses a different base URL (upload.heygen.com).

        Args:
            file_path: Path to the file to upload.

        Returns:
            MCPAssetUploadResponse with asset_id and url.
        """
        import mimetypes

        upload_url = "https://upload.heygen.com/v1/asset"

        try:
            # Determine MIME type - API only accepts specific types
            mime_type, _ = mimetypes.guess_type(file_path)
            allowed_types = {
                "image/png",
                "image/jpeg",
                "video/mp4",
                "video/webm",
                "audio/mpeg",
            }
            if mime_type not in allowed_types:
                return MCPAssetUploadResponse(
                    error=f"Unsupported file type: {mime_type}. "
                    f"Allowed types: {', '.join(sorted(allowed_types))}"
                )

            # Read the file as raw binary
            with open(file_path, "rb") as f:
                file_content = f.read()

            # API expects raw binary data with Content-Type header
            headers = {
                "X-Api-Key": self.api_key,
                "User-Agent": self._user_agent,
                "Content-Type": mime_type,
            }

            response = await self._client.post(
                upload_url,
                headers=headers,
                content=file_content,
            )

            if response.status_code in RETRYABLE_STATUS_CODES:
                raise RetryableHTTPError(
                    response.status_code,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                )

            response.raise_for_status()
            result = response.json()

            parsed = AssetUploadResponse.model_validate(result)

            if parsed.error:
                return MCPAssetUploadResponse(error=parsed.error)

            if parsed.data:
                return MCPAssetUploadResponse(
                    asset_id=parsed.data.id,
                    url=parsed.data.url,
                )

            return MCPAssetUploadResponse(error="Upload failed: No data returned.")

        except FileNotFoundError:
            return MCPAssetUploadResponse(error=f"File not found: {file_path}")
        except httpx.HTTPStatusError as e:
            return MCPAssetUploadResponse(error=f"Upload failed: {e}")
        except Exception as e:
            return MCPAssetUploadResponse(error=f"Upload error: {e}")

    async def list_assets(self) -> MCPAssetListResponse:
        """List all assets in the HeyGen account.

        Returns:
            MCPAssetListResponse with list of assets.
        """

        async def api_call():
            return await self._make_request("../v1/asset/list")

        def transform_data(data, mcp_class):
            return mcp_class(
                assets=data.assets if data.assets else [],
                total=data.total,
            )

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=AssetListResponse,
            mcp_response_class=MCPAssetListResponse,
            error_msg="Failed to list assets.",
            transform_func=transform_data,
        )

    async def delete_asset(self, asset_id: str) -> MCPAssetDeleteResponse:
        """Delete a specific asset by its ID.

        Args:
            asset_id: The ID of the asset to delete.

        Returns:
            MCPAssetDeleteResponse indicating success or failure.
        """

        async def api_call():
            return await self._make_request(
                f"../v1/asset/{asset_id}/delete",
                method="POST",
            )

        try:
            result = await api_call()
            parsed = AssetDeleteResponse.model_validate(result)

            if parsed.error:
                return MCPAssetDeleteResponse(error=parsed.error, success=False)

            return MCPAssetDeleteResponse(success=True, asset_id=asset_id)

        except httpx.HTTPStatusError as e:
            return MCPAssetDeleteResponse(
                error=f"Failed to delete asset: {e}",
                success=False,
            )
        except Exception as e:
            return MCPAssetDeleteResponse(
                error=f"Error deleting asset: {e}",
                success=False,
            )

    # ==================== Folder Methods ====================

    async def list_folders(self) -> MCPFolderListResponse:
        """List all folders in the HeyGen account.

        Returns:
            MCPFolderListResponse with list of folders.
        """

        async def api_call():
            return await self._make_request("../v1/folders")

        def transform_data(data, mcp_class):
            return mcp_class(
                folders=data.folders if data.folders else [],
                total=data.total,
                token=data.token,
            )

        return await self._handle_api_request(
            api_call=api_call,
            response_model_class=FolderListResponse,
            mcp_response_class=MCPFolderListResponse,
            error_msg="Failed to list folders.",
            transform_func=transform_data,
        )

    async def create_folder(self, name: str) -> MCPFolderCreateResponse:
        """Create a new folder.

        Args:
            name: The name of the folder to create.

        Returns:
            MCPFolderCreateResponse with folder_id.
        """

        async def api_call():
            return await self._make_request(
                "../v1/folders/create",
                method="POST",
                data={"name": name},
            )

        try:
            result = await api_call()
            parsed = FolderCreateResponse.model_validate(result)

            if parsed.error:
                return MCPFolderCreateResponse(error=parsed.error)

            if parsed.data:
                return MCPFolderCreateResponse(folder_id=parsed.data.id)

            return MCPFolderCreateResponse(error="Failed to create folder.")

        except httpx.HTTPStatusError as e:
            return MCPFolderCreateResponse(error=f"Failed to create folder: {e}")
        except Exception as e:
            return MCPFolderCreateResponse(error=f"Error creating folder: {e}")

    async def update_folder(self, folder_id: str, name: str) -> MCPFolderUpdateResponse:
        """Update (rename) a folder.

        Args:
            folder_id: The ID of the folder to update.
            name: The new name for the folder.

        Returns:
            MCPFolderUpdateResponse indicating success or failure.
        """

        async def api_call():
            return await self._make_request(
                f"../v1/folders/{folder_id}",
                method="POST",
                data={"name": name},
            )

        try:
            result = await api_call()
            parsed = FolderUpdateResponse.model_validate(result)

            if parsed.error:
                return MCPFolderUpdateResponse(error=parsed.error, success=False)

            return MCPFolderUpdateResponse(folder_id=folder_id, success=True)

        except httpx.HTTPStatusError as e:
            return MCPFolderUpdateResponse(
                error=f"Failed to update folder: {e}",
                success=False,
            )
        except Exception as e:
            return MCPFolderUpdateResponse(
                error=f"Error updating folder: {e}",
                success=False,
            )

    async def trash_folder(self, folder_id: str) -> MCPFolderTrashResponse:
        """Move a folder to trash.

        Args:
            folder_id: The ID of the folder to trash.

        Returns:
            MCPFolderTrashResponse indicating success or failure.
        """

        async def api_call():
            return await self._make_request(
                f"../v1/folders/{folder_id}/trash",
                method="POST",
            )

        try:
            result = await api_call()
            parsed = FolderTrashRestoreResponse.model_validate(result)

            if parsed.error:
                return MCPFolderTrashResponse(error=parsed.error, success=False)

            return MCPFolderTrashResponse(folder_id=folder_id, success=True)

        except httpx.HTTPStatusError as e:
            return MCPFolderTrashResponse(
                error=f"Failed to trash folder: {e}",
                success=False,
            )
        except Exception as e:
            return MCPFolderTrashResponse(
                error=f"Error trashing folder: {e}",
                success=False,
            )

    async def restore_folder(self, folder_id: str) -> MCPFolderRestoreResponse:
        """Restore a folder from trash.

        Args:
            folder_id: The ID of the folder to restore.

        Returns:
            MCPFolderRestoreResponse indicating success or failure.
        """

        async def api_call():
            return await self._make_request(
                f"../v1/folders/{folder_id}/restore",
                method="POST",
            )

        try:
            result = await api_call()
            parsed = FolderTrashRestoreResponse.model_validate(result)

            if parsed.error:
                return MCPFolderRestoreResponse(error=parsed.error, success=False)

            return MCPFolderRestoreResponse(folder_id=folder_id, success=True)

        except httpx.HTTPStatusError as e:
            return MCPFolderRestoreResponse(
                error=f"Failed to restore folder: {e}",
                success=False,
            )
        except Exception as e:
            return MCPFolderRestoreResponse(
                error=f"Error restoring folder: {e}",
                success=False,
            )
