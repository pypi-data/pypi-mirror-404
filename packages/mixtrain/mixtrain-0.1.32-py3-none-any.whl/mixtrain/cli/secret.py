import json

import typer
from rich import print as rprint
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from mixtrain.client import MixClient

from .utils import format_datetime, print_empty_state, print_error

console = Console()
app = typer.Typer(help="Manage workspace secrets.", invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def list(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    """List all secrets in the current workspace."""
    try:
        client = MixClient()
        response = client.get_all_secrets()
        secrets = response.get("data", [])

        if json_output:
            # Don't include secret values in JSON output
            safe_secrets = (
                [{k: v for k, v in s.items() if k != "value"} for s in secrets]
                if secrets
                else []
            )
            rprint(json.dumps(safe_secrets, indent=2))
            return

        if not secrets:
            print_empty_state(
                "secrets in this workspace",
                "Use 'mixtrain secret set <name> <value>' to create one.",
            )
            return

        # Create table
        table = Table()
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Created", style="dim")
        table.add_column("Created By", style="dim")

        for secret in secrets:
            table.add_row(
                secret.get("name", ""),
                secret.get("description", "") or "[dim]No description[/dim]",
                format_datetime(secret.get("created_at", "")),
                secret.get("created_by", ""),
            )

        console.print(table)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def get(
    name: str = typer.Argument(..., help="Name of the secret to retrieve"),
    show_value: bool = typer.Option(
        False, "--show", "-s", help="Display the secret value (use with caution)"
    ),
):
    """Get a specific secret by name."""
    try:
        client = MixClient()
        secret_data = client._request("GET", f"/secrets/{name}").json()

        # Create info table
        table = Table.grid(padding=(0, 2))
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row("Name:", secret_data.get("name", ""))
        table.add_row(
            "Description:",
            secret_data.get("description", "") or "[dim]No description[/dim]",
        )

        table.add_row("Created:", format_datetime(secret_data.get("created_at", "")))
        table.add_row("Updated:", format_datetime(secret_data.get("updated_at", "")))
        table.add_row("Created by:", secret_data.get("created_by", ""))

        if show_value:
            value = secret_data.get("value", "")
            display_value = value
            table.add_row("Value:", f"[yellow]{display_value}[/yellow]")
        else:
            table.add_row("Value:", "[dim]Hidden (use --show to display)[/dim]")

        console.print(table)

    except Exception as e:
        if "404" in str(e):
            print_error(f"Secret '{name}' not found.")
        else:
            print_error(str(e))
        raise typer.Exit(1)


@app.command()
def set(
    name: str = typer.Argument(..., help="Name of the secret"),
    value: str | None = typer.Argument(
        None, help="Value of the secret (will prompt if not provided)"
    ),
    description: str | None = typer.Option(
        None, "--description", "-d", help="Description of the secret"
    ),
    update: bool = typer.Option(
        False, "--update", "-u", help="Update existing secret if it exists"
    ),
):
    """Create or update a secret."""
    try:
        client = MixClient()
        workspace_name = client.workspace_name

        # Get value if not provided
        if value is None:
            rprint(
                f"Creating secret '[cyan]{name}[/cyan]' in workspace '[bold]{workspace_name}[/bold]'"
            )
            value = Prompt.ask("\nEnter secret value", password=True)
            if not value.strip():
                print_error("Secret value cannot be empty.")
                raise typer.Exit(1)

        # Get description if not provided
        if description is None:
            description = Prompt.ask("Enter description (optional)", default="")

        # Check if secret already exists
        existing_secret = None
        try:
            existing_secret = client._request("GET", f"/secrets/{name}").json()
        except Exception:
            pass  # Secret doesn't exist, which is fine for creation

        if existing_secret and not update:
            print_error(
                f"Secret '{name}' already exists.", "Use --update flag to update it."
            )
            raise typer.Exit(1)

        # Create or update secret
        data = {"name": name, "value": value, "description": description}

        if existing_secret:
            # Update existing secret
            update_data = {"value": value, "description": description}
            client._request("PUT", f"/secrets/{name}", json=update_data)
            rprint(f"Secret '{name}' updated.")
        else:
            # Create new secret
            client._request("POST", "/secrets/", json=data)
            rprint(f"Secret '{name}' created.")

    except Exception as e:
        if "already exists" in str(e):
            print_error(
                f"Secret '{name}' already exists.", "Use --update flag to update it."
            )
        else:
            print_error(str(e))
        raise typer.Exit(1)


@app.command()
def delete(
    name: str = typer.Argument(..., help="Name of the secret to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a secret."""
    try:
        client = MixClient()
        workspace_name = client.workspace_name

        # Confirm deletion unless --yes is used
        if not yes:
            confirmed = Confirm.ask(
                f"Delete secret '[bold]{name}[/bold]' from workspace '[bold]{workspace_name}[/bold]'?",
                default=False,
            )
            if not confirmed:
                rprint("Deletion cancelled.")
                return

        client._request("DELETE", f"/secrets/{name}")
        rprint(f"Secret '{name}' deleted.")

    except Exception as e:
        if "404" in str(e):
            print_error(f"Secret '{name}' not found.")
        else:
            print_error(str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
