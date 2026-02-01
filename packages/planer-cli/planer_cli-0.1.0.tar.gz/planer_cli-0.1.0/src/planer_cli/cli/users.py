"""Users CLI commands."""

import click

from planer_cli.api.client import GraphClient
from planer_cli.api.users import UsersAPI
from planer_cli.auth.manager import AuthManager
from planer_cli.cli.common import async_command, handle_api_errors
from planer_cli.output.formatter import output_json
from planer_cli.output.tables import print_user_detail, print_users_table


def get_users_api() -> tuple[GraphClient, UsersAPI]:
    """Get client and users API.

    Returns:
        Tuple of (GraphClient, UsersAPI).
    """
    auth = AuthManager()
    client = GraphClient(auth)
    users_api = UsersAPI(client)
    return client, users_api


@click.group()
def users() -> None:
    """Manage users and get user IDs."""
    pass


@users.command("me")
@click.pass_context
@handle_api_errors
@async_command
async def get_me(ctx: click.Context) -> None:
    """Show current user info and ID."""
    client, users_api = get_users_api()

    try:
        user = await users_api.get_me()

        if ctx.obj.get("format") == "json":
            output_json(user)
        else:
            print_user_detail(user)
    finally:
        await client.close()


@users.command("list")
@click.option("--search", "-s", help="Search by name or email.")
@click.pass_context
@handle_api_errors
@async_command
async def list_users(ctx: click.Context, search: str | None) -> None:
    """List users in the organization."""
    client, users_api = get_users_api()

    try:
        user_list = await users_api.list_users(search)

        if not user_list:
            click.echo("No users found.")
            return

        if ctx.obj.get("format") == "json":
            output_json(user_list)
        else:
            print_users_table(user_list)
    finally:
        await client.close()


@users.command("get")
@click.argument("user_id")
@click.pass_context
@handle_api_errors
@async_command
async def get_user(ctx: click.Context, user_id: str) -> None:
    """Get a user by ID or email.

    USER_ID: The user ID or email address.
    """
    client, users_api = get_users_api()

    try:
        user = await users_api.get_user(user_id)

        if ctx.obj.get("format") == "json":
            output_json(user)
        else:
            print_user_detail(user)
    finally:
        await client.close()
