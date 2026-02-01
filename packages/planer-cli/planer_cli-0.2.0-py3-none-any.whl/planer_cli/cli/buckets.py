"""Buckets CLI commands."""

import click

from planer_cli.cli.common import async_command, get_client_and_api, handle_api_errors
from planer_cli.output.formatter import output_json, output_success
from planer_cli.output.tables import print_bucket_detail, print_buckets_table


@click.group()
def buckets() -> None:
    """Manage Planner buckets."""
    pass


@buckets.command("list")
@click.argument("plan_id")
@click.pass_context
@handle_api_errors
@async_command
async def list_buckets(ctx: click.Context, plan_id: str) -> None:
    """List buckets in a plan.

    PLAN_ID: The plan ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        bucket_list = await planner_api.list_buckets(plan_id)

        if not bucket_list:
            click.echo("No buckets found in this plan.")
            return

        if ctx.obj.get("format") == "json":
            output_json(bucket_list)
        else:
            print_buckets_table(bucket_list)
    finally:
        await client.close()


@buckets.command("get")
@click.argument("bucket_id")
@click.pass_context
@handle_api_errors
@async_command
async def get_bucket(ctx: click.Context, bucket_id: str) -> None:
    """Get a bucket by ID.

    BUCKET_ID: The bucket ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        bucket = await planner_api.get_bucket(bucket_id)

        if ctx.obj.get("format") == "json":
            output_json(bucket)
        else:
            print_bucket_detail(bucket)
    finally:
        await client.close()


@buckets.command("create")
@click.argument("plan_id")
@click.argument("name")
@click.pass_context
@handle_api_errors
@async_command
async def create_bucket(ctx: click.Context, plan_id: str, name: str) -> None:
    """Create a new bucket.

    PLAN_ID: The plan ID.
    NAME: The bucket name.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        bucket = await planner_api.create_bucket(plan_id, name)

        if ctx.obj.get("format") == "json":
            output_json(bucket)
        else:
            output_success(f"Created bucket: {bucket.name} (ID: {bucket.id})")
    finally:
        await client.close()


@buckets.command("update")
@click.argument("bucket_id")
@click.option("--name", "-n", help="New name for the bucket.")
@click.pass_context
@handle_api_errors
@async_command
async def update_bucket(
    ctx: click.Context, bucket_id: str, name: str | None
) -> None:
    """Update a bucket.

    BUCKET_ID: The bucket ID.
    """
    if not name:
        click.echo("Error: At least one option (--name) is required.")
        return

    client, planner_api, _ = get_client_and_api()

    try:
        # Get current bucket to retrieve ETag
        current = await planner_api.get_bucket(bucket_id)
        if not current.etag:
            click.echo("Error: Could not retrieve ETag for bucket.")
            return

        data = {}
        if name:
            data["name"] = name

        bucket = await planner_api.update_bucket(bucket_id, data, current.etag)

        if ctx.obj.get("format") == "json":
            output_json(bucket)
        else:
            output_success(f"Updated bucket: {bucket.name}")
    finally:
        await client.close()


@buckets.command("delete")
@click.argument("bucket_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@click.pass_context
@handle_api_errors
@async_command
async def delete_bucket(ctx: click.Context, bucket_id: str, yes: bool) -> None:
    """Delete a bucket.

    BUCKET_ID: The bucket ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        # Get current bucket to retrieve ETag and name
        current = await planner_api.get_bucket(bucket_id)
        if not current.etag:
            click.echo("Error: Could not retrieve ETag for bucket.")
            return

        if not yes:
            click.confirm(
                f"Delete bucket '{current.name}'? This will also delete all tasks in the bucket.",
                abort=True,
            )

        await planner_api.delete_bucket(bucket_id, current.etag)
        output_success(f"Deleted bucket: {current.name}")
    finally:
        await client.close()
