"""Tool for uploading device screenshots to remote storage.

This tool captures a screenshot from the connected device and uploads it
to remote storage, returning a filename that can be used with other tools
like figma_compare_screenshot.
"""

import base64

from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult

from minitap.mcp.core.decorators import handle_tool_errors
from minitap.mcp.core.device import capture_screenshot, find_mobile_device
from minitap.mcp.core.logging_config import get_logger
from minitap.mcp.core.storage import StorageUploadError, upload_screenshot_to_storage
from minitap.mcp.main import mcp
from minitap.mcp.server.cloud_mobile import get_cloud_mobile_id, get_cloud_screenshot

logger = get_logger(__name__)


@mcp.tool(
    name="upload_screenshot",
    description="""
    Capture a screenshot from the connected device and upload it to storage.
    
    This tool:
    1. Captures a screenshot from the connected device (local or cloud)
    2. Uploads the screenshot to remote storage
    3. Returns a filename that can be used with other tools
    
    Use this to get a screenshot filename for tools like figma_compare_screenshot
    that require a current_screenshot_filename parameter.
    
    Example workflow:
    1. Call upload_screenshot to get a filename
    2. Use the returned filename with figma_compare_screenshot
    """,
)
@handle_tool_errors
async def upload_screenshot() -> ToolResult:
    """Capture and upload a device screenshot, return the filename."""
    logger.info("Capturing and uploading device screenshot")

    # Step 1: Capture screenshot from device
    cloud_mobile_id = get_cloud_mobile_id()

    if cloud_mobile_id:
        logger.debug("Capturing screenshot from cloud device", device_id=cloud_mobile_id)
        try:
            screenshot_bytes = await get_cloud_screenshot(cloud_mobile_id)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            raise ToolError(f"Failed to capture cloud device screenshot: {e}") from e
    else:
        logger.debug("Capturing screenshot from local device")
        try:
            device = find_mobile_device()
            screenshot_base64 = capture_screenshot(device)
        except Exception as e:
            raise ToolError(f"Failed to capture local device screenshot: {e}") from e

    logger.info("Screenshot captured from device")

    # Step 2: Upload screenshot to storage
    try:
        filename = await upload_screenshot_to_storage(screenshot_base64)
        logger.info("Screenshot uploaded to storage", filename=filename)
    except StorageUploadError as e:
        raise ToolError(f"Failed to upload screenshot: {e}") from e

    return ToolResult(
        content=[
            {
                "type": "text",
                "text": f"Screenshot uploaded successfully.\n\n**Filename:** {filename}",
            }
        ]
    )
