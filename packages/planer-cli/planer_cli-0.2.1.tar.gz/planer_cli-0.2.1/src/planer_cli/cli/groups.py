"""Groups CLI commands."""

import click

from planer_cli.cli.common import async_command, get_client_and_api, handle_api_errors
from planer_cli.output.formatter import output_json
from planer_cli.output.tables import print_groups_table


@click.group()
def groups() -> None:
    """Manage Microsoft 365 groups."""
    pass


@groups.command("list")
@click.pass_context
@handle_api_errors
@async_command
async def list_groups(ctx: click.Context) -> None:
    """List Microsoft 365 groups you are a member of."""
    client, _, groups_api = get_client_and_api()

    try:
        group_list = await groups_api.list_my_groups()

        if not group_list:
            click.echo("No Microsoft 365 groups found.")
            return

        if ctx.obj.get("format") == "json":
            output_json(group_list)
        else:
            print_groups_table(group_list)
    finally:
        await client.close()
