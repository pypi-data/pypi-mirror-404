"""Plans CLI commands."""

import click

from planer_cli.cli.common import async_command, get_client_and_api, handle_api_errors
from planer_cli.output.formatter import output_json, output_success
from planer_cli.output.tables import (
    print_labels_table,
    print_plan_detail,
    print_plans_table,
)


@click.group()
def plans() -> None:
    """Manage Planner plans."""
    pass


@plans.command("my")
@click.pass_context
@handle_api_errors
@async_command
async def my_plans(ctx: click.Context) -> None:
    """List plans you have tasks in."""
    client, planner_api, _ = get_client_and_api()

    try:
        plan_list = await planner_api.list_my_plans()

        if not plan_list:
            click.echo("No plans found.")
            return

        if ctx.obj.get("format") == "json":
            output_json(plan_list)
        else:
            print_plans_table(plan_list)
    finally:
        await client.close()


@plans.command("list")
@click.argument("group_id")
@click.pass_context
@handle_api_errors
@async_command
async def list_plans(ctx: click.Context, group_id: str) -> None:
    """List plans in a group.

    GROUP_ID: The Microsoft 365 group ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        plan_list = await planner_api.list_plans(group_id)

        if not plan_list:
            click.echo("No plans found in this group.")
            return

        if ctx.obj.get("format") == "json":
            output_json(plan_list)
        else:
            print_plans_table(plan_list)
    finally:
        await client.close()


@plans.command("get")
@click.argument("plan_id")
@click.pass_context
@handle_api_errors
@async_command
async def get_plan(ctx: click.Context, plan_id: str) -> None:
    """Get a plan by ID.

    PLAN_ID: The plan ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        plan = await planner_api.get_plan(plan_id)

        if ctx.obj.get("format") == "json":
            output_json(plan)
        else:
            print_plan_detail(plan)
    finally:
        await client.close()


@plans.command("create")
@click.argument("group_id")
@click.argument("title")
@click.pass_context
@handle_api_errors
@async_command
async def create_plan(ctx: click.Context, group_id: str, title: str) -> None:
    """Create a new plan.

    GROUP_ID: The Microsoft 365 group ID (owner).
    TITLE: The plan title.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        plan = await planner_api.create_plan(group_id, title)

        if ctx.obj.get("format") == "json":
            output_json(plan)
        else:
            output_success(f"Created plan: {plan.title} (ID: {plan.id})")
    finally:
        await client.close()


@plans.command("update")
@click.argument("plan_id")
@click.option("--title", "-t", help="New title for the plan.")
@click.pass_context
@handle_api_errors
@async_command
async def update_plan(
    ctx: click.Context, plan_id: str, title: str | None
) -> None:
    """Update a plan.

    PLAN_ID: The plan ID.
    """
    if not title:
        click.echo("Error: At least one option (--title) is required.")
        return

    client, planner_api, _ = get_client_and_api()

    try:
        # Get current plan to retrieve ETag
        current = await planner_api.get_plan(plan_id)
        if not current.etag:
            click.echo("Error: Could not retrieve ETag for plan.")
            return

        data = {}
        if title:
            data["title"] = title

        plan = await planner_api.update_plan(plan_id, data, current.etag)

        if ctx.obj.get("format") == "json":
            output_json(plan)
        else:
            output_success(f"Updated plan: {plan.title}")
    finally:
        await client.close()


@plans.command("delete")
@click.argument("plan_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@click.pass_context
@handle_api_errors
@async_command
async def delete_plan(ctx: click.Context, plan_id: str, yes: bool) -> None:
    """Delete a plan.

    PLAN_ID: The plan ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        # Get current plan to retrieve ETag and title
        current = await planner_api.get_plan(plan_id)
        if not current.etag:
            click.echo("Error: Could not retrieve ETag for plan.")
            return

        if not yes:
            click.confirm(
                f"Delete plan '{current.title}'? This cannot be undone.",
                abort=True,
            )

        await planner_api.delete_plan(plan_id, current.etag)
        output_success(f"Deleted plan: {current.title}")
    finally:
        await client.close()


# ========== Labels Commands ==========


@plans.command("labels")
@click.argument("plan_id")
@click.pass_context
@handle_api_errors
@async_command
async def show_labels(ctx: click.Context, plan_id: str) -> None:
    """Show labels defined for a plan.

    PLAN_ID: The plan ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        details = await planner_api.get_plan_details(plan_id)

        if ctx.obj.get("format") == "json":
            output_json(details.category_descriptions or {})
        else:
            print_labels_table(details.category_descriptions or {})
    finally:
        await client.close()


@plans.command("set-label")
@click.argument("plan_id")
@click.argument("label_key")
@click.argument("label_name")
@click.pass_context
@handle_api_errors
@async_command
async def set_label(
    ctx: click.Context, plan_id: str, label_key: str, label_name: str
) -> None:
    """Set a label name for a plan.

    PLAN_ID: The plan ID.
    LABEL_KEY: The label key (1-25 or category1-category25).
    LABEL_NAME: The label name/description.
    """
    client, planner_api, _ = get_client_and_api()

    # Normalize key
    key = label_key if label_key.startswith("category") else f"category{label_key}"

    try:
        details = await planner_api.get_plan_details(plan_id)
        if not details.etag:
            click.echo("Error: Could not retrieve ETag for plan details.")
            return

        await planner_api.update_plan_details(
            plan_id, {"categoryDescriptions": {key: label_name}}, details.etag
        )

        output_success(f"Set {key} = '{label_name}'")
    finally:
        await client.close()
