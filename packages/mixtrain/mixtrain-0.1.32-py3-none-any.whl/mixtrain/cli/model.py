"""Mixtrain Model CLI Commands"""

import json
import os
import subprocess
import tempfile

import typer
from rich import print as rprint
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from mixtrain import MixClient

from .utils import (
    expand_file_args,
    fetch_logs,
    print_empty_state,
    print_error,
    stream_logs,
    truncate,
)

app = typer.Typer(help="Manage models.", invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command(name="list")
def list_models(
    provider: str | None = typer.Option(
        "workspace",
        "--provider",
        "-p",
        help="Filter by provider: 'workspace' (default), 'fal', 'modal', etc.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all models."""
    try:
        response = MixClient().list_models(provider=provider)
        models = response.get("data", [])

        if json_output:
            rprint(json.dumps(models, indent=2))
            return

        if not models:
            print_empty_state("models", "Use 'mixtrain model create' to create one.")
            return

        rprint("[bold]Models:[/bold]")
        table = Table("Name", "Type", "Description", "Created At")
        for model in models:
            model_source = model.get("source", "")
            model_type = "Workspace" if model_source == "native" else "External"
            table.add_row(
                model.get("name", ""),
                model_type,
                truncate(model.get("description", "")),
                model.get("created_at", ""),
            )
        rprint(table)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="create")
def create_model(
    files: list[str] = typer.Argument(
        ..., help="Files, directories, or glob patterns to upload"
    ),
    name: str = typer.Option(
        None, "--name", "-n", help="Model name (defaults to first .py filename)"
    ),
    description: str = typer.Option(
        "", "--description", "-d", help="Model description"
    ),
):
    """Create a model from files.

    Examples:
        mixtrain model create ./model-dir/ --name my-model
        mixtrain model create model.py utils.py --name my-model
        mixtrain model create "*.py" Dockerfile --name my-model
    """
    try:
        expanded_files = expand_file_args(files)

        if not expanded_files:
            print_error("No files found to upload")
            raise typer.Exit(1)

        # Validate all files exist
        for f in expanded_files:
            if not os.path.exists(f):
                print_error(f"File not found: {f}")
                raise typer.Exit(1)

        # Default name to first .py filename without extension if not provided
        if not name:
            py_files = [f for f in expanded_files if f.endswith(".py")]
            if py_files:
                name = os.path.splitext(os.path.basename(py_files[0]))[0]
            else:
                name = os.path.splitext(os.path.basename(expanded_files[0]))[0]

        client = MixClient()
        model_data = client.create_model(
            name=name,
            file_paths=expanded_files,
            description=description,
        )
        model_name_created = model_data.get("name")

        model_url = client.frontend_url(f"/models/{model_name_created}")

        rprint(f"Created model '{model_name_created}'")
        rprint(f"[link={model_url}]{model_url}[/link]")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="run")
def run_model(
    model_name: str = typer.Argument(..., help="Model name"),
    input: str | None = typer.Option(
        None, "--input", "-i", help="JSON input data or path to JSON file"
    ),
    detach: bool = typer.Option(
        False, "--detach", "-d", help="Start run and exit without streaming logs"
    ),
):
    """Run a model.

    By default, streams logs in real-time until the run completes.
    Use --detach to start the run and exit immediately.

    Examples:
        mixtrain model run my-model --input '{"prompt": "Hello world"}'
        mixtrain model run my-model -i input.json --detach
    """
    try:
        # Parse JSON input (from string or file)
        input_data = {}
        if input:
            import os

            if os.path.isfile(input):
                with open(input) as f:
                    input_data = json.load(f)
            else:
                input_data = json.loads(input)

        client = MixClient()
        run_data = client.run_model(model_name, inputs=input_data)

        run_number = run_data.get("run_number")
        run_url = client.frontend_url(f"/models/{model_name}/runs/{run_number}")

        rprint(f"Model run started (run #{run_number}).")
        rprint(f"[link={run_url}]{run_url}[/link]")

        if detach:
            # Display outputs if available (for synchronous runs)
            outputs = run_data.get("outputs")
            if outputs:
                rprint("\nOutputs:")
                rprint(json.dumps(outputs, indent=2))
            return

        # Check if this is a native model (only native models support log streaming)
        model_info = client.get_model(model_name)
        if model_info.get("source") != "native":
            # For non-native models, just show outputs
            outputs = run_data.get("outputs")
            if outputs:
                rprint("\nOutputs:")
                rprint(json.dumps(outputs, indent=2))
            return

        # Stream logs in real-time for native models
        final_status = stream_logs(
            client,
            "model",
            model_name,
            run_number,
        )

        # Show final status and outputs
        status_color = "green" if final_status == "completed" else "red"
        rprint(f"\n[{status_color}]Run {final_status}[/{status_color}]")

        # Get final outputs
        final_run = client.get_model_run(model_name, run_number)
        outputs = final_run.get("outputs")
        if outputs:
            rprint("\nOutputs:")
            rprint(json.dumps(outputs, indent=2))

    except KeyboardInterrupt:
        rprint(
            "\n[yellow]Detached from log stream. Run continues in background.[/yellow]"
        )
        raise typer.Exit(0)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="logs")
