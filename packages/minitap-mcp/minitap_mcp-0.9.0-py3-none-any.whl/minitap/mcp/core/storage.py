"""Storage utilities for uploading local files to remote storage.

This module provides functionality to upload local files (like screenshots)
to the MaaS API storage backend and get presigned URLs that can be passed
to remote MCP tools.
"""

import base64
import uuid
from pathlib import Path

import httpx

from minitap.mcp.core.config import settings
from minitap.mcp.core.logging_config import get_logger

logger = get_logger(__name__)


class StorageUploadError(Exception):
    """Error raised when file upload fails."""

    pass


def _get_api_key() -> str:
    """Get the API key from settings.

    Returns:
        The API key string

    Raises:
        StorageUploadError: If API key is not configured
    """
    api_key = settings.MINITAP_API_KEY.get_secret_value() if settings.MINITAP_API_KEY else None
    if not api_key:
        raise StorageUploadError("MINITAP_API_KEY is required for file uploads")
    return api_key


def _generate_filename(content_type: str) -> str:
    """Generate a unique filename based on content type.

    Args:
        content_type: MIME type of the file

    Returns:
        UUID-based filename with appropriate extension
    """
    ext = _get_extension_from_mime_type(content_type)
    return f"{uuid.uuid4()}.{ext}"


async def _get_signed_upload_url(
    client: httpx.AsyncClient,
    filename: str,
    api_key: str,
) -> str:
    """Get a signed upload URL from the MaaS API.

    Args:
        client: HTTP client to use for the request
        filename: Name of the file to upload
        api_key: API key for authentication

    Returns:
        Signed upload URL

    Raises:
        StorageUploadError: If request fails or no URL is returned
    """
    base_url = settings.MINITAP_API_BASE_URL
    endpoint = f"{base_url}/storage/signed-upload"

    try:
        logger.debug("Requesting signed upload URL", filename=filename)
        response = await client.get(
            endpoint,
            params={"filenames": filename},
            headers={"Authorization": f"Bearer {api_key}"},
        )

        if response.status_code != 200:
            logger.error(
                "Failed to get signed upload URL",
                status_code=response.status_code,
                response=response.text,
            )
            raise StorageUploadError(
                f"Failed to get signed upload URL: HTTP {response.status_code}"
            )

        signed_urls = response.json().get("signed_urls", {})
        if filename not in signed_urls:
            raise StorageUploadError(f"No signed URL returned for {filename}")

        logger.debug("Got signed upload URL", filename=filename)
        return signed_urls[filename]

    except httpx.TimeoutException as e:
        logger.error("Signed URL request timed out", error=str(e))
        raise StorageUploadError("Signed URL request timed out") from e
    except httpx.RequestError as e:
        logger.error("Signed URL request failed", error=str(e))
        raise StorageUploadError(f"Signed URL request failed: {str(e)}") from e
    except StorageUploadError:
        raise
    except Exception as e:
        logger.error("Unexpected error getting signed URL", error=str(e))
        raise StorageUploadError(f"Unexpected error: {str(e)}") from e


async def _upload_to_signed_url(
    client: httpx.AsyncClient,
    url: str,
    content: bytes,
    content_type: str,
    filename: str,
) -> None:
    """Upload content to a signed URL.

    Args:
        client: HTTP client to use for the request
        url: Signed upload URL
        content: File content as bytes
        content_type: MIME type of the content
        filename: Filename (for logging)

    Raises:
        StorageUploadError: If upload fails
    """
    try:
        logger.debug("Uploading file to storage", filename=filename, size=len(content))
        response = await client.put(
            url,
            content=content,
            headers={"Content-Type": content_type},
        )

        if response.status_code not in (200, 201):
            logger.error(
                "Failed to upload file",
                status_code=response.status_code,
                response=response.text,
            )
            raise StorageUploadError(f"Failed to upload file: HTTP {response.status_code}")

        logger.info("File uploaded successfully", filename=filename)

    except httpx.TimeoutException as e:
        logger.error("Upload request timed out", error=str(e))
        raise StorageUploadError("Upload request timed out") from e
    except httpx.RequestError as e:
        logger.error("Upload request failed", error=str(e))
        raise StorageUploadError(f"Upload request failed: {str(e)}") from e
    except StorageUploadError:
        raise
    except Exception as e:
        logger.error("Unexpected error during upload", error=str(e))
        raise StorageUploadError(f"Unexpected error: {str(e)}") from e


async def upload_file_to_storage(
    file_content: bytes,
    filename: str | None = None,
    content_type: str = "image/png",
) -> str:
    """Upload file content to remote storage and return the filename.

    This function:
    1. Gets a signed upload URL from the MaaS API
    2. Uploads the file content to that URL
    3. Returns the filename for use with remote MCP tools

    Args:
        file_content: The file content as bytes
        filename: Optional filename (will generate UUID-based name if not provided)
        content_type: MIME type of the file (default: image/png)

    Returns:
        Filename of the uploaded file (to be used with remote MCP tools)

    Raises:
        StorageUploadError: If upload fails at any step
    """
    api_key = _get_api_key()
    filename = filename or _generate_filename(content_type)

    async with httpx.AsyncClient(timeout=30.0) as client:
        signed_url = await _get_signed_upload_url(client, filename, api_key)
        await _upload_to_signed_url(client, signed_url, file_content, content_type, filename)

    return filename


