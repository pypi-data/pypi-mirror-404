"""Mixtrain CLI - Command Line Interface for Mixtrain SDK."""

import json
import os
from importlib.metadata import version

import httpx
import typer
from rich import print as rprint
from rich.table import Table

from mixtrain import client as mixtrain_client
from mixtrain.client import MixClient
from mixtrain.utils import auth as auth_utils
from mixtrain.utils.config import get_config

from . import dataset, file, model, provider, router, secret, update, workflow
from .update import check_update_notification
from .utils import print_empty_state, print_error, truncate

__version__ = version("mixtrain")

app = typer.Typer(invoke_without_command=True)


@app.callback()
def cli_main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
):
    if version:
        typer.echo(f"mixtrain {__version__}")
        raise typer.Exit()

    # Check for updates (non-blocking, cached)
    if msg := check_update_notification():
        rprint(f"[dim]{msg}[/dim]")

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def login():
    """Authenticate with mixtrain."""
    try:

        def make_auth_request(method: str, path: str, **kwargs) -> httpx.Response:
            """Make unauthenticated request for auth purposes."""
            base_url = os.getenv(
                "MIXTRAIN_PLATFORM_URL", "https://platform.mixtrain.ai/api/v1"
            )
            url = f"{base_url}{path}"
            with httpx.Client() as client:
                return client.request(method, url, **kwargs)

        auth_utils.authenticate_browser(get_config, make_auth_request)
        rprint("Authenticated successfully.")

        # Show new configuration
        show_config()

    except Exception as e:
        print_error(
            str(e),
            "Your previous authentication and workspace settings remain unchanged.",
        )
        raise typer.Exit(1)


workspace_app = typer.Typer(help="Manage workspaces.", invoke_without_command=True)


@workspace_app.callback()
def workspace_main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@workspace_app.command(name="list")
def list_user_workspaces(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all workspaces you have access to."""
    try:
        client = MixClient()
        data = client.list_workspaces()
        workspaces = data.get("data", [])

        if json_output:
            rprint(json.dumps(workspaces, indent=2))
            return

        if not workspaces:
            print_empty_state(
                "workspaces", "Use 'mixtrain workspace create <name>' to create one."
            )
            return

        # Show workspaces
        table = Table("Name", "Description", "Role", "Members", "Created At")
        for workspace in workspaces:
            table.add_row(
                workspace.get("name", ""),
                truncate(workspace.get("description", "")),
                workspace.get("role", ""),
                str(workspace.get("totalMembers", 0)),
                workspace.get("created_at", ""),
            )
        rprint(table)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@workspace_app.command(name="create")
def create_workspace_cmd(
    name: str,
    description: str = typer.Option(
        "", "--description", "-d", help="Workspace description"
    ),
):
    """Create a new workspace."""
    try:
        client = MixClient()
        result = client.create_workspace(name, description)
        workspace_data = result.get("data", {})
        workspace_name_created = workspace_data.get("name")

        frontend_url = os.getenv("FRONTEND_URL", "https://app.mixtrain.ai")
        workspace_url = f"{frontend_url}/{workspace_name_created}"

        rprint(f"Created workspace '{workspace_name_created}'")
        rprint(f"[link={workspace_url}]{workspace_url}[/link]")

        # Automatically switch to the new workspace
        mixtrain_client.set_workspace(name)
        rprint(f"Switched to workspace: [bold]{name}[/bold]")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@workspace_app.command(name="delete")
def delete_workspace_cmd(
    workspace_name: str,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a workspace. This will delete all datasets and configurations."""
    try:
        # Confirm deletion unless --yes flag is used
        if not yes:
            confirm = typer.confirm(
                f"Delete workspace '{workspace_name}'? This will permanently delete all datasets, providers, and configurations."
            )
            if not confirm:
                rprint("Deletion cancelled.")
                return

        client = MixClient()
        client.delete_workspace(workspace_name)
        rprint(f"Deleted workspace '{workspace_name}'.")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def config(
    workspace: str = typer.Option(
        None, "--workspace", "-w", help="Set the current workspace"
    ),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
):
    """Manage CLI configuration."""
    if workspace:
        try:
            mixtrain_client.set_workspace(workspace)
            rprint(f"Switched to workspace: [bold]{workspace}[/bold]")
            rprint("\nUpdated configuration:")
            show_config()
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)
    else:
        show_config()


def show_config():
    """Show current configuration in a table format"""
    config = mixtrain_client.get_config()

    if not config.workspaces:
        print_empty_state("workspaces configured", "Run 'mixtrain login' first.")
        return

    # Create workspaces table
    table = Table()
    table.add_column("Workspace", style="cyan")
    table.add_column("Status", style="green")

    for workspace in config.workspaces:
        status = "ACTIVE" if workspace.active else ""
        table.add_row(workspace.name, status)

    rprint(table)


app.add_typer(dataset.app, name="dataset")
app.add_typer(model.app, name="model")
app.add_typer(workflow.app, name="workflow")
app.add_typer(file.app, name="file")
app.add_typer(router.app, name="router")
app.add_typer(secret.app, name="secret")
app.add_typer(workspace_app, name="workspace")
app.add_typer(update.app, name="update")
app.add_typer(provider.app, name="provider", hidden=True)
# app.add_typer(train.app, name="train")
# app.add_typer(eval.app, name="eval")


def main():
    app()


if __name__ == "__main__":
    main()
