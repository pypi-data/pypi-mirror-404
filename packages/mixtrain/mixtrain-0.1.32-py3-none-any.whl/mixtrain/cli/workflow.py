"""Mixtrain Workflow CLI Commands"""

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

app = typer.Typer(help="Manage workflows.", invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command(name="list")
def list_workflows(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all workflows."""
    try:
        response = MixClient().list_workflows()
        workflows = response.get("data", [])

        if json_output:
            rprint(json.dumps(workflows, indent=2))
            return

        if not workflows:
            print_empty_state(
                "workflows", "Use 'mixtrain workflow create' to create one."
            )
            return

        # Show workflows
        rprint("[bold]Workflows:[/bold]")
        table = Table("Name", "Description", "Created At")
        for workflow in workflows:
            table.add_row(
                workflow.get("name", ""),
                truncate(workflow.get("description", "")),
                workflow.get("created_at", ""),
            )
        rprint(table)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="create")
def create_workflow(
    files: list[str] = typer.Argument(..., help="Files, directories, or glob patterns"),
    name: str = typer.Option(
        None, "--name", "-n", help="Workflow name (defaults to first .py filename)"
    ),
    description: str = typer.Option(
        "", "--description", "-d", help="Workflow description"
    ),
):
    """Create a workflow from files.

    Examples:
        mixtrain workflow create ./workflow-dir/
        mixtrain workflow create main.py utils.py config.json
        mixtrain workflow create "*.py" Dockerfile --name my-workflow
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

        # Create workflow with files
        client = MixClient()
        workflow_data = client.create_workflow(
            name=name,
            description=description,
            file_paths=expanded_files,
        )
        workflow_name_created = workflow_data.get("name")

        workflow_url = client.frontend_url(f"/workflows/{workflow_name_created}")

        rprint(f"Created workflow '{workflow_name_created}'")
        rprint(f"[link={workflow_url}]{workflow_url}[/link]")

    except FileNotFoundError as e:
        print_error(f"File not found: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="run")
def run_workflow(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    input: str | None = typer.Option(
        None, "--input", "-i", help="JSON input data or path to JSON file"
    ),
    detach: bool = typer.Option(
        False, "--detach", "-d", help="Start run and exit without streaming logs"
    ),
):
    """Run a workflow.

    By default, streams logs in real-time until the run completes.
    Use --detach to start the run and exit immediately.
    """
    try:
        input_data = {}
        if input:
            import json
            import os

            # Check if input is a file path
            if os.path.exists(input):
                try:
                    with open(input) as f:
                        input_data = json.load(f)
                except json.JSONDecodeError:
                    print_error(f"Invalid JSON in input file: {input}")
                    raise typer.Exit(1)
                except Exception as e:
                    print_error(f"Could not read input file: {str(e)}")
                    raise typer.Exit(1)
            else:
                # Try to parse as JSON string
                try:
                    input_data = json.loads(input)
                except json.JSONDecodeError:
                    print_error(
                        "Input must be a valid JSON string or an existing file path."
                    )
                    raise typer.Exit(1)

        client = MixClient()
        run_data = client.start_workflow_run(workflow_name, json_config=input_data)
        run_number = run_data.get("run_number")

        run_url = client.frontend_url(f"/workflows/{workflow_name}/runs/{run_number}")

        rprint(f"Started workflow run #{run_number}")
        rprint(f"[link={run_url}]{run_url}[/link]")

        if detach:
            return

        final_status = stream_logs(
            client,
            "workflow",
            workflow_name,
            run_number,
        )

        # Show final status
        status_color = "green" if final_status == "completed" else "red"
        rprint(f"\n[{status_color}]Run {final_status}[/{status_color}]")

    except KeyboardInterrupt:
        rprint(
            "\n[yellow]Detached from log stream. Run continues in background.[/yellow]"
        )
        raise typer.Exit(0)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="logs")
def get_logs(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    run_number: int = typer.Argument(..., help="Run number"),
):
    """View logs for a workflow run."""
    try:
        client = MixClient()
        fetch_logs(client, "workflow", workflow_name, run_number)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="edit")
def edit_workflow(
    ctx: typer.Context,
    workflow_name: str | None = typer.Argument(None, help="Workflow name"),
    # File operations
    file_path: str | None = typer.Option(
        None, "--file", "-f", help="Edit file in $EDITOR"
    ),
    view: str | None = typer.Option(None, "--view", "-v", help="View file contents"),
    delete: str | None = typer.Option(
        None, "--delete", "-d", help="Delete file/folder at this path"
    ),
    add: list[str] | None = typer.Option(
        None, "--add", "-a", help="Add local files to workflow"
    ),
    # Metadata operations
    name: str | None = typer.Option(None, "--name", "-n", help="Rename workflow"),
    description: str | None = typer.Option(
        None, "--description", "-D", help="Update description"
    ),
    # Common
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """View and modify workflow files and metadata."""
    # Show help if no workflow name provided
    if not workflow_name:
        rprint(ctx.get_help())
        raise typer.Exit(0)

    try:
        client = MixClient()

        # Validate: file operations are mutually exclusive
        file_ops = [file_path, view, delete, add]
        if sum(1 for op in file_ops if op) > 1:
            print_error("Only one of -f, -v, -d, --add can be used at a time")
            raise typer.Exit(1)

        # Validate: -f/-v cannot be combined with metadata operations
        if (file_path or view) and (name or description):
            print_error("-f/--file and -v/--view cannot be combined with -n or -D")
            raise typer.Exit(1)

        # Priority: delete > add > metadata-only > edit (with -f) > list

        if delete:
            # Delete file/folder at path specified by delete arg
            if not yes:
                confirm = typer.confirm(
                    f"Delete '{delete}' from workflow '{workflow_name}'?"
                )
                if not confirm:
                    rprint("Deletion cancelled.")
                    return

            client.delete_workflow_file(workflow_name, delete)
            rprint(f"Deleted '{delete}' from workflow '{workflow_name}'.")
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

            workflow_data = client.update_workflow(
                workflow_name=workflow_name,
                file_paths=expanded_files,
                file_base_dir=file_base_dir,
            )

            workflow_name_updated = workflow_data.get("name")
            workflow_url = client.frontend_url(f"/workflows/{workflow_name_updated}")

            rprint(
                f"Added {len(expanded_files)} file(s) to workflow '{workflow_name_updated}'"
            )
            rprint(f"[link={workflow_url}]{workflow_url}[/link]")
            return

        if name or description:
            if not file_path:
                # Metadata-only update
                workflow_data = client.update_workflow(
                    workflow_name=workflow_name,
                    name=name,
                    description=description,
                )

                workflow_name_updated = workflow_data.get("name")
                workflow_url = client.frontend_url(
                    f"/workflows/{workflow_name_updated}"
                )

                rprint(f"Updated workflow '{workflow_name_updated}'")
                rprint(f"[link={workflow_url}]{workflow_url}[/link]")
                return

        # File operations: list or edit
        result = client.list_workflow_files(workflow_name)
        data = result.get("data", {})
        files = data.get("files", [])

        if not files:
            rprint("[yellow]No files found in this workflow.[/yellow]")
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
            file_data = client.get_workflow_file(workflow_name, view)
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
            file_data = client.get_workflow_file(workflow_name, file_path)
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
                try:
                    os.removedirs(os.path.dirname(tmp_file_path))
                except OSError:
                    pass
                return

            # Update file via PATCH with multipart form
            client.update_workflow(workflow_name, file_paths=[tmp_file_path])
            rprint(f"Updated '{file_path}' for workflow '{workflow_name}'.")

            # Clean up temp file
            os.unlink(tmp_file_path)
            try:
                os.removedirs(os.path.dirname(tmp_file_path))
            except OSError:
                pass  # Dir might not be empty or already removed
            return

        # Default: list files
        rprint(f"[bold]Files in workflow '{workflow_name}':[/bold]")
        table = Table("Path", "Size")
        for f in all_files:
            path = f.get("path", f.get("name", ""))
            size = f.get("size", 0)
            size_str = f"{size} B" if size < 1024 else f"{size / 1024:.1f} KB"
            table.add_row(path, size_str)
        rprint(table)

    except FileNotFoundError as e:
        print_error(f"File not found: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="delete")
def delete_workflow(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a workflow."""
    try:
        if not yes:
            confirm = typer.confirm(
                f"Delete workflow '{workflow_name}'? This will permanently delete all workflow runs."
            )
            if not confirm:
                rprint("Deletion cancelled.")
                return

        MixClient().delete_workflow(workflow_name)
        rprint(f"Deleted workflow '{workflow_name}'.")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="cancel")
def cancel_run(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    run_number: int = typer.Argument(..., help="Run number"),
):
    """Cancel a workflow run."""
    try:
        run_data = MixClient().cancel_workflow_run(workflow_name, run_number)
        rprint(f"Cancelled run #{run_number} (status: {run_data.get('status')}).")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="runs")
def list_runs(
    workflow_name: str = typer.Argument(..., help="Workflow name"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum runs to show"),
):
    """List runs for a workflow."""
    try:
        response = MixClient().list_workflow_runs(workflow_name, limit=limit)
        runs = response.get("data", [])
        total = response.get("total", len(runs))
        has_more = response.get("has_more", False)

        if not runs:
            print_empty_state("runs for this workflow")
            return

        # Show count info: "Showing 50 of 127" or just "Total: 5"
        if has_more:
            header = f"[bold]Workflow Runs (showing {len(runs)} of {total}, latest first):[/bold]"
        else:
            header = f"[bold]Workflow Runs ({total} total):[/bold]"
        rprint(header)

        table = Table("Run #", "Status", "Started", "Completed", "Triggered By")
        for run in runs:
            # Display user name, email, or ID as fallback
            triggered_by = (
                run.get("triggered_by_name")
                or run.get("triggered_by_email")
                or "Unknown"
            )
            table.add_row(
                str(run.get("run_number", "")),
                run.get("status", ""),
                run.get("started_at", "N/A"),
                run.get("completed_at", "N/A"),
                triggered_by,
            )
        rprint(table)

        if has_more:
            rprint("[dim]Use --limit to see more runs[/dim]")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="get")
def get_workflow(workflow_name: str = typer.Argument(..., help="Workflow name")):
    """Get workflow details."""
    try:
        workflow = MixClient().get_workflow(workflow_name)

        rprint(f"[bold]Workflow: {workflow.get('name')}[/bold]")
        rprint(f"Description: {workflow.get('description')}")
        rprint(f"Created: {workflow.get('created_at')}")
        rprint(f"Updated: {workflow.get('updated_at')}")

        # Show runs
        runs = workflow.get("runs", [])
        if runs:
            rprint(f"\n[bold]Recent Runs ({len(runs)}):[/bold]")
            table = Table("Run #", "Status", "Started", "Triggered By")
            for run in runs[:10]:  # Show last 10 runs
                # Display user name, email, or ID as fallback
                triggered_by = (
                    run.get("triggered_by_name")
                    or run.get("triggered_by_email")
                    or "Unknown"
                )
                table.add_row(
                    str(run.get("run_number", "")),
                    run.get("status", ""),
                    run.get("started_at", "N/A"),
                    triggered_by,
                )
            rprint(table)
        else:
            print_empty_state("runs")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
