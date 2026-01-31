"""Shared CLI utilities for consistent output formatting."""

import glob as glob_module
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich import print as rprint
from rich.console import Console
from rich.status import Status

MAX_UPLOAD_FILES = 100

if TYPE_CHECKING:
    from mixtrain import MixClient

# Shared console for status updates
_console = Console()


def expand_file_args(args: list[str]) -> list[str]:
    """Expand directories and glob patterns to file paths.

    Args:
        args: List of file paths, directories, or glob patterns

    Returns:
        Deduplicated list of file paths

    Raises:
        ValueError: If expanded files exceed MAX_UPLOAD_FILES limit
    """
    files = []
    for arg in args:
        path = Path(arg)
        if path.is_dir():
            # Recursively include all files in directory
            files.extend(str(f) for f in path.rglob("*") if f.is_file())
        elif any(c in arg for c in "*?["):
            # Glob pattern
            files.extend(glob_module.glob(arg, recursive=True))
        else:
            files.append(arg)

    # Dedupe preserving order
    files = list(dict.fromkeys(files))

    if len(files) > MAX_UPLOAD_FILES:
        raise ValueError(
            f"Too many files ({len(files)}). Maximum is {MAX_UPLOAD_FILES}. "
            "Use more specific patterns or split into multiple uploads."
        )

    return files


def print_error(message: str, suggestion: str | None = None):
    """Print consistent error message."""
    rprint(f"[red]Error:[/red] {message}")
    if suggestion:
        rprint(f"[dim]Tip: {suggestion}[/dim]")


def print_empty_state(resource_type: str, suggestion: str | None = None):
    """Print consistent empty state message."""
    rprint(f"[yellow]No {resource_type} found.[/yellow]")
    if suggestion:
        rprint(f"[dim]{suggestion}[/dim]")


def truncate(text: str | None, max_len: int = 50) -> str:
    """Truncate text for table display."""
    if not text:
        return ""
    return text[:max_len] + "..." if len(text) > max_len else text


def format_datetime(iso_string: str | None) -> str:
    """Format ISO datetime string to local time."""
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return iso_string


def stream_logs(
    client: "MixClient",
    resource_type: str,
    resource_name: str,
    run_number: int,
) -> str:
    """Stream logs from a workflow or model run via SSE.

    Shows a spinner status that gets replaced when logs start streaming.

    Args:
        client: MixClient instance for authentication
        resource_type: Either "workflow" or "model"
        resource_name: Name of the workflow or model
        run_number: Run number

    Returns:
        Final status of the run (completed, failed, cancelled, etc.)
    """
    if resource_type == "workflow":
        get_run_fn = lambda: client.get_workflow_run(resource_name, run_number)
    else:
        get_run_fn = lambda: client.get_model_run(resource_name, run_number)

    # Use Status context manager for spinner that gets replaced
    with Status(
        "[dim]Waiting for run to start...[/dim]", console=_console, spinner="dots"
    ) as status:
        # Wait for run to start (sandbox_id or running status)
        max_wait = 600  # 10 minutes - allows for longer provisioning times
        waited = 0
        run_ready = False

        while waited < max_wait:
            try:
                run_data = get_run_fn()
            except Exception:
                time.sleep(2)
                waited += 2
                continue

            run = run_data.get("data", run_data)
            run_status = run.get("status")
            metadata = run.get("run_metadata") or {}
            sandbox_id = metadata.get("sandbox_id")

            # If run already completed, fetch static logs and return
            if run_status in ("completed", "failed", "cancelled"):
                status.stop()
                _print_static_logs(client, resource_type, resource_name, run_number)
                return run_status

            # Check if sandbox_id is available (run has started executing)
            if sandbox_id:
                run_ready = True
                break

            # If running but no sandbox_id, try streaming anyway
            if run_status == "running":
                run_ready = True
                break

            time.sleep(2)
            waited += 2

        if not run_ready and waited >= max_wait:
            status.stop()
            rprint("[yellow]Timed out waiting for run to start[/yellow]")
            run_data = get_run_fn()
            run = run_data.get("data", run_data)
            return run.get("status", "unknown")

        # Update status before streaming
        status.update("[dim]Streaming logs...[/dim]")

        # Stream logs via client method
        log_count = 0
        stream_error = None
        first_log = True

        try:
            for data in client.stream_run_logs(
                resource_type, resource_name, run_number
            ):
                # Stop status spinner on first log output
                if first_log:
                    status.stop()
                    first_log = False

                # Check for error response
                if data.get("_error"):
                    stream_error = f"HTTP {data['status_code']}: {data['body']}"
                    break

                # Handle batched logs format: {"logs": [{"data": "...", ...}, ...]}
                if "logs" in data:
                    for log_entry in data["logs"]:
                        log_text = log_entry.get("data", "")
                        if log_text:
                            log_count += 1
                            print(log_text, end="", flush=True)
                # Fallback for single log format
                elif "data" in data:
                    log_text = data.get("data", "")
                    if log_text:
                        log_count += 1
                        print(log_text, end="", flush=True)

            # Ensure status is stopped
            if first_log:
                status.stop()

            if log_count == 0 and not stream_error:
                _print_static_logs(client, resource_type, resource_name, run_number)

        except KeyboardInterrupt:
            status.stop()
            run_data = get_run_fn()
            run = run_data.get("data", run_data)
            return run.get("status", "unknown")
        except Exception:
            status.stop()
            _print_static_logs(client, resource_type, resource_name, run_number)

    # Get final run status
    run_data = get_run_fn()
    run = run_data.get("data", run_data)
    return run.get("status", "unknown")


def _print_static_logs(
    client: "MixClient",
    resource_type: str,
    resource_name: str,
    run_number: int,
) -> None:
    """Fetch and print static logs using client methods."""
    try:
        if resource_type == "workflow":
            logs = client.get_workflow_run_logs(resource_name, run_number)
        else:
            logs = client.get_model_run_logs(resource_name, run_number)
        if logs:
            print(logs, flush=True)
    except Exception as e:
        rprint(f"[yellow]Error fetching logs: {e}[/yellow]")


def fetch_logs(
    client: "MixClient",
    resource_type: str,
    resource_name: str,
    run_number: int,
) -> None:
    """Fetch and print logs for a workflow or model run.

    Tries streaming first for active runs, falls back to static logs.
    """
    if resource_type == "workflow":
        get_run_fn = lambda: client.get_workflow_run(resource_name, run_number)
    else:
        get_run_fn = lambda: client.get_model_run(resource_name, run_number)

    # Check run status
    run_data = get_run_fn()
    run = run_data.get("data", run_data)
    status = run.get("status")

    # For completed runs, fetch static logs
    if status in ("completed", "failed", "cancelled"):
        _print_static_logs(client, resource_type, resource_name, run_number)
        return

    # For active runs, try streaming
    stream_logs(client, resource_type, resource_name, run_number)


def _poll_for_completion(
    get_run_fn, poll_interval: int = 5, max_polls: int = 360
) -> str:
    """Poll for run completion when streaming is not available.

    Args:
        get_run_fn: Function to get current run status
        poll_interval: Seconds between polls (default: 5)
        max_polls: Maximum number of polls before giving up (default: 360 = 30 min)
    """
    polls = 0
    try:
        while polls < max_polls:
            run_data = get_run_fn()
            run = run_data.get("data", run_data)
            status = run.get("status")

            if status in ("completed", "failed", "cancelled"):
                return status

            polls += 1
            time.sleep(poll_interval)

        return "unknown"
    except KeyboardInterrupt:
        run_data = get_run_fn()
        run = run_data.get("data", run_data)
        return run.get("status", "unknown")
