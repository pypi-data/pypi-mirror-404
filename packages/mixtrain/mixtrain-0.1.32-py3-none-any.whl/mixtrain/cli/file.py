"""Mixtrain File CLI Commands"""

import json
import os

import typer
from rich import print as rprint
from rich.table import Table

from mixtrain import Files

from .utils import format_datetime, print_empty_state, print_error

app = typer.Typer(help="Manage workspace files.", invoke_without_command=True)


def format_size(size_bytes: int | None) -> str:
    """Format bytes to human-readable size."""
    if size_bytes is None:
        return "-"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command(name="upload")
def upload_file(
    local_path: str = typer.Argument(
        ..., help="Local file or directory path to upload"
    ),
    remote_path: str | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Remote path/prefix in storage (defaults to filename or directory name)",
    ),
    content_type: str | None = typer.Option(
        None,
        "--content-type",
        "-t",
        help="MIME type for single file (auto-detected if not provided)",
    ),
    pattern: str = typer.Option(
        "**/*",
        "--pattern",
        help="Glob pattern for directory uploads (e.g., '**/*.json')",
    ),
    max_concurrency: int = typer.Option(
        5,
        "--concurrency",
        "-c",
        help="Max parallel uploads for directories",
    ),
):
    """Upload a file or directory to workspace storage.

    Examples:
        mixtrain file upload model.bin
        mixtrain file upload output.json --path outputs/run_123/output.json
        mixtrain file upload ./my_data/ --path data/
        mixtrain file upload ./my_data/ --path data/ --pattern "**/*.json"
        mixtrain file upload ./my_data/ --concurrency 10
    """
    try:
        if not os.path.exists(local_path):
            print_error(f"Path not found: {local_path}")
            raise typer.Exit(1)

        files = Files()

        # Check if it's a directory
        if os.path.isdir(local_path):
            rprint(f"[dim]Uploading directory {local_path}...[/dim]")

            result = files.upload_dir(
                local_path,
                remote_prefix=remote_path or "",
                pattern=pattern,
                max_concurrency=max_concurrency,
            )

            rprint(f"[green]Uploaded {len(result.successful)} file(s)[/green]")
            if result.failed:
                rprint(f"[red]Failed: {len(result.failed)} file(s)[/red]")
                for err in result.failed:
                    rprint(f"[dim]  - {err.local_path}: {err.error}[/dim]")
                raise typer.Exit(1)
        else:
            # Single file upload
            rprint(f"[dim]Uploading {local_path}...[/dim]")

            info = files.upload(local_path, remote_path, content_type)

            rprint(f"[green]Uploaded:[/green] {info.path}")
            rprint(f"[dim]Size: {format_size(info.size)}[/dim]")

    except typer.Exit:
        raise
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="download")
def download_file(
    remote_path: str = typer.Argument(..., help="Remote file path in storage"),
    local_path: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Local destination path (defaults to filename)",
    ),
):
    """Download a file from workspace storage.

    Examples:
        mixtrain file download outputs/model.bin
        mixtrain file download outputs/results.json --output ./local_results.json
    """
    try:
        files = Files()
        rprint(f"[dim]Downloading {remote_path}...[/dim]")

        downloaded_path = files.download(remote_path, local_path)

        rprint(f"[green]Downloaded:[/green] {downloaded_path}")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="list")
def list_files(
    prefix: str = typer.Argument("", help="Path prefix to filter files"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
    limit: int = typer.Option(
        100,
        "--limit",
        "-n",
        help="Maximum number of files to list",
    ),
):
    """List files in workspace storage.

    Examples:
        mixtrain file list
        mixtrain file list outputs/
        mixtrain file list --json
    """
    try:
        files = Files()
        file_list = files.list(prefix=prefix, limit=limit)

        if json_output:
            output = [
                {
                    "path": f.path,
                    "name": f.name,
                    "size": f.size,
                    "content_type": f.content_type,
                    "last_modified": f.last_modified.isoformat()
                    if f.last_modified
                    else None,
                }
                for f in file_list
            ]
            rprint(json.dumps(output, indent=2))
            return

        if not file_list:
            print_empty_state(
                "files", f"No files found with prefix '{prefix}'" if prefix else None
            )
            return

        table = Table(title=f"Files{f' (prefix: {prefix})' if prefix else ''}")
        table.add_column("Path", style="cyan")
        table.add_column("Size", justify="right")
        table.add_column("Modified")

        for f in file_list:
            modified = (
                format_datetime(f.last_modified.isoformat()) if f.last_modified else "-"
            )
            table.add_row(
                f.path,
                format_size(f.size),
                modified,
            )

        rprint(table)
        rprint(f"[dim]Showing {len(file_list)} file(s)[/dim]")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="get")
def get_file_info(
    remote_path: str = typer.Argument(..., help="Remote file path"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
):
    """Get file metadata and download URL.

    Examples:
        mixtrain file get outputs/model.bin
        mixtrain file get outputs/results.json --json
    """
    try:
        files = Files()
        info = files.get(remote_path)

        if json_output:
            output = {
                "path": info.path,
                "name": info.name,
                "size": info.size,
                "content_type": info.content_type,
                "last_modified": info.last_modified.isoformat()
                if info.last_modified
                else None,
                "download_url": info.download_url,
            }
            rprint(json.dumps(output, indent=2))
            return

        rprint(f"[bold]Path:[/bold] {info.path}")
        rprint(f"[bold]Size:[/bold] {format_size(info.size)}")
        rprint(f"[bold]Type:[/bold] {info.content_type or '-'}")
        if info.last_modified:
            rprint(
                f"[bold]Modified:[/bold] {format_datetime(info.last_modified.isoformat())}"
            )
        if info.download_url:
            rprint(f"[bold]Download URL:[/bold] {info.download_url}")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="delete")
def delete_file(
    remote_path: str = typer.Argument(..., help="Remote file path to delete"),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
):
    """Delete a file from workspace storage.

    Examples:
        mixtrain file delete outputs/old_model.bin
        mixtrain file delete outputs/temp.json --yes
    """
    try:
        if not yes:
            confirm = typer.confirm(f"Delete file '{remote_path}'?")
            if not confirm:
                rprint("[yellow]Deletion cancelled.[/yellow]")
                return

        files = Files()
        success = files.delete(remote_path)

        if success:
            rprint(f"[green]Deleted:[/green] {remote_path}")
        else:
            print_error(f"Failed to delete: {remote_path}")
            raise typer.Exit(1)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="exists")
def check_file_exists(
    remote_path: str = typer.Argument(..., help="Remote file path to check"),
):
    """Check if a file exists in workspace storage.

    Examples:
        mixtrain file exists outputs/model.bin
    """
    try:
        files = Files()
        exists = files.exists(remote_path)

        if exists:
            rprint(f"[green]Exists:[/green] {remote_path}")
        else:
            rprint(f"[yellow]Not found:[/yellow] {remote_path}")
            raise typer.Exit(1)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
