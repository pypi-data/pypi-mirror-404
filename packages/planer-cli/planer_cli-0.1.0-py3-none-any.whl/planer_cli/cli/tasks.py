"""Tasks CLI commands."""

import shutil
import subprocess
from datetime import datetime, timedelta

import click

from planer_cli.api.users import UsersAPI
from planer_cli.cli.common import (
    async_command,
    get_client_and_api,
    handle_api_errors,
)
from planer_cli.output.formatter import (
    export_to_csv,
    export_to_json_file,
    output_json,
    output_success,
)
from planer_cli.output.tables import print_task_detail, print_tasks_table

PRIORITY_MAP = {
    "urgent": 0,
    "important": 1,
    "normal": 5,
    "low": 9,
}


def check_fzf_installed() -> bool:
    """Check if fzf is installed."""
    return shutil.which("fzf") is not None


def format_task_for_fzf(task) -> str:
    """Format a task for fzf display.

    Format: [status] title | priority | due | ID
    """
    # Status indicator
    if task.percent_complete == 100:
        status = "[x]"
    elif task.percent_complete > 0:
        status = f"[{task.percent_complete}%]"
    else:
        status = "[ ]"

    # Due date
    due = task.due_date_time.strftime("%Y-%m-%d") if task.due_date_time else "no due"

    # Format line: status title | priority | due | ID
    return f"{status} {task.title} | {task.priority_label} | {due} | {task.id}"


