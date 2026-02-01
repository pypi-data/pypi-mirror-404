"""Config CLI commands."""

import click

from planer_cli.config.settings import (
    create_config_template,
    get_config_file_path,
    get_settings,
)
from planer_cli.output.formatter import output_success


@click.group()
def config() -> None:
    """Manage configuration."""
    pass


@config.command("init")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing config.")
def init_config(force: bool) -> None:
    """Create a config file template.

    Creates ~/.config/planer-cli/config.yaml with default settings.
    """
    config_path = get_config_file_path()

    if config_path.exists() and not force:
        click.echo(f"Config file already exists: {config_path}")
        click.echo("Use --force to overwrite.")
        return

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write template
    config_path.write_text(create_config_template())
    output_success(f"Created config file: {config_path}")


@config.command("show")
@click.option("--path", "-p", is_flag=True, help="Show only the config file path.")
def show_config(path: bool) -> None:
    """Show current configuration.

    Displays all settings with their current values and sources.
    """
    from rich.console import Console
    from rich.table import Table

    config_path = get_config_file_path()

    if path:
        click.echo(config_path)
        return

    console = Console()
    settings = get_settings()

    # Show config file status
    if config_path.exists():
        console.print(f"[dim]Config file:[/dim] {config_path}")
    else:
        console.print(
            f"[dim]Config file:[/dim] {config_path} [yellow](not found)[/yellow]"
        )

    console.print()

    # Show current settings
    table = Table(title="Current Settings")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # Display relevant settings
    table.add_row("client_id", settings.client_id or "[dim](not set)[/dim]")
    table.add_row("tenant_id", settings.tenant_id)
    table.add_row("output_format", settings.output_format)
    table.add_row("default_plan_id", settings.default_plan_id or "[dim](not set)[/dim]")
    table.add_row("log_level", settings.log_level)
    table.add_row("config_dir", str(settings.config_dir))

    console.print(table)


@config.command("edit")
def edit_config() -> None:
    """Open config file in default editor.

    Uses $EDITOR or falls back to vim/nano.
    """
    import os
    import subprocess

    config_path = get_config_file_path()

    if not config_path.exists():
        click.echo(f"Config file not found: {config_path}")
        click.echo("Run 'planer config init' to create one.")
        return

    editor = os.environ.get("EDITOR", "vim")
    subprocess.run([editor, str(config_path)])
