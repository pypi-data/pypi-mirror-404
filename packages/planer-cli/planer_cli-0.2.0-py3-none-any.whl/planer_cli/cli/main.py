"""Main CLI entry point."""

import click

from planer_cli import __version__
from planer_cli.auth.manager import AuthManager
from planer_cli.cli.buckets import buckets
from planer_cli.cli.common import async_command, get_client_and_api, handle_api_errors
from planer_cli.cli.completions import completions
from planer_cli.cli.config import config
from planer_cli.cli.groups import groups
from planer_cli.cli.plans import plans
from planer_cli.cli.tasks import tasks
from planer_cli.cli.users import users
from planer_cli.cli.watch import watch
from planer_cli.config.settings import get_settings
from planer_cli.output.formatter import output_json, output_success


@click.group()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (default: table).",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging.",
)
@click.version_option(version=__version__, prog_name="planer")
@click.pass_context
def cli(ctx: click.Context, format: str, verbose: bool) -> None:
    """Microsoft Planner CLI - Manage plans, tasks, and buckets.

    Authenticate first with 'planer login', then use the various commands
    to interact with your Microsoft Planner data.

    Examples:

        planer login

        planer groups list

        planer plans list <group-id>

        planer tasks create <plan-id> "My task"
    """
    ctx.ensure_object(dict)
    ctx.obj["format"] = format
    ctx.obj["verbose"] = verbose

    if verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)


@cli.command()
@handle_api_errors
def login() -> None:
    """Authenticate with Microsoft Graph using device code flow.

    Opens a browser to complete the authentication flow. Your credentials
    are cached locally for future use.
    """
    auth = AuthManager()
    auth.authenticate()


@cli.command()
@handle_api_errors
def logout() -> None:
    """Clear cached authentication tokens.

    Removes the locally cached tokens. You will need to run 'login' again
    to use the CLI.
    """
    auth = AuthManager()
    auth.logout()


@cli.command()
@handle_api_errors
def status() -> None:
    """Check authentication status."""
    from rich.console import Console

    console = Console()
    auth = AuthManager()

    if auth.is_authenticated():
        console.print("[green]Authenticated[/green]")
    else:
        console.print("[yellow]Not authenticated[/yellow]")
        console.print("Run [cyan]planer login[/cyan] to authenticate.")


@cli.command()
@click.argument("text")
@click.option("--plan-id", "-p", help="Plan ID (overrides PLANER_DEFAULT_PLAN_ID).")
@click.option("--bucket-id", "-b", help="Bucket ID to add task to.")
@click.pass_context
@handle_api_errors
@async_command
async def quick(
    ctx: click.Context,
    text: str,
    plan_id: str | None,
    bucket_id: str | None,
) -> None:
    """Quick-add a task with natural language date parsing.

    TEXT: Task title with optional date (e.g., "Fix bug tomorrow").

    Examples:

        planer quick "Fix bug tomorrow"

        planer quick "Review PR next Monday"

        planer quick "Deploy to prod on Friday" --plan-id <plan-id>
    """
    import dateparser

    settings = get_settings()

    # Determine plan ID
    effective_plan_id = plan_id or settings.default_plan_id
    if not effective_plan_id:
        click.echo(
            "Error: No plan ID specified. Use --plan-id or set "
            "PLANER_DEFAULT_PLAN_ID environment variable."
        )
        return

    # Parse date from text
    parsed_date = dateparser.parse(
        text,
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": None,
        },
    )

    # Extract title (remove date phrases)
    title = text
    due_date = None

    if parsed_date:
        due_date = parsed_date.strftime("%Y-%m-%dT00:00:00Z")
        # Common date phrases to remove from title
        date_phrases = [
            "tomorrow", "today", "next monday", "next tuesday",
            "next wednesday", "next thursday", "next friday",
            "next saturday", "next sunday", "on monday", "on tuesday",
            "on wednesday", "on thursday", "on friday", "on saturday",
            "on sunday", "next week", "this week",
        ]
        title_lower = title.lower()
        for phrase in date_phrases:
            if phrase in title_lower:
                # Remove phrase and clean up
                idx = title_lower.find(phrase)
                title = (title[:idx] + title[idx + len(phrase):]).strip()
                title_lower = title.lower()

    client, planner_api, _ = get_client_and_api()

    try:
        task = await planner_api.create_task(
            plan_id=effective_plan_id,
            title=title,
            bucket_id=bucket_id,
            due_date=due_date,
        )

        if ctx.obj.get("format") == "json":
            output_json(task)
        else:
            due_info = ""
            if parsed_date:
                due_info = f" (due: {parsed_date.strftime('%Y-%m-%d')})"
            output_success(f"Created task: {task.title}{due_info}")
    finally:
        await client.close()


# Register command groups
cli.add_command(completions)
cli.add_command(config)
cli.add_command(groups)
cli.add_command(plans)
cli.add_command(buckets)
cli.add_command(tasks)
cli.add_command(users)
cli.add_command(watch)


if __name__ == "__main__":
    cli()
