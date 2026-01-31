"""Remote MCP proxy for bridging with the MaaS API MCP server.

This module provides functionality to create a proxy to the remote MaaS API
MCP server, enabling the local MCP to expose remote tools (Figma, Jira, etc.)
through a unified interface.
"""

import asyncio
from urllib.parse import urlparse

from fastmcp import FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.server.proxy import ProxyClient

from minitap.mcp.core.logging_config import get_logger

logger = get_logger(__name__)


def create_remote_mcp_proxy(
    mcp_url: str,
    api_key: str,
    prefix: str = "",
) -> FastMCP:
    """Create a proxy to the remote MaaS API MCP server.

    This function creates a FastMCP proxy that connects to the remote MaaS API
    MCP server using StreamableHTTP transport with Bearer authentication.

    Args:
        mcp_url: The URL of the remote MCP server (e.g., "http://127.0.0.1:8000/mcp").
        api_key: The Minitap API key for authentication.
        prefix: The prefix for remote tools (default: empty string, no prefix).

    Returns:
        A FastMCP proxy server configured to forward requests to the remote MCP.

    Example:
        >>> proxy = create_remote_mcp_proxy(
        ...     mcp_url="http://127.0.0.1:8000/mcp",
        ...     api_key="your-api-key"
        ... )
        >>> main_mcp.mount(proxy, prefix="remote")
    """
    logger.info(f"Creating remote MCP proxy for: {mcp_url}")

    transport = StreamableHttpTransport(
        url=mcp_url,
        headers={
            "Authorization": f"Bearer {api_key}",
        },
    )

    proxy = FastMCP.as_proxy(
        ProxyClient(transport),
        name=f"remote-mcp-proxy-{prefix}",
    )

    logger.info(f"Remote MCP proxy created successfully with prefix: {prefix}")
    return proxy


async def check_remote_mcp_availability(mcp_url: str, api_key: str) -> bool:
    """Check if the remote MCP server is available by testing TCP connection.

    Args:
        mcp_url: The URL of the remote MCP server (e.g., http://localhost:8000/mcp).
        api_key: The Minitap API key for authentication (unused, kept for API compat).

    Returns:
        True if the remote MCP is available, False otherwise.
    """

    parsed = urlparse(mcp_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    try:
        # Simple TCP connection check
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=5.0,
        )
        writer.close()
        await writer.wait_closed()
        logger.info(f"Remote MCP availability check: connected to {host}:{port}")
        return True
    except TimeoutError:
        logger.warning(f"Remote MCP availability check timed out: {mcp_url}")
        return False
    except OSError as e:
        logger.warning(f"Remote MCP connection failed: {mcp_url} - {e}")
        return False
    except Exception as e:
        logger.warning(f"Remote MCP availability check failed: {e}")
        return False
