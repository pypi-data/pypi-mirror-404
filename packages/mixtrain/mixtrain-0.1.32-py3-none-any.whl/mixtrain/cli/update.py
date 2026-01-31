"""Update command for mixtrain CLI - Self-updating functionality."""

import json
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path

import httpx
import typer
from packaging.version import parse as parse_version
from rich.console import Console

PACKAGE_NAME = "mixtrain"
PYPI_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
CACHE_DIR = Path.home() / ".mixtrain"
CACHE_FILE = CACHE_DIR / "update_check.json"
CACHE_TTL = 86400  # 24 hours


def get_current_version() -> str:
    """Get the currently installed version of mixtrain."""
    return version(PACKAGE_NAME)


def get_pypi_version() -> str | None:
    """Fetch latest version from PyPI."""
    try:
        r = httpx.get(PYPI_URL, timeout=5)
        r.raise_for_status()
        return r.json()["info"]["version"]
    except Exception:
        return None


def detect_install_method() -> str:
    """Detect how mixtrain was installed based on sys.executable path."""
    exe = sys.executable.lower()

    # pipx: ~/.local/pipx/venvs/mixtrain/...
    if "pipx" in exe and "venvs" in exe:
        return "pipx"

    # uv tool: ~/.local/share/uv/tools/mixtrain/...
    if "uv" in exe and "tools" in exe:
        return "uv_tool"

    # Check if uv is available (prefer it for venvs)
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return "uv"
    except Exception:
        return "pip"


def run_upgrade(method: str, console: Console) -> bool:
    """Run the appropriate upgrade command."""
    commands = {
        "pipx": ["pipx", "upgrade", PACKAGE_NAME],
        "uv_tool": ["uv", "tool", "upgrade", PACKAGE_NAME],
        "uv": ["uv", "pip", "install", "--upgrade", PACKAGE_NAME],
        "pip": [sys.executable, "-m", "pip", "install", "--upgrade", PACKAGE_NAME],
    }

    cmd = commands.get(method, commands["pip"])
    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")

    result = subprocess.run(cmd)
    return result.returncode == 0


def _spawn_update_checker() -> None:
    """Spawn a detached subprocess to refresh the update cache.

    Uses a separate process so the main CLI can exit immediately without
    waiting for the network request to complete.
    """
    subprocess.Popen(
        [sys.executable, "-m", "mixtrain.cli.update", "--refresh-cache"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # Detach from parent process group
    )


def _do_refresh_cache() -> None:
    """Actually fetch from PyPI and write cache. Called by subprocess."""
    try:
        latest = get_pypi_version()
        if latest:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            CACHE_FILE.write_text(
                json.dumps({"last_check": time.time(), "latest_version": latest})
            )
    except Exception:
        pass  # Silently fail - this is best-effort background refresh


def check_update_notification() -> str | None:
    """Check for updates (non-blocking). Returns message if update available.

    Uses cached data for immediate response. If cache is stale or missing,
    spawns a background process to refresh it for the next CLI invocation.
    """
    try:
        cache = None
        cache_fresh = False

        # Read cache if it exists
        if CACHE_FILE.exists():
            try:
                cache = json.loads(CACHE_FILE.read_text())
                cache_fresh = time.time() - cache.get("last_check", 0) < CACHE_TTL
            except Exception:
                cache = None

        # If cache is stale or missing, spawn background process to refresh
        if not cache_fresh:
            _spawn_update_checker()

        # Return notification based on cached data (if available)
        if cache:
            latest = cache.get("latest_version")
            if latest:
                current = get_current_version()
                if parse_version(latest) > parse_version(current):
                    return (
                        f"Update available: {current} → {latest}. Run 'mixtrain update'"
                    )
        return None
    except Exception:
        return None


app = typer.Typer(help="Check for and install updates.")


@app.callback(invoke_without_command=True)
def update(
    ctx: typer.Context,
    check: bool = typer.Option(False, "--check", help="Only check, don't install"),
    force: bool = typer.Option(False, "--force", help="Force reinstall"),
):
    """Check for and install updates."""
    # If a subcommand was invoked, don't run the default behavior
    if ctx.invoked_subcommand is not None:
        return

    console = Console()

    current = get_current_version()
    console.print(f"Current version: {current}")

    latest = get_pypi_version()
    if not latest:
        console.print("[red]Could not fetch latest version from PyPI[/red]")
        raise typer.Exit(1)

    console.print(f"Latest version:  {latest}")

    needs_update = parse_version(latest) > parse_version(current)

    if not needs_update and not force:
        console.print("[green]✓ Already up to date[/green]")
        return

    if check:
        if needs_update:
            console.print(
                "\n[yellow]Update available![/yellow] Run 'mixtrain update' to upgrade."
            )
        return

    method = detect_install_method()
    console.print(f"Install method:  {method}")

    if run_upgrade(method, console):
        console.print(f"[green]✓ Updated to {latest}[/green]")
    else:
        console.print("[red]Update failed[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    # Entry point for background cache refresh subprocess
    if len(sys.argv) == 2 and sys.argv[1] == "--refresh-cache":
        _do_refresh_cache()
    else:
        app()
