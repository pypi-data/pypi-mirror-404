"""Tool for running manual tasks on a connected mobile device."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from minitap.mobile_use.sdk.types import ManualTaskConfig
from minitap.mobile_use.sdk.types.task import PlatformTaskRequest
from pydantic import Field

from minitap.mcp.core.cloud_apk import install_apk_on_cloud_mobile, upload_apk_to_cloud_mobile
from minitap.mcp.core.config import settings
from minitap.mcp.core.decorators import handle_tool_errors
from minitap.mcp.core.logging_config import get_logger
from minitap.mcp.core.sdk_agent import get_mobile_use_agent
from minitap.mcp.core.storage import StorageDownloadError, download_trajectory_gif
from minitap.mcp.core.task_runs import TaskRunsError, get_latest_task_run_id
from minitap.mcp.main import mcp
from minitap.mcp.server.cloud_mobile import check_cloud_mobile_status

logger = get_logger(__name__)


def _serialize_result(result: Any) -> Any:
    """Convert SDK responses to serializable data for MCP."""
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    if isinstance(result, Mapping):
        return dict(result)
    return result


@mcp.tool(
    name="execute_mobile_command",
    description="""
    Execute a natural language command on a mobile device using the Minitap SDK.
    This tool allows you to control your Android or iOS device using natural language.
    
    Examples:
    - "Open the settings app and tell me the battery level"
    - "Find the first 3 unread emails in Gmail"
    - "Take a screenshot and save it"
    
    APK Deployment (Cloud Mobile Only):
    When CLOUD_MOBILE_NAME is set, you can deploy and test APKs on cloud mobiles:
    - Set apk_path to the path of your locally built APK
    - The APK will be uploaded to cloud storage and installed on the device
    - Requires MINITAP_API_KEY environment variable
    - Must provide locked_app_package when using apk_path
    
    Example with APK deployment:
    execute_mobile_command(
        apk_path="/path/to/app-debug.apk",
        locked_app_package="com.example.myapp",
        goal="Test the login flow with valid credentials"
    )
    
    Note: If apk path is set and no cloud mobile name -> it will raise a tool error
    """,
)
@handle_tool_errors
async def execute_mobile_command(
    goal: str = Field(description="High-level goal describing the action to perform."),
    output_description: str | None = Field(
        default=None,
        description="Optional description of the expected output format. "
        "For example: 'A JSON array with sender and subject for each email' "
        "or 'The battery percentage as a number'.",
    ),
    locked_app_package: str | None = Field(
        default=None,
        description="Optional package name of the app to lock the device to. "
        "Will launch the app if not already running, and keep it in foreground "
        "until the task is completed. REQUIRED when using apk_path.",
    ),
    apk_path: str | None = Field(
        default=None,
        description="Path to local APK file to deploy to cloud mobile. "
        "Only works when CLOUD_MOBILE_NAME is set. "
        "The APK will be uploaded to cloud storage and installed before task execution. "
        "Requires MINITAP_API_KEY to be configured. ",
    ),
) -> str | dict[str, Any] | ToolResult:
    """Run a manual task on a mobile device via the Minitap platform."""
    try:
        if settings.CLOUD_MOBILE_NAME:
            await check_cloud_mobile_status(settings.CLOUD_MOBILE_NAME)

        if apk_path:
            if not settings.CLOUD_MOBILE_NAME:
                raise ToolError(
                    "apk_path parameter requires CLOUD_MOBILE_NAME to be set. "
                    "APK deployment is only supported in cloud mobile mode."
                )

            # Step 1: Upload APK via Platform storage API
            filename = await upload_apk_to_cloud_mobile(apk_path=apk_path)

            # Step 2: Install APK on cloud mobile
            await install_apk_on_cloud_mobile(filename=filename)

        request = PlatformTaskRequest(
            task=ManualTaskConfig(
                goal=goal,
                output_description=output_description,
            ),
            execution_origin="mcp",
        )
        agent = get_mobile_use_agent()
        if not agent._initialized:
            await agent.init()
        result = await agent.run_task(
            request=request,
            locked_app_package=locked_app_package,
        )

        trajectory_gif_path: Path | None = None
        if settings.TRAJECTORY_GIF_DOWNLOAD_FOLDER:
            trajectory_gif_path = await _download_trajectory_gif_if_available()

        serialized_result = _serialize_result(result)

        # If trajectory was saved, return a ToolResult with multiple content items
        if trajectory_gif_path:
            import json

            result_text = (
                json.dumps(serialized_result, indent=2)
                if isinstance(serialized_result, dict)
                else str(serialized_result)
            )
            return ToolResult(
                content=[
                    TextContent(type="text", text=result_text),
                    TextContent(type="text", text=f"Trajectory saved to {trajectory_gif_path}"),
                ],
            )

        return serialized_result
    except Exception as e:
        raise ToolError(str(e))


async def _download_trajectory_gif_if_available() -> Path | None:
    """Download the trajectory GIF if available and folder is configured.

    Fetches the latest task run ID from the API and downloads the GIF.

    Returns:
        The path to the downloaded GIF file, or None if download failed or not configured.
    """
    download_folder = settings.TRAJECTORY_GIF_DOWNLOAD_FOLDER
    if not download_folder:
        logger.warning("TRAJECTORY_GIF_DOWNLOAD_FOLDER not configured, skipping GIF download")
        return None

    task_run_id = None
    try:
        task_run_id = await get_latest_task_run_id()

        gif_path = await download_trajectory_gif(
            task_run_id=task_run_id,
            download_path=download_folder,
        )
        logger.info(
            "Trajectory GIF downloaded",
            task_run_id=task_run_id,
            path=str(gif_path),
        )
        return gif_path
    except (StorageDownloadError, TaskRunsError) as e:
        logger.warning(
            "Failed to download trajectory GIF",
            task_run_id=task_run_id,
            error=str(e),
        )
        return None