async def upload_screenshot_to_storage(screenshot_base64: str) -> str:
    """Upload a base64-encoded screenshot to storage.

    Convenience function for uploading screenshots captured from devices.

    Args:
        screenshot_base64: Base64-encoded screenshot data

    Returns:
        Filename of the uploaded screenshot

    Raises:
        StorageUploadError: If upload fails
    """

    try:
        screenshot_bytes = base64.b64decode(screenshot_base64)
    except Exception as e:
        raise StorageUploadError(f"Invalid base64 data: {str(e)}") from e

    return await upload_file_to_storage(
        file_content=screenshot_bytes,
        content_type="image/png",
    )


async def upload_local_file_to_storage(file_path: str | Path) -> str:
    """Upload a local file to storage.

    Args:
        file_path: Path to the local file

    Returns:
        Public download URL for the uploaded file

    Raises:
        StorageUploadError: If file doesn't exist or upload fails
    """
    path = Path(file_path)

    if not path.exists():
        raise StorageUploadError(f"File not found: {file_path}")

    mime_type = _guess_mime_type(path.suffix)
    file_content = path.read_bytes()

    return await upload_file_to_storage(
        file_content=file_content,
        filename=f"{uuid.uuid4()}{path.suffix}",
        content_type=mime_type,
    )


def _get_extension_from_mime_type(mime_type: str) -> str:
    """Get file extension from MIME type."""
    mime_to_ext = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/gif": "gif",
        "image/webp": "webp",
        "application/json": "json",
        "text/plain": "txt",
    }
    return mime_to_ext.get(mime_type, "bin")


def _guess_mime_type(extension: str) -> str:
    """Guess MIME type from file extension."""
    ext = extension.lower().lstrip(".")
    ext_to_mime = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "json": "application/json",
        "txt": "text/plain",
    }
    return ext_to_mime.get(ext, "application/octet-stream")


class StorageDownloadError(Exception):
    """Error raised when file download fails."""

    pass


async def get_trajectory_gif_download_url(task_run_id: str) -> str:
    """Get a signed download URL for a trajectory GIF.

    This function calls the MaaS API to get a signed S3 download URL for the
    trajectory GIF associated with a task run.

    Args:
        task_run_id: The ID of the task run to get the GIF for

    Returns:
        The signed download URL for the GIF

    Raises:
        StorageDownloadError: If the request fails or no URL is returned
    """
    try:
        api_key = _get_api_key()
    except StorageUploadError as e:
        raise StorageDownloadError(str(e)) from e
    base_url = settings.MINITAP_API_BASE_URL
    endpoint = f"{base_url}/storage/trajectory-gif-download/{task_run_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.debug("Requesting trajectory GIF download URL", task_run_id=task_run_id)
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if response.status_code == 404:
                raise StorageDownloadError(f"Trajectory GIF not found for task run: {task_run_id}")

            if response.status_code != 200:
                logger.error(
                    "Failed to get trajectory GIF download URL",
                    status_code=response.status_code,
                    response=response.text,
                )
                raise StorageDownloadError(
                    f"Failed to get trajectory GIF download URL: HTTP {response.status_code}"
                )

            data = response.json()
            download_url = data.get("signed_url")
            if not download_url:
                raise StorageDownloadError("No download URL returned in response")

            logger.debug("Got trajectory GIF download URL", task_run_id=task_run_id)
            return download_url

        except httpx.TimeoutException as e:
            logger.error("Trajectory GIF download URL request timed out", error=str(e))
            raise StorageDownloadError("Request timed out") from e
        except httpx.RequestError as e:
            logger.error("Trajectory GIF download URL request failed", error=str(e))
            raise StorageDownloadError(f"Request failed: {str(e)}") from e
        except StorageDownloadError:
            raise
        except Exception as e:
            logger.error("Unexpected error getting trajectory GIF download URL", error=str(e))
            raise StorageDownloadError(f"Unexpected error: {str(e)}") from e


async def download_trajectory_gif(task_run_id: str, download_path: str | Path) -> Path:
    """Download a trajectory GIF to a local path.

    This function:
    1. Gets a signed download URL from the MaaS API
    2. Downloads the GIF from that URL
    3. Saves it to the specified local path

    Args:
        task_run_id: The ID of the task run to download the GIF for
        download_path: Directory path where the GIF will be saved.
                      The file will be saved as {task_run_id}/trajectory.gif

    Returns:
        The full path to the downloaded GIF file

    Raises:
        StorageDownloadError: If download fails at any step
    """
    download_dir = Path(download_path) / task_run_id

    try:
        download_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise StorageDownloadError(f"Failed to create download directory: {e}") from e

    download_url = await get_trajectory_gif_download_url(task_run_id)

    output_file = download_dir / "trajectory.gif"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            logger.info(
                "Downloading trajectory GIF", task_run_id=task_run_id, path=str(output_file)
            )
            response = await client.get(download_url)

            if response.status_code != 200:
                raise StorageDownloadError(f"Failed to download GIF: HTTP {response.status_code}")

            output_file.write_bytes(response.content)
            logger.info(
                "Trajectory GIF downloaded successfully",
                task_run_id=task_run_id,
                path=str(output_file),
                size=len(response.content),
            )

            return output_file

        except httpx.TimeoutException as e:
            logger.error("GIF download timed out", error=str(e))
            raise StorageDownloadError("Download timed out") from e
        except httpx.RequestError as e:
            logger.error("GIF download request failed", error=str(e))
            raise StorageDownloadError(f"Download failed: {str(e)}") from e
        except StorageDownloadError:
            raise
        except Exception as e:
            logger.error("Unexpected error downloading GIF", error=str(e))
            raise StorageDownloadError(f"Unexpected error: {str(e)}") from e
