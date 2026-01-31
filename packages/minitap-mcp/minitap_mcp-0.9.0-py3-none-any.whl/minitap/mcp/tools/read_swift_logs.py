"""Tool for reading Swift/iOS logs for debugging during development."""

import asyncio
import json
import sys
from datetime import datetime

from pydantic import BaseModel, Field

from minitap.mcp.core.decorators import handle_tool_errors
from minitap.mcp.core.logging_config import get_logger
from minitap.mcp.main import mcp

logger = get_logger(__name__)


class BacktraceFrame(BaseModel):
    imageOffset: int | None = None
    imageUUID: str | None = None
    imagePath: str | None = None
    symbol: str | None = None


class Backtrace(BaseModel):
    frames: list[BacktraceFrame] = []


class SimplifiedLog(BaseModel):
    timestamp: str
    level: str
    category: str
    message: str
    process_id: int
    backtrace: Backtrace | None = None
    sender_image_path: str | None = None
    process_image_path: str | None = None
    sender_image_uuid: str | None = None


class LogsOutput(BaseModel):
    bundle_id: str
    last_minutes: int
    log_count: int
    logs: list[SimplifiedLog]
    message: str | None = None


def _convert_to_iso8601(timestamp: str) -> str:
    """Convert macOS log show timestamp to ISO8601 format.

    Input format:  "YYYY-MM-DD HH:MM:SS.NNNNNN±TTTT"
    Output format: "YYYY-MM-DDTHH:MM:SS.NNNNNN±TT:TT"
    """
    if not timestamp:
        return timestamp

    try:
        dt = datetime.fromisoformat(timestamp.replace(" ", "T"))
        return dt.isoformat()
    except ValueError:
        return timestamp


def _parse_backtrace(raw: dict | None) -> Backtrace | None:
    """Parse raw backtrace dict into Backtrace model."""
    if not raw or not isinstance(raw, dict):
        return None
    frames_raw = raw.get("frames", [])
    if not frames_raw:
        return None
    frames = [
        BacktraceFrame(
            imageOffset=f.get("imageOffset"),
            imageUUID=f.get("imageUUID"),
            imagePath=f.get("imagePath"),
            symbol=f.get("symbol"),
        )
        for f in frames_raw
        if isinstance(f, dict)
    ]
    return Backtrace(frames=frames) if frames else None


async def _run_log_show(
    predicate: str | None,
    last_minutes: int,
    include_debug: bool,
    *,
    simulator: bool = False,
) -> tuple[list, str | None]:
    """Run log show command and return parsed logs and optional error message."""
    if simulator:
        cmd = ["xcrun", "simctl", "spawn", "booted", "log", "show"]
    else:
        cmd = ["log", "show"]

    cmd.extend(["--style", "json", "--last", f"{last_minutes}m"])

    if predicate:
        cmd.extend(["--predicate", predicate])

    if include_debug:
        cmd.extend(["--debug", "--info"])

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()
    error_output = stderr.decode("utf-8", errors="replace")

    if process.returncode != 0:
        if simulator and "No devices are booted" in error_output:
            return [], "Error: No iOS Simulator is running. Please boot a simulator first."
        return [], None

    output = stdout.decode("utf-8", errors="replace").strip()
    lines = output.split("\n")
    if lines and lines[0].startswith("Filtering the log data"):
        lines = lines[1:]
    if lines and lines[0].startswith("Skipping info and debug"):
        lines = lines[1:]

    json_output = "\n".join(lines).strip()

    if not json_output or json_output == "[]":
        return [], None

    try:
        return json.loads(json_output), None
    except json.JSONDecodeError:
        return [], None


@mcp.tool(
    name="read_swift_logs",
    description="""
    Read Swift/iOS logs for debugging during app development. Please note that this tool expect the
    bundle identifier of the app to be passed as an argument.
    
    This tool can read logs from:
    1. iOS Simulator runtime logs (source="simulator") - filters by process name
    2. All unified logging sources (source="all") - queries by subsystem and process name
    
    Use cases:
    - Debug runtime issues by reading simulator logs
    - Find crash logs and error messages
    - Read print() statements and os.Logger output from your Swift app
    
    Examples:
    - read_swift_logs(source="simulator", bundle_id="com.example.myapp")
    - read_swift_logs(source="simulator", bundle_id="com.example.myapp", last_minutes=10)
    - read_swift_logs(source="all", bundle_id="com.example.myapp", last_minutes=5)
    """,
)
@handle_tool_errors
async def read_swift_logs(
    bundle_id: str = Field(
        description="The bundle identifier of the iOS app (e.g., 'com.example.myapp'). "
        "This is used to filter logs by subsystem.",
    ),
    source: str = Field(
        default="all",
        description="Log source: 'simulator' for iOS Simulator runtime logs, "
        "'all' to read from all sources that generate runtime logs related with the bundle.",
    ),
    last_minutes: int = Field(
        default=5,
        description="Number of minutes of logs to retrieve. Default is 5 minutes.",
    ),
) -> LogsOutput | str:
    """Read Swift/iOS logs from simulator or file."""
    if sys.platform != "darwin":
        return "Error: This tool only works on macOS with Xcode installed."

    process_name = bundle_id.split(".")[-1]

    if source == "simulator":
        return await _read_simulator_logs(bundle_id, last_minutes, process_name)
    elif source == "all":
        return await _read_file_logs(bundle_id, process_name, last_minutes)
    else:
        return f"Error: Unknown source '{source}'. Use 'simulator' or 'all'."