def select_task_with_fzf(tasks: list, prompt: str = "Select task") -> str | None:
    """Show fzf picker for task selection.

    Args:
        tasks: List of Task objects.
        prompt: Prompt to show in fzf.

    Returns:
        Selected task ID or None if cancelled.
    """
    if not check_fzf_installed():
        click.echo("Error: fzf is not installed. Install it with:")
        click.echo("  brew install fzf  # macOS")
        click.echo("  apt install fzf   # Ubuntu/Debian")
        return None

    if not tasks:
        click.echo("No tasks to select from.")
        return None

    # Format tasks for fzf
    lines = [format_task_for_fzf(t) for t in tasks]
    input_text = "\n".join(lines)

    try:
        result = subprocess.run(
            ["fzf", "--prompt", f"{prompt}: ", "--height", "40%", "--reverse"],
            input=input_text,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return None  # User cancelled

        # Extract task ID from selection (last part after |)
        selected = result.stdout.strip()
        if selected:
            task_id = selected.split("|")[-1].strip()
            return task_id
    except Exception as e:
        click.echo(f"Error running fzf: {e}")

    return None


def select_plan_with_fzf(plans: list, prompt: str = "Select plan") -> str | None:
    """Show fzf picker for plan selection.

    Args:
        plans: List of Plan objects.
        prompt: Prompt to show in fzf.

    Returns:
        Selected plan ID or None if cancelled.
    """
    if not check_fzf_installed():
        click.echo("Error: fzf is not installed.")
        return None

    if not plans:
        click.echo("No plans to select from.")
        return None

    lines = []
    for p in plans:
        url = f"https://tasks.office.com/Home/PlanViews/{p.id}"
        lines.append(f"{p.title} | {url} | {p.id}")
    input_text = "\n".join(lines)

    try:
        result = subprocess.run(
            ["fzf", "--prompt", f"{prompt}: ", "--height", "40%", "--reverse"],
            input=input_text,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        selected = result.stdout.strip()
        if selected:
            return selected.split("|")[-1].strip()
    except Exception as e:
        click.echo(f"Error running fzf: {e}")
    return None


def select_bucket_with_fzf(buckets: list, prompt: str = "Select bucket") -> str | None:
    """Show fzf picker for bucket selection.

    Args:
        buckets: List of Bucket objects.
        prompt: Prompt to show in fzf.

    Returns:
        Selected bucket ID or None if cancelled.
    """
    if not check_fzf_installed():
        return None

    if not buckets:
        return None

    lines = [f"{b.name} | {b.id}" for b in buckets]
    input_text = "\n".join(lines)

    try:
        result = subprocess.run(
            ["fzf", "--prompt", f"{prompt}: ", "--height", "40%", "--reverse"],
            input=input_text,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        selected = result.stdout.strip()
        if selected:
            return selected.split("|")[-1].strip()
    except Exception as e:
        click.echo(f"Error running fzf: {e}")
    return None


def select_user_with_fzf(users: list, prompt: str = "Select user") -> str | None:
    """Show fzf picker for user selection.

    Args:
        users: List of User objects.
        prompt: Prompt to show in fzf.

    Returns:
        Selected user ID or None if cancelled.
    """
    if not check_fzf_installed():
        return None

    if not users:
        return None

    lines = []
    for u in users:
        email = u.mail or u.user_principal_name or ""
        lines.append(f"{u.display_name} ({email}) | {u.id}")
    input_text = "\n".join(lines)

    try:
        result = subprocess.run(
            ["fzf", "--prompt", f"{prompt}: ", "--height", "40%", "--reverse"],
            input=input_text,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        selected = result.stdout.strip()
        if selected:
            return selected.split("|")[-1].strip()
    except Exception as e:
        click.echo(f"Error running fzf: {e}")
    return None


@click.group()
def tasks() -> None:
    """Manage Planner tasks."""
    pass


def filter_tasks(
    tasks: list,
    open_only: bool = False,
    done_only: bool = False,
    due_today: bool = False,
    overdue: bool = False,
    this_week: bool = False,
    unassigned: bool = False,
    label: str | None = None,
) -> list:
    """Filter tasks by status and due date.

    Args:
        tasks: List of tasks.
        open_only: Show only open tasks (< 100%).
        done_only: Show only completed tasks (100%).
        due_today: Show only tasks due today.
        overdue: Show only overdue tasks.
        this_week: Show only tasks due this week.
        unassigned: Show only unassigned tasks.
        label: Filter by label (category key like "category1").

    Returns:
        Filtered list of tasks.
    """
    result = tasks
    today = datetime.now().date()

    if due_today:
        result = [
            t for t in result
            if t.due_date_time and t.due_date_time.date() == today
        ]

    if overdue:
        result = [
            t for t in result
            if t.due_date_time
            and t.due_date_time.date() < today
            and t.percent_complete < 100
        ]

    if this_week:
        # Week starts on Monday
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        result = [
            t for t in result
            if t.due_date_time
            and start_of_week <= t.due_date_time.date() <= end_of_week
        ]

    if unassigned:
        result = [t for t in result if not t.assignments]

    if label:
        # Support both "category1" and "1" formats
        category_key = label if label.startswith("category") else f"category{label}"
        result = [t for t in result if category_key in t.category_keys]

    if open_only:
        result = [t for t in result if t.percent_complete < 100]
    elif done_only:
        result = [t for t in result if t.percent_complete == 100]

    return result


def sort_tasks(tasks: list, sort_by: str | None, reverse: bool = False) -> list:
    """Sort tasks by specified field.

    Args:
        tasks: List of tasks.
        sort_by: Field to sort by (due-date, priority, title, created).
        reverse: Reverse sort order.

    Returns:
        Sorted list of tasks.
    """
    if not sort_by:
        return tasks

    sort_keys = {
        "due-date": lambda t: (t.due_date_time or datetime.max, t.title.lower()),
        "priority": lambda t: (t.priority, t.title.lower()),
        "title": lambda t: t.title.lower(),
    }

    key_func = sort_keys.get(sort_by)
    if key_func:
        return sorted(tasks, key=key_func, reverse=reverse)

    return tasks


@tasks.command("my")
@click.option("--open", "-o", "open_only", is_flag=True, help="Show open tasks.")
@click.option("--done", "-d", "done_only", is_flag=True, help="Show completed tasks.")
@click.option("--due-today", "-t", "due_today", is_flag=True, help="Due today.")
@click.option("--overdue", is_flag=True, help="Show overdue tasks.")
@click.option("--this-week", "-w", "this_week", is_flag=True, help="Due this week.")
@click.option("--unassigned", "-u", is_flag=True, help="Show unassigned tasks.")
@click.option("--label", "-l", help="Filter by label (e.g., 'category1' or '1').")
@click.option(
    "--sort-by", "-s",
    type=click.Choice(["due-date", "priority", "title"]),
    help="Sort tasks by field.",
)
@click.option("--reverse", "-r", is_flag=True, help="Reverse sort order.")
@click.option("--export", "-e", "export_file", help="Export to file (.csv/.json).")
@click.pass_context
@handle_api_errors
@async_command
async def my_tasks(
    ctx: click.Context,
    open_only: bool,
    done_only: bool,
    due_today: bool,
    overdue: bool,
    this_week: bool,
    unassigned: bool,
    label: str | None,
    sort_by: str | None,
    reverse: bool,
    export_file: str | None,
) -> None:
    """List all tasks assigned to you."""
    client, planner_api, _ = get_client_and_api()

    try:
        task_list = await planner_api.list_my_tasks()
        task_list = filter_tasks(
            task_list, open_only, done_only, due_today, overdue, this_week,
            unassigned, label
        )
        task_list = sort_tasks(task_list, sort_by, reverse)

        if not task_list:
            click.echo("No tasks found.")
            return

        if export_file:
            if export_file.endswith(".csv"):
                export_to_csv(task_list, export_file)
                output_success(f"Exported {len(task_list)} tasks to {export_file}")
            elif export_file.endswith(".json"):
                export_to_json_file(task_list, export_file)
                output_success(f"Exported {len(task_list)} tasks to {export_file}")
            else:
                click.echo("Error: Export file must end with .csv or .json")
        elif ctx.obj.get("format") == "json":
            output_json(task_list)
        else:
            print_tasks_table(task_list)
    finally:
        await client.close()


@tasks.command("list")
@click.argument("plan_id")
@click.option("--open", "-o", "open_only", is_flag=True, help="Show open tasks.")
@click.option("--done", "-d", "done_only", is_flag=True, help="Show completed tasks.")
@click.option("--due-today", "-t", "due_today", is_flag=True, help="Due today.")
@click.option("--overdue", is_flag=True, help="Show overdue tasks.")
@click.option("--this-week", "-w", "this_week", is_flag=True, help="Due this week.")
@click.option("--unassigned", "-u", is_flag=True, help="Show unassigned tasks.")
@click.option("--label", "-l", help="Filter by label (e.g., 'category1' or '1').")
@click.option(
    "--sort-by", "-s",
    type=click.Choice(["due-date", "priority", "title"]),
    help="Sort tasks by field.",
)
@click.option("--reverse", "-r", is_flag=True, help="Reverse sort order.")
@click.option("--export", "-e", "export_file", help="Export to file (.csv/.json).")
@click.pass_context
@handle_api_errors
@async_command
async def list_tasks(
    ctx: click.Context,
    plan_id: str,
    open_only: bool,
    done_only: bool,
    due_today: bool,
    overdue: bool,
    this_week: bool,
    unassigned: bool,
    label: str | None,
    sort_by: str | None,
    reverse: bool,
    export_file: str | None,
) -> None:
    """List tasks in a plan.

    PLAN_ID: The plan ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        task_list = await planner_api.list_tasks(plan_id)
        task_list = filter_tasks(
            task_list, open_only, done_only, due_today, overdue, this_week,
            unassigned, label
        )
        task_list = sort_tasks(task_list, sort_by, reverse)

        if not task_list:
            click.echo("No tasks found.")
            return

        if export_file:
            if export_file.endswith(".csv"):
                export_to_csv(task_list, export_file)
                output_success(f"Exported {len(task_list)} tasks to {export_file}")
            elif export_file.endswith(".json"):
                export_to_json_file(task_list, export_file)
                output_success(f"Exported {len(task_list)} tasks to {export_file}")
            else:
                click.echo("Error: Export file must end with .csv or .json")
        elif ctx.obj.get("format") == "json":
            output_json(task_list)
        else:
            print_tasks_table(task_list)
    finally:
        await client.close()


@tasks.command("list-bucket")
@click.argument("bucket_id")
@click.option("--open", "-o", "open_only", is_flag=True, help="Show open tasks.")
@click.option("--done", "-d", "done_only", is_flag=True, help="Show completed tasks.")
@click.option("--due-today", "-t", "due_today", is_flag=True, help="Due today.")
@click.option("--overdue", is_flag=True, help="Show overdue tasks.")
@click.option("--this-week", "-w", "this_week", is_flag=True, help="Due this week.")
@click.option("--unassigned", "-u", is_flag=True, help="Show unassigned tasks.")
@click.option("--label", "-l", help="Filter by label (e.g., 'category1' or '1').")
@click.option(
    "--sort-by", "-s",
    type=click.Choice(["due-date", "priority", "title"]),
    help="Sort tasks by field.",
)
@click.option("--reverse", "-r", is_flag=True, help="Reverse sort order.")
@click.option("--export", "-e", "export_file", help="Export to file (.csv/.json).")
@click.pass_context
@handle_api_errors
@async_command
async def list_bucket_tasks(
    ctx: click.Context,
    bucket_id: str,
    open_only: bool,
    done_only: bool,
    due_today: bool,
    overdue: bool,
    this_week: bool,
    unassigned: bool,
    label: str | None,
    sort_by: str | None,
    reverse: bool,
    export_file: str | None,
) -> None:
    """List tasks in a bucket.

    BUCKET_ID: The bucket ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        task_list = await planner_api.list_bucket_tasks(bucket_id)
        task_list = filter_tasks(
            task_list, open_only, done_only, due_today, overdue, this_week,
            unassigned, label
        )
        task_list = sort_tasks(task_list, sort_by, reverse)

        if not task_list:
            click.echo("No tasks found.")
            return

        if export_file:
            if export_file.endswith(".csv"):
                export_to_csv(task_list, export_file)
                output_success(f"Exported {len(task_list)} tasks to {export_file}")
            elif export_file.endswith(".json"):
                export_to_json_file(task_list, export_file)
                output_success(f"Exported {len(task_list)} tasks to {export_file}")
            else:
                click.echo("Error: Export file must end with .csv or .json")
        elif ctx.obj.get("format") == "json":
            output_json(task_list)
        else:
            print_tasks_table(task_list)
    finally:
        await client.close()


@tasks.command("get")
@click.argument("task_id", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Select task with fzf.")
@click.pass_context
@handle_api_errors
@async_command
async def get_task(
    ctx: click.Context, task_id: str | None, interactive: bool
) -> None:
    """Get a task by ID.

    TASK_ID: The task ID (optional with --interactive).
    """
    client, planner_api, _ = get_client_and_api()

    try:
        # Interactive selection
        if interactive:
            task_list = await planner_api.list_my_tasks()
            task_id = select_task_with_fzf(task_list, "View task")
            if not task_id:
                return

        if not task_id:
            click.echo("Error: TASK_ID required (or use --interactive).")
            return

        task = await planner_api.get_task(task_id)
        details = await planner_api.get_task_details(task_id)

        # Get category descriptions from plan details
        category_descriptions = None
        try:
            plan_details = await planner_api.get_plan_details(task.plan_id)
            category_descriptions = plan_details.category_descriptions
        except Exception:
            pass  # Ignore if can't get plan details

        if ctx.obj.get("format") == "json":
            # Combine task and details for JSON output
            task_dict = task.model_dump(by_alias=True)
            task_dict["notes"] = details.description
            output_json(task_dict)
        else:
            print_task_detail(task, details, category_descriptions)
    finally:
        await client.close()


@tasks.command("create")
@click.argument("plan_id", required=False)
@click.argument("title", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode with fzf.")
@click.option("--bucket-id", "-b", help="Bucket ID to add the task to.")
@click.option(
    "--due-date",
    "-d",
    help="Due date (YYYY-MM-DD format).",
)
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["urgent", "important", "normal", "low"]),
    default="normal",
    help="Task priority.",
)
@click.option("--notes", "-n", help="Task notes/description.")
@click.pass_context
@handle_api_errors
@async_command
async def create_task(
    ctx: click.Context,
    plan_id: str | None,
    title: str | None,
    interactive: bool,
    bucket_id: str | None,
    due_date: str | None,
    priority: str,
    notes: str | None,
) -> None:
    """Create a new task.

    PLAN_ID: The plan ID (optional with --interactive).
    TITLE: The task title (will prompt if not provided).
    """
    client, planner_api, _ = get_client_and_api()

    assign_user_id = None

    try:
        # Interactive mode: select plan and optionally bucket
        if interactive:
            plans = await planner_api.list_all_my_plans()
            plan_id = select_plan_with_fzf(plans, "Select plan")
            if not plan_id:
                return

            # Optionally select bucket
            buckets = await planner_api.list_buckets(plan_id)
            if buckets:
                if click.confirm("Select a bucket?", default=False):
                    bucket_id = select_bucket_with_fzf(buckets, "Select bucket")

            # Prompt for due date
            if not due_date:
                if click.confirm("Set due date?", default=False):
                    due_date = click.prompt("Due date (YYYY-MM-DD)")

            # Optionally assign to user
            if click.confirm("Assign to someone?", default=False):
                users_api = UsersAPI(client)
                search_term = click.prompt(
                    "Search user (name/email)", default="", show_default=False
                )
                users = await users_api.list_users(
                    search_term if search_term else None
                )
                if users:
                    assign_user_id = select_user_with_fzf(users, "Assign to")
                else:
                    click.echo("No users found.")

        if not plan_id:
            click.echo("Error: PLAN_ID required (or use --interactive).")
            return

        # Prompt for title if not provided
        if not title:
            title = click.prompt("Task title")

        # Parse and format due date
        formatted_due_date = None
        if due_date:
            try:
                parsed = datetime.strptime(due_date, "%Y-%m-%d")
                formatted_due_date = parsed.strftime("%Y-%m-%dT00:00:00Z")
            except ValueError:
                click.echo("Error: Due date must be in YYYY-MM-DD format.")
                return

        task = await planner_api.create_task(
            plan_id=plan_id,
            title=title,
            bucket_id=bucket_id,
            due_date=formatted_due_date,
            priority=PRIORITY_MAP.get(priority, 5),
        )

        # Update task details if notes provided
        if notes:
            details = await planner_api.get_task_details(task.id)
            if details.etag:
                await planner_api.update_task_details(
                    task.id, {"description": notes}, details.etag
                )

        # Assign to user if selected
        if assign_user_id:
            task = await planner_api.get_task(task.id)  # Refresh for new etag
            if task.etag:
                await planner_api.assign_task(task.id, assign_user_id, task.etag)

        if ctx.obj.get("format") == "json":
            output_json(task)
        else:
            output_success(f"Created task: {task.title} (ID: {task.id})")
    finally:
        await client.close()


@tasks.command("update")
@click.argument("task_id", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Select task with fzf.")
@click.option("--title", "-t", help="New title.")
@click.option("--progress", "-g", type=int, help="Percent complete (0-100).")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["urgent", "important", "normal", "low"]),
    help="Task priority.",
)
@click.option("--due-date", "-d", help="Due date (YYYY-MM-DD format).")
@click.option("--bucket-id", "-b", help="Move to a different bucket.")
@click.option("--notes", "-n", help="Task notes/description.")
@click.option("--label", "-l", multiple=True, help="Add label (1-25).")
@click.option("--remove-label", multiple=True, help="Remove label.")
@click.pass_context
@handle_api_errors
@async_command
async def update_task(
    ctx: click.Context,
    task_id: str | None,
    interactive: bool,
    title: str | None,
    progress: int | None,
    priority: str | None,
    due_date: str | None,
    bucket_id: str | None,
    notes: str | None,
    label: tuple[str, ...],
    remove_label: tuple[str, ...],
) -> None:
    """Update a task.

    TASK_ID: The task ID (optional with --interactive).
    """
    has_labels = label or remove_label
    if not any([title, progress is not None, priority, due_date, bucket_id, notes,
                has_labels, interactive]):
        click.echo("Error: At least one option is required.")
        return

    client, planner_api, _ = get_client_and_api()

    try:
        # Interactive selection
        if interactive:
            task_list = await planner_api.list_my_tasks()
            task_id = select_task_with_fzf(task_list, "Update task")
            if not task_id:
                return

        if not task_id:
            click.echo("Error: TASK_ID required (or use --interactive).")
            return

        # Get current task to retrieve ETag
        current = await planner_api.get_task(task_id)
        if not current.etag:
            click.echo("Error: Could not retrieve ETag for task.")
            return

        data: dict = {}
        if title:
            data["title"] = title
        if progress is not None:
            if not 0 <= progress <= 100:
                click.echo("Error: Progress must be between 0 and 100.")
                return
            data["percentComplete"] = progress
        if priority:
            data["priority"] = PRIORITY_MAP.get(priority, 5)
        if due_date:
            try:
                parsed = datetime.strptime(due_date, "%Y-%m-%d")
                data["dueDateTime"] = parsed.strftime("%Y-%m-%dT00:00:00Z")
            except ValueError:
                click.echo("Error: Due date must be in YYYY-MM-DD format.")
                return
        if bucket_id:
            data["bucketId"] = bucket_id

        # Handle labels
        if has_labels:
            applied = current.applied_categories or {}
            for lbl in label:
                key = lbl if lbl.startswith("category") else f"category{lbl}"
                applied[key] = True
            for lbl in remove_label:
                key = lbl if lbl.startswith("category") else f"category{lbl}"
                applied[key] = False
            data["appliedCategories"] = applied

        # Update task if there are task-level changes
        task = current
        if data:
            task = await planner_api.update_task(task_id, data, current.etag)

        # Update task details if notes provided
        if notes:
            details = await planner_api.get_task_details(task_id)
            if details.etag:
                await planner_api.update_task_details(
                    task_id, {"description": notes}, details.etag
                )

        if ctx.obj.get("format") == "json":
            output_json(task)
        else:
            output_success(f"Updated task: {task.title}")
    finally:
        await client.close()


@tasks.command("complete")
@click.argument("task_id", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Select task with fzf.")
@click.pass_context
@handle_api_errors
@async_command
async def complete_task(
    ctx: click.Context, task_id: str | None, interactive: bool
) -> None:
    """Mark a task as complete (100%).

    TASK_ID: The task ID (optional with --interactive).
    """
    client, planner_api, _ = get_client_and_api()

    try:
        # Interactive selection
        if interactive:
            task_list = await planner_api.list_my_tasks()
            # Filter to only incomplete tasks
            task_list = [t for t in task_list if t.percent_complete < 100]
            task_id = select_task_with_fzf(task_list, "Complete task")
            if not task_id:
                return

        if not task_id:
            click.echo("Error: TASK_ID required (or use --interactive).")
            return

        # Get current task to retrieve ETag
        current = await planner_api.get_task(task_id)
        if not current.etag:
            click.echo("Error: Could not retrieve ETag for task.")
            return

        task = await planner_api.complete_task(task_id, current.etag)

        if ctx.obj.get("format") == "json":
            output_json(task)
        else:
            output_success(f"Completed task: {task.title}")
    finally:
        await client.close()


@tasks.command("assign")
@click.argument("task_id", required=False)
@click.argument("user_id", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive fzf selection.")
@click.pass_context
@handle_api_errors
@async_command
async def assign_task(
    ctx: click.Context,
    task_id: str | None,
    user_id: str | None,
    interactive: bool,
) -> None:
    """Assign a task to a user.

    TASK_ID: The task ID (optional with --interactive).
    USER_ID: The user ID (optional with --interactive).
    """
    client, planner_api, _ = get_client_and_api()

    try:
        # Interactive mode: select task and user
        if interactive:
            # Select task
            task_list = await planner_api.list_my_tasks()
            task_list = [t for t in task_list if t.percent_complete < 100]
            task_id = select_task_with_fzf(task_list, "Select task to assign")
            if not task_id:
                return

            # Select user - prompt for search term to find specific users
            users_api = UsersAPI(client)
            search_term = click.prompt(
                "Search user (name/email)", default="", show_default=False
            )
            users = await users_api.list_users(search_term if search_term else None)
            if not users:
                click.echo("No users found.")
                return
            user_id = select_user_with_fzf(users, "Assign to")
            if not user_id:
                return

        if not task_id:
            click.echo("Error: TASK_ID required (or use --interactive).")
            return
        if not user_id:
            click.echo("Error: USER_ID required (or use --interactive).")
            return

        # Get current task to retrieve ETag
        current = await planner_api.get_task(task_id)
        if not current.etag:
            click.echo("Error: Could not retrieve ETag for task.")
            return

        task = await planner_api.assign_task(task_id, user_id, current.etag)

        if ctx.obj.get("format") == "json":
            output_json(task)
        else:
            output_success(f"Assigned task: {task.title}")
    finally:
        await client.close()


@tasks.command("delete")
@click.argument("task_id", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Select task with fzf.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@click.pass_context
@handle_api_errors
@async_command
async def delete_task(
    ctx: click.Context, task_id: str | None, interactive: bool, yes: bool
) -> None:
    """Delete a task.

    TASK_ID: The task ID (optional with --interactive).
    """
    client, planner_api, _ = get_client_and_api()

    try:
        # Interactive selection
        if interactive:
            task_list = await planner_api.list_my_tasks()
            task_id = select_task_with_fzf(task_list, "Delete task")
            if not task_id:
                return

        if not task_id:
            click.echo("Error: TASK_ID required (or use --interactive).")
            return

        # Get current task to retrieve ETag and title
        current = await planner_api.get_task(task_id)
        if not current.etag:
            click.echo("Error: Could not retrieve ETag for task.")
            return

        if not yes:
            click.confirm(
                f"Delete task '{current.title}'? This cannot be undone.",
                abort=True,
            )

        await planner_api.delete_task(task_id, current.etag)
        output_success(f"Deleted task: {current.title}")
    finally:
        await client.close()


# ========== Batch Commands ==========


@tasks.command("complete-all")
@click.option("--plan-id", "-p", help="Complete all tasks in this plan.")
@click.option("--bucket-id", "-b", help="Complete all tasks in this bucket.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@click.pass_context
@handle_api_errors
@async_command
async def complete_all_tasks(
    ctx: click.Context,
    plan_id: str | None,
    bucket_id: str | None,
    yes: bool,
) -> None:
    """Complete all tasks in a plan or bucket.

    Must specify either --plan-id or --bucket-id.
    """
    if not plan_id and not bucket_id:
        click.echo("Error: Must specify --plan-id or --bucket-id")
        return

    client, planner_api, _ = get_client_and_api()

    try:
        # Get tasks to complete
        if bucket_id:
            task_list = await planner_api.list_bucket_tasks(bucket_id)
            scope = f"bucket {bucket_id}"
        else:
            task_list = await planner_api.list_tasks(plan_id)
            scope = f"plan {plan_id}"

        # Filter to only incomplete tasks
        incomplete = [t for t in task_list if t.percent_complete < 100]

        if not incomplete:
            click.echo("No incomplete tasks found.")
            return

        if not yes:
            click.confirm(
                f"Complete {len(incomplete)} tasks in {scope}?",
                abort=True,
            )

        # Complete each task
        completed = 0
        for task in incomplete:
            if task.etag:
                await planner_api.complete_task(task.id, task.etag)
                completed += 1

        output_success(f"Completed {completed} tasks")
    finally:
        await client.close()


@tasks.command("move-all")
@click.option("--from-bucket", "-f", required=True, help="Source bucket ID.")
@click.option("--to-bucket", "-t", required=True, help="Destination bucket ID.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@click.pass_context
@handle_api_errors
@async_command
async def move_all_tasks(
    ctx: click.Context,
    from_bucket: str,
    to_bucket: str,
    yes: bool,
) -> None:
    """Move all tasks from one bucket to another.

    Both buckets must be in the same plan.
    """
    if from_bucket == to_bucket:
        click.echo("Error: Source and destination buckets are the same.")
        return

    client, planner_api, _ = get_client_and_api()

    try:
        # Get tasks from source bucket
        task_list = await planner_api.list_bucket_tasks(from_bucket)

        if not task_list:
            click.echo("No tasks in source bucket.")
            return

        if not yes:
            click.confirm(
                f"Move {len(task_list)} tasks to bucket {to_bucket}?",
                abort=True,
            )

        # Move each task
        moved = 0
        for task in task_list:
            if task.etag:
                await planner_api.update_task(
                    task.id, {"bucketId": to_bucket}, task.etag
                )
                moved += 1

        output_success(f"Moved {moved} tasks")
    finally:
        await client.close()


@tasks.command("delete-all")
@click.option("--plan-id", "-p", help="Delete all tasks in this plan.")
@click.option("--bucket-id", "-b", help="Delete all tasks in this bucket.")
@click.option("--done-only", "-d", is_flag=True, help="Only delete completed tasks.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@click.pass_context
@handle_api_errors
@async_command
async def delete_all_tasks(
    ctx: click.Context,
    plan_id: str | None,
    bucket_id: str | None,
    done_only: bool,
    yes: bool,
) -> None:
    """Delete all tasks in a plan or bucket.

    Must specify either --plan-id or --bucket-id.
    Use --done-only to only delete completed tasks.
    """
    if not plan_id and not bucket_id:
        click.echo("Error: Must specify --plan-id or --bucket-id")
        return

    client, planner_api, _ = get_client_and_api()

    try:
        # Get tasks to delete
        if bucket_id:
            task_list = await planner_api.list_bucket_tasks(bucket_id)
            scope = f"bucket {bucket_id}"
        else:
            task_list = await planner_api.list_tasks(plan_id)
            scope = f"plan {plan_id}"

        # Filter if done-only
        if done_only:
            task_list = [t for t in task_list if t.percent_complete == 100]

        if not task_list:
            click.echo("No tasks to delete.")
            return

        if not yes:
            msg = f"DELETE {len(task_list)} tasks from {scope}? This cannot be undone."
            click.confirm(msg, abort=True)

        # Delete each task
        deleted = 0
        for task in task_list:
            if task.etag:
                await planner_api.delete_task(task.id, task.etag)
                deleted += 1

        output_success(f"Deleted {deleted} tasks")
    finally:
        await client.close()


# ========== Checklist Commands ==========


@tasks.group("checklist")
def checklist() -> None:
    """Manage task checklists."""
    pass


@checklist.command("list")
@click.argument("task_id")
@click.pass_context
@handle_api_errors
@async_command
async def list_checklist(ctx: click.Context, task_id: str) -> None:
    """List checklist items for a task.

    TASK_ID: The task ID.
    """
    from planer_cli.output.tables import print_checklist

    client, planner_api, _ = get_client_and_api()

    try:
        details = await planner_api.get_task_details(task_id)

        if not details.checklist:
            click.echo("No checklist items.")
            return

        if ctx.obj.get("format") == "json":
            output_json(details.checklist)
        else:
            print_checklist(details.checklist)
    finally:
        await client.close()


@checklist.command("add")
@click.argument("task_id")
@click.argument("title")
@click.pass_context
@handle_api_errors
@async_command
async def add_checklist_item(ctx: click.Context, task_id: str, title: str) -> None:
    """Add a checklist item to a task.

    TASK_ID: The task ID.
    TITLE: The checklist item title.
    """
    import uuid

    client, planner_api, _ = get_client_and_api()

    try:
        details = await planner_api.get_task_details(task_id)
        if not details.etag:
            click.echo("Error: Could not retrieve ETag for task details.")
            return

        # Generate a new item ID
        item_id = str(uuid.uuid4())

        # Build checklist update - need to add to existing checklist
        checklist_update = {
            item_id: {
                "@odata.type": "#microsoft.graph.plannerChecklistItem",
                "title": title,
                "isChecked": False,
            }
        }

        await planner_api.update_task_details(
            task_id, {"checklist": checklist_update}, details.etag
        )

        output_success(f"Added checklist item: {title}")
    finally:
        await client.close()


@checklist.command("check")
@click.argument("task_id")
@click.argument("item_id")
@click.pass_context
@handle_api_errors
@async_command
async def check_item(ctx: click.Context, task_id: str, item_id: str) -> None:
    """Mark a checklist item as done.

    TASK_ID: The task ID.
    ITEM_ID: The checklist item ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        details = await planner_api.get_task_details(task_id)
        if not details.etag:
            click.echo("Error: Could not retrieve ETag for task details.")
            return

        if not details.checklist or item_id not in details.checklist:
            click.echo(f"Error: Checklist item '{item_id}' not found.")
            return

        checklist_update = {
            item_id: {
                "@odata.type": "#microsoft.graph.plannerChecklistItem",
                "isChecked": True,
            }
        }

        await planner_api.update_task_details(
            task_id, {"checklist": checklist_update}, details.etag
        )

        item_title = details.checklist[item_id].get("title", item_id)
        output_success(f"Checked: {item_title}")
    finally:
        await client.close()


@checklist.command("uncheck")
@click.argument("task_id")
@click.argument("item_id")
@click.pass_context
@handle_api_errors
@async_command
async def uncheck_item(ctx: click.Context, task_id: str, item_id: str) -> None:
    """Mark a checklist item as not done.

    TASK_ID: The task ID.
    ITEM_ID: The checklist item ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        details = await planner_api.get_task_details(task_id)
        if not details.etag:
            click.echo("Error: Could not retrieve ETag for task details.")
            return

        if not details.checklist or item_id not in details.checklist:
            click.echo(f"Error: Checklist item '{item_id}' not found.")
            return

        checklist_update = {
            item_id: {
                "@odata.type": "#microsoft.graph.plannerChecklistItem",
                "isChecked": False,
            }
        }

        await planner_api.update_task_details(
            task_id, {"checklist": checklist_update}, details.etag
        )

        item_title = details.checklist[item_id].get("title", item_id)
        output_success(f"Unchecked: {item_title}")
    finally:
        await client.close()


@checklist.command("remove")
@click.argument("task_id")
@click.argument("item_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@click.pass_context
@handle_api_errors
@async_command
async def remove_checklist_item(
    ctx: click.Context, task_id: str, item_id: str, yes: bool
) -> None:
    """Remove a checklist item from a task.

    TASK_ID: The task ID.
    ITEM_ID: The checklist item ID.
    """
    client, planner_api, _ = get_client_and_api()

    try:
        details = await planner_api.get_task_details(task_id)
        if not details.etag:
            click.echo("Error: Could not retrieve ETag for task details.")
            return

        if not details.checklist or item_id not in details.checklist:
            click.echo(f"Error: Checklist item '{item_id}' not found.")
            return

        item_title = details.checklist[item_id].get("title", item_id)

        if not yes:
            click.confirm(f"Remove checklist item '{item_title}'?", abort=True)

        # Set item to null to remove it
        checklist_update = {item_id: None}

        await planner_api.update_task_details(
            task_id, {"checklist": checklist_update}, details.etag
        )

        output_success(f"Removed checklist item: {item_title}")
    finally:
        await client.close()
