"""Task runs API utilities.

This module provides functionality to interact with the task runs API
for fetching information about executed tasks.
"""

import httpx

from minitap.mcp.core.config import settings
from minitap.mcp.core.logging_config import get_logger

logger = get_logger(__name__)


class TaskRunsError(Exception):
    """Error raised when task runs API operations fail."""

    pass


def _get_api_key() -> str:
    """Get the API key from settings.

    Returns:
        The API key string

    Raises:
        TaskRunsError: If API key is not configured
    """
    api_key = settings.MINITAP_API_KEY.get_secret_value() if settings.MINITAP_API_KEY else None
    if not api_key:
        raise TaskRunsError("MINITAP_API_KEY is required for task runs API")
    return api_key


async def get_latest_task_run_id() -> str:
    """Get the ID of the most recently finished task run.

    This function calls the MaaS API to get the latest task run,
    sorted by finished_at in descending order.

    Returns:
        The ID of the latest task run

    Raises:
        TaskRunsError: If the request fails or no task run is found
    """
    api_key = _get_api_key()
    base_url = settings.MINITAP_API_BASE_URL
    endpoint = f"{base_url}/task-runs"

    params = {
        "page": 1,
        "pageSize": 1,
        "orphans": "include",
        "virtualMobile": "include",
        "sortBy": "finished_at",
        "sortOrder": "desc",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.debug("Fetching latest task run ID")
            response = await client.get(
                endpoint,
                params=params,
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if response.status_code != 200:
                logger.error(
                    "Failed to get latest task run",
                    status_code=response.status_code,
                    response=response.text,
                )
                raise TaskRunsError(f"Failed to get latest task run: HTTP {response.status_code}")

            data = response.json()
            items = data.get("runs", [])
            if not items:
                raise TaskRunsError("No task runs found")

            task_run_id = items[0].get("id")
            if not task_run_id:
                raise TaskRunsError("Task run ID not found in response")

            logger.debug("Got latest task run ID", task_run_id=task_run_id)
            return task_run_id

        except httpx.TimeoutException as e:
            logger.error("Latest task run request timed out", error=str(e))
            raise TaskRunsError("Request timed out") from e
        except httpx.RequestError as e:
            logger.error("Latest task run request failed", error=str(e))
            raise TaskRunsError(f"Request failed: {str(e)}") from e
        except TaskRunsError:
            raise
        except Exception as e:
            logger.error("Unexpected error getting latest task run", error=str(e))
            raise TaskRunsError(f"Unexpected error: {str(e)}") from e