def _map_to_simplified_logs(log_entries: list[dict]) -> list[SimplifiedLog]:
    return [
        SimplifiedLog(
            timestamp=_convert_to_iso8601(entry.get("timestamp", "")),
            level=entry.get("messageType", ""),
            category=entry.get("category", ""),
            message=entry.get("eventMessage", ""),
            process_id=entry.get("processID", 0),
            backtrace=_parse_backtrace(entry.get("backtrace")),
            sender_image_path=entry.get("senderImagePath"),
            process_image_path=entry.get("processImagePath"),
            sender_image_uuid=entry.get("senderImageUUID"),
        )
        for entry in log_entries
        if entry.get("eventMessage")
    ]


async def _read_simulator_logs(
    bundle_id: str,
    last_minutes: int,
    process_name: str | None,
) -> LogsOutput | str:
    """Read historical logs from the booted iOS Simulator."""
    predicate = f'processImagePath CONTAINS "{process_name}"' if process_name else None

    logger.info(f"Reading simulator logs for last {last_minutes}m")

    log_entries, error = await _run_log_show(
        predicate, last_minutes, include_debug=True, simulator=True
    )

    if error:
        return error

    if not log_entries:
        return LogsOutput(
            bundle_id=bundle_id,
            last_minutes=last_minutes,
            log_count=0,
            logs=[],
            message=f"No logs found for '{process_name}' in the last {last_minutes} min.",
        )

    simplified_logs = _map_to_simplified_logs(log_entries)

    return LogsOutput(
        bundle_id=bundle_id,
        last_minutes=last_minutes,
        log_count=len(simplified_logs),
        logs=simplified_logs,
    )


async def _read_file_logs(bundle_id: str, process_name: str, last_minutes: int) -> LogsOutput:
    # Query 1: Logs by subsystem (os.Logger logs)
    subsystem_predicate = f'subsystem == "{bundle_id}"'

    # Query 2: Logs by process name (catches crashes and system logs)
    # Include fatal errors, crashes, and error-level logs
    process_predicate = (
        f'process == "{process_name}" AND '
        f'(messageType == "Fault" OR messageType == "Error" OR '
        f'eventMessage CONTAINS "fatal" OR eventMessage CONTAINS "crash")'
    )

    logger.info(
        "fetching_ios_logs",
        bundle_id=bundle_id,
        last_minutes=last_minutes,
    )

    # Run both queries in parallel
    (subsystem_logs, _), (process_logs, _) = await asyncio.gather(
        _run_log_show(subsystem_predicate, last_minutes, include_debug=True),
        _run_log_show(process_predicate, last_minutes, include_debug=False),
    )

    # Merge and deduplicate logs by timestamp + message
    all_logs = subsystem_logs + process_logs
    seen = set()
    unique_logs = []
    for log_entry in all_logs:
        key = (log_entry.get("timestamp"), log_entry.get("eventMessage"))
        if key not in seen:
            seen.add(key)
            unique_logs.append(log_entry)

    # Sort by timestamp
    unique_logs.sort(key=lambda x: x.get("timestamp", ""))

    if not unique_logs:
        return LogsOutput(
            bundle_id=bundle_id,
            last_minutes=last_minutes,
            log_count=0,
            logs=[],
            message=f"No logs found for '{bundle_id}' in the last {last_minutes} min.",
        )

    simplified_logs = _map_to_simplified_logs(unique_logs)

    logger.info("logs_retrieved", bundle_id=bundle_id, log_count=len(simplified_logs))

    return LogsOutput(
        bundle_id=bundle_id,
        last_minutes=last_minutes,
        log_count=len(simplified_logs),
        logs=simplified_logs,
    )
