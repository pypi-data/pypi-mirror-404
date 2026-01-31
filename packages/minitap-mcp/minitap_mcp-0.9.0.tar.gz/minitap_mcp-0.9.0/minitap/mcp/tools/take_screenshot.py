"""Simple screenshot capture tool - returns raw base64 image without LLM analysis."""

import base64

from mcp.types import ImageContent
from pydantic import Field

from minitap.mcp.core.decorators import handle_tool_errors
from minitap.mcp.core.device import capture_screenshot, find_mobile_device
from minitap.mcp.main import mcp
from minitap.mcp.server.cloud_mobile import (
    check_cloud_mobile_status,
    get_cloud_mobile_id,
    get_cloud_screenshot,
)


@mcp.tool(
    name="take_screenshot",
    description="""
    Capture a screenshot from the connected mobile device.
    Returns the raw base64-encoded PNG image directly without any LLM analysis.
    Use this when you need the screenshot image for display or further processing.
    """,
)
@handle_tool_errors
async def take_screenshot(
    device_id: str | None = Field(
        default=None,
        description="ID of the device to capture screenshot from. "
        "If not provided, the first available device is used.",
    ),
) -> list[ImageContent]:
    """Capture screenshot and return as base64 image content."""
    cloud_mobile_id = get_cloud_mobile_id()

    if cloud_mobile_id:
        # Cloud mode: use cloud screenshot API
        await check_cloud_mobile_status(cloud_mobile_id)
        screenshot_bytes = await get_cloud_screenshot(cloud_mobile_id)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
    else:
        # Local mode: capture from local device
        device = find_mobile_device(device_id=device_id)
        screenshot_base64 = capture_screenshot(device)

    return [
        ImageContent(
            type="image",
            data=screenshot_base64,
            mimeType="image/png",
        )
    ]