def get_logs(
    model_name: str = typer.Argument(..., help="Model name"),
    run_number: int = typer.Argument(..., help="Run number"),
):
    """View logs for a model run."""
    try:
        client = MixClient()
        fetch_logs(client, "model", model_name, run_number)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="edit")
def edit_model(
    ctx: typer.Context,
    model_name: str | None = typer.Argument(None, help="Model name"),
    # File operations
    file_path: str | None = typer.Option(
        None, "--file", "-f", help="Edit file in $EDITOR"
    ),
    view: str | None = typer.Option(None, "--view", "-v", help="View file contents"),
    delete: str | None = typer.Option(
        None, "--delete", "-d", help="Delete file/folder at this path"
    ),
    add: list[str] | None = typer.Option(
        None, "--add", "-a", help="Add local files to model"
    ),
    # Metadata operations
    name: str | None = typer.Option(None, "--name", "-n", help="Rename model"),
    description: str | None = typer.Option(
        None, "--description", "-D", help="Update description"
    ),
    # Common
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """View and modify model files and metadata."""
    # Show help if no model name provided
    if not model_name:
        rprint(ctx.get_help())
        raise typer.Exit(0)

    try:
        client = MixClient()

        # Validate: file operations are mutually exclusive
        file_ops = [file_path, view, delete, add]
        if sum(1 for op in file_ops if op) > 1:
            print_error("Only one of -f, -v, -d, --add can be used at a time")
            raise typer.Exit(1)

        # Validate: -f/-v/-d/--add cannot be combined with metadata operations
        if (file_path or view) and (name or description):
            print_error("-f/--file and -v/--view cannot be combined with -n or -D")
            raise typer.Exit(1)

        # Priority: delete > add > metadata-only > edit (with -f) > list

        if delete:
            # Delete file/folder at path specified by delete arg
            if not yes:
                confirm = typer.confirm(f"Delete '{delete}' from model '{model_name}'?")
                if not confirm:
                    rprint("Deletion cancelled.")
                    return

            client.delete_model_file(model_name, delete)
            rprint(f"Deleted '{delete}' from model '{model_name}'.")
            return

        if add:
            # Determine base directory for relative paths
            # If first arg is a directory, use it; otherwise use parent of first arg
            first_arg = add[0]
            if os.path.isdir(first_arg):
                file_base_dir = os.path.abspath(first_arg)
            else:
                file_base_dir = (
                    os.path.dirname(os.path.abspath(first_arg)) or os.getcwd()
                )

            expanded_files = expand_file_args(add)

            if not expanded_files:
                print_error("No files found to add")
                raise typer.Exit(1)

            # Validate files exist
            for f in expanded_files:
                if not os.path.exists(f):
                    print_error(f"File not found: {f}")
                    raise typer.Exit(1)

            result = client.update_model(
                model_name=model_name,
                file_paths=expanded_files,
                file_base_dir=file_base_dir,
            )

            model_data = result.get("data", {}) if "data" in result else result
            model_name_updated = model_data.get("name")
            model_url = client.frontend_url(f"/models/{model_name_updated}")

            rprint(
                f"Added {len(expanded_files)} file(s) to model '{model_name_updated}'"
            )
            rprint(f"[link={model_url}]{model_url}[/link]")
            return

        if name or description:
            if not file_path:
                # Metadata-only update
                result = client.update_model(
                    model_name=model_name,
                    name=name,
                    description=description,
                )

                model_data = result.get("data", {}) if "data" in result else result
                model_name_updated = model_data.get("name")
                model_url = client.frontend_url(f"/models/{model_name_updated}")

                rprint(f"Updated model '{model_name_updated}'")
                rprint(f"[link={model_url}]{model_url}[/link]")
                return

        # File operations: list or edit
        response = client.list_model_files(model_name)
        files = response.get("data", {}).get("files", [])

        if not files:
            rprint("[yellow]No files found in this model.[/yellow]")
            return

        # Helper to flatten file tree and get all files with metadata
        def get_all_files(file_list):
            result = []
            for f in file_list:
                if f.get("type") == "file":
                    result.append(f)
                elif f.get("type") == "directory" and f.get("children"):
                    result.extend(get_all_files(f.get("children", [])))
            return result

        all_files = get_all_files(files)

        # -v provided: view file contents
        if view:
            file_data = client.get_model_file(model_name, view)
            data = file_data.get("data", {})
            current_code = data.get("content", "")
            message = data.get("message")
            size = data.get("size", 0)

            if not current_code:
                if message:
                    rprint(f"[yellow]{message}[/yellow]")
                else:
                    rprint(f"[yellow]No content found in '{view}'.[/yellow]")
                return

            size_str = f"{size:,} bytes" if size else ""
            rprint(f"[bold]{view}[/bold] {size_str}\n")

            # Detect language from file extension
            ext = os.path.splitext(view)[1].lower()
            lang_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".json": "json",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".toml": "toml",
                ".md": "markdown",
                ".sh": "bash",
                ".bash": "bash",
                ".dockerfile": "dockerfile",
            }
            lexer = lang_map.get(ext, "text")
            if os.path.basename(view).lower() == "dockerfile":
                lexer = "dockerfile"

            console = Console()
            syntax = Syntax(current_code, lexer, theme="monokai", line_numbers=True)
            console.print(syntax)
            return

        # -f provided: edit file in $EDITOR
        if file_path:
            file_data = client.get_model_file(model_name, file_path)
            data = file_data.get("data", {})
            current_code = data.get("content", "")
            message = data.get("message")

            if not current_code:
                if message:
                    rprint(f"[yellow]{message}[/yellow]")
                else:
                    rprint(f"[yellow]No content found in '{file_path}'.[/yellow]")
                return

            # Create temp dir with proper file path structure for upload
            tmp_dir = tempfile.mkdtemp()
            tmp_file_path = os.path.join(tmp_dir, file_path)
            os.makedirs(os.path.dirname(tmp_file_path), exist_ok=True)
            with open(tmp_file_path, "w") as tmp:
                tmp.write(current_code)

            # Open editor (check VISUAL first per Unix convention)
            editor = os.environ.get("VISUAL") or os.environ.get("EDITOR", "vim")
            subprocess.call([editor, tmp_file_path])

            # Read edited code
            with open(tmp_file_path) as f:
                new_code = f.read()

            # Check if code changed
            if new_code == current_code:
                rprint("[yellow]No changes made.[/yellow]")
                # Clean up
                os.unlink(tmp_file_path)
                os.removedirs(os.path.dirname(tmp_file_path) or tmp_dir)
                return

            # Update file via PATCH with multipart form
            client.update_model(model_name, file_paths=[tmp_file_path])
            rprint(f"Updated '{file_path}' for model '{model_name}'.")

            # Clean up temp file
            os.unlink(tmp_file_path)
            try:
                os.removedirs(os.path.dirname(tmp_file_path))
            except OSError:
                pass  # Dir might not be empty or already removed
            return

        # Default: list files
        rprint(f"[bold]Files in model '{model_name}':[/bold]")
        table = Table("Path", "Size")
        for f in all_files:
            path = f.get("path", f.get("name", ""))
            size = f.get("size", 0)
            size_str = f"{size:,} bytes" if size else "-"
            table.add_row(path, size_str)
        rprint(table)

    except FileNotFoundError as e:
        print_error(f"File not found: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="delete")
def delete_model(
    model_name: str = typer.Argument(..., help="Model name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a model."""
    try:
        if not yes:
            confirm = typer.confirm(f"Delete model '{model_name}'?")
            if not confirm:
                rprint("Deletion cancelled.")
                return

        MixClient().delete_model(model_name)
        rprint(f"Deleted model '{model_name}'.")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="cancel")
def cancel_run(
    model_name: str = typer.Argument(..., help="Model name"),
    run_number: int = typer.Argument(..., help="Run number to cancel"),
):
    """Cancel a model run."""
    try:
        run_data = MixClient().cancel_model_run(model_name, run_number)
        rprint(f"Cancelled run #{run_number} for model '{model_name}'.")
        rprint(f"Status: {run_data.get('status')}")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="runs")
def list_runs(
    model_name: str = typer.Argument(..., help="Model name"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum runs to show"),
):
    """List runs for a model."""
    try:
        response = MixClient().list_model_runs(model_name, limit=limit)
        runs = response.get("data", [])
        total = response.get("total", len(runs))
        has_more = response.get("has_more", False)

        if not runs:
            print_empty_state("runs for this model")
            return

        # Show count info: "Showing 50 of 127" or just "Total: 5"
        if has_more:
            header = f"[bold]Model Runs (showing {len(runs)} of {total}, latest first):[/bold]"
        else:
            header = f"[bold]Model Runs ({total} total):[/bold]"
        rprint(header)

        table = Table("Run #", "Status", "Started", "Completed")
        for run in runs:
            table.add_row(
                str(run.get("run_number", "")),
                run.get("status", ""),
                run.get("started_at", "N/A"),
                run.get("completed_at", "N/A"),
            )
        rprint(table)

        if has_more:
            rprint("[dim]Use --limit to see more runs[/dim]")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="get")
def get_model(model_name: str = typer.Argument(..., help="Model name")):
    """Get model details."""
    try:
        model = MixClient().get_model(model_name)

        rprint(f"[bold]Model: {model.get('name')}[/bold]")
        rprint(f"Display Name: {model.get('display_name', model.get('name'))}")
        rprint(f"Description: {model.get('description', 'N/A')}")

        rprint(
            f"Agent Integration: {'Enabled' if model.get('agent_integration') else 'Disabled'}"
        )
        rprint(f"Created: {model.get('created_at', 'N/A')}")
        rprint(f"Updated: {model.get('updated_at', 'N/A')}")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="catalog")
def catalog(
    provider: str | None = typer.Option(
        None, "--provider", "-p", help="Filter by provider name (e.g., 'fal', 'modal')"
    ),
):
    """Browse available external models."""
    try:
        response = MixClient().get_catalog_models(provider=provider)
        models = response.get("data", [])

        if not models:
            print_empty_state(
                "catalog models", "Make sure you have onboarded providers."
            )
            return

        rprint(f"[bold]Available External Models ({len(models)} found):[/bold]")
        table = Table("Name", "Model ID", "Description")
        for model in models:
            table.add_row(
                model.get("name", ""),
                model.get("provider_model_id", ""),
                truncate(model.get("description", "")),
            )
        rprint(table)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
