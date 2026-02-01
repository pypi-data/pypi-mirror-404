"""Rich table definitions for entities."""

from rich.console import Console
from rich.table import Table

from planer_cli.models.bucket import Bucket
from planer_cli.models.group import Group
from planer_cli.models.plan import Plan
from planer_cli.models.task import Task, TaskDetails
from planer_cli.models.user import User

console = Console()


def print_groups_table(groups: list[Group]) -> None:
    """Print groups as a table.

    Args:
        groups: List of groups.
    """
    table = Table(title="Microsoft 365 Groups")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Mail", style="green")

    for group in groups:
        table.add_row(group.id, group.display_name, group.mail or "-")

    console.print(table)


def print_plans_table(plans: list[Plan]) -> None:
    """Print plans as a table.

    Args:
        plans: List of plans.
    """
    table = Table(title="Plans")
    table.add_column("ID", style="dim")
    table.add_column("Title", style="cyan")
    table.add_column("Created", style="green")

    for plan in plans:
        created = (
            plan.created_date_time.strftime("%Y-%m-%d")
            if plan.created_date_time
            else "-"
        )
        table.add_row(plan.id, plan.title, created)

    console.print(table)


def print_plan_detail(plan: Plan) -> None:
    """Print plan details.

    Args:
        plan: Plan object.
    """
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("ID", plan.id)
    table.add_row("Title", plan.title)
    table.add_row("Owner (Group)", plan.owner)
    if plan.created_date_time:
        table.add_row("Created", plan.created_date_time.strftime("%Y-%m-%d %H:%M"))
    if plan.etag:
        table.add_row("ETag", plan.etag)

    console.print(table)


def print_buckets_table(buckets: list[Bucket]) -> None:
    """Print buckets as a table.

    Args:
        buckets: List of buckets.
    """
    table = Table(title="Buckets")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")

    for bucket in buckets:
        table.add_row(bucket.id, bucket.name)

    console.print(table)


def print_bucket_detail(bucket: Bucket) -> None:
    """Print bucket details.

    Args:
        bucket: Bucket object.
    """
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("ID", bucket.id)
    table.add_row("Name", bucket.name)
    table.add_row("Plan ID", bucket.plan_id)
    if bucket.etag:
        table.add_row("ETag", bucket.etag)

    console.print(table)


def print_tasks_table(tasks: list[Task]) -> None:
    """Print tasks as a table.

    Args:
        tasks: List of tasks.
    """
    table = Table(title="Tasks")
    table.add_column("Status", justify="center")
    table.add_column("Title", style="cyan")
    table.add_column("Priority")
    table.add_column("Due Date", style="yellow")
    table.add_column("ID", style="dim", max_width=20)

    for task in tasks:
        # Status indicator (escape brackets for Rich)
        if task.percent_complete == 100:
            status = "[green]\\[x][/green]"
        elif task.percent_complete > 0:
            status = f"[yellow]\\[{task.percent_complete}%][/yellow]"
        else:
            status = "[ ]"

        # Priority with color
        priority_colors = {
            "Urgent": "[red]Urgent[/red]",
            "Important": "[yellow]Important[/yellow]",
            "Normal": "[dim]Normal[/dim]",
            "Low": "[dim]Low[/dim]",
        }
        priority = priority_colors.get(task.priority_label, task.priority_label)

        due = (
            task.due_date_time.strftime("%Y-%m-%d")
            if task.due_date_time
            else "-"
        )

        table.add_row(status, task.title, priority, due, task.id[:20] + "...")

    console.print(table)


def print_task_detail(
    task: Task,
    details: TaskDetails | None = None,
    category_descriptions: dict | None = None,
) -> None:
    """Print task details.

    Args:
        task: Task object.
        details: Optional TaskDetails object with description/notes.
        category_descriptions: Optional dict mapping category keys to labels.
    """
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("ID", task.id)
    table.add_row("Title", task.title)
    table.add_row("Plan ID", task.plan_id)
    table.add_row("Bucket ID", task.bucket_id or "-")

    # Progress with color
    if task.percent_complete == 100:
        progress = "[green]100% (Complete)[/green]"
    else:
        progress = f"{task.percent_complete}%"
    table.add_row("Progress", progress)

    table.add_row("Priority", task.priority_label)

    # Show labels if any
    if task.category_keys:
        labels = get_label_names(task.category_keys, category_descriptions)
        table.add_row("Labels", ", ".join(labels))

    if task.start_date_time:
        table.add_row("Start Date", task.start_date_time.strftime("%Y-%m-%d"))
    if task.due_date_time:
        table.add_row("Due Date", task.due_date_time.strftime("%Y-%m-%d"))
    if task.completed_date_time:
        table.add_row(
            "Completed",
            task.completed_date_time.strftime("%Y-%m-%d %H:%M"),
        )

    # Show notes/description if available
    if details and details.description:
        table.add_row("Notes", details.description)

    if task.etag:
        table.add_row("ETag", task.etag)

    console.print(table)

    # Show checklist if available
    if details and details.checklist:
        print_checklist(details.checklist)


def get_label_names(
    category_keys: list[str], category_descriptions: dict | None
) -> list[str]:
    """Convert category keys to label names.

    Args:
        category_keys: List of category keys (category1, category2, etc.).
        category_descriptions: Dict mapping keys to descriptions.

    Returns:
        List of label names.
    """
    labels = []
    for key in category_keys:
        if category_descriptions and key in category_descriptions:
            labels.append(category_descriptions[key])
        else:
            # Use key as fallback (e.g., "category1" -> "Label 1")
            num = key.replace("category", "")
            labels.append(f"Label {num}")
    return labels


def print_labels_table(category_descriptions: dict) -> None:
    """Print plan labels/categories table.

    Args:
        category_descriptions: Dict mapping category keys to descriptions.
    """
    table = Table(title="Plan Labels")
    table.add_column("Key", style="dim")
    table.add_column("Label", style="cyan")

    # Sort by category number
    sorted_items = sorted(
        category_descriptions.items(),
        key=lambda x: int(x[0].replace("category", "")),
    )

    for key, description in sorted_items:
        if description:  # Only show defined labels
            table.add_row(key, description)

    if not any(desc for desc in category_descriptions.values()):
        console.print("[dim]No labels defined for this plan.[/dim]")
    else:
        console.print(table)


def print_checklist(checklist: dict) -> None:
    """Print checklist items.

    Args:
        checklist: Checklist dictionary from task details.
    """
    if not checklist:
        return

    console.print()
    table = Table(title="Checklist")
    table.add_column("Status", justify="center", width=6)
    table.add_column("Item", style="cyan")
    table.add_column("ID", style="dim", max_width=20)

    # Sort items by orderHint if available
    items = []
    for item_id, item_data in checklist.items():
        items.append((item_id, item_data))

    # Sort by orderHint (string comparison works for Planner's orderHint)
    items.sort(key=lambda x: x[1].get("orderHint", ""))

    for item_id, item_data in items:
        is_checked = item_data.get("isChecked", False)
        title = item_data.get("title", "")

        if is_checked:
            status = "[green]\\[x][/green]"
            title_styled = f"[dim]{title}[/dim]"
        else:
            status = "[ ]"
            title_styled = title

        table.add_row(status, title_styled, item_id[:20] + "...")

    console.print(table)


def print_users_table(users: list[User]) -> None:
    """Print users as a table.

    Args:
        users: List of users.
    """
    table = Table(title="Users")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Email", style="green")
    table.add_column("Job Title", style="yellow")

    for user in users:
        table.add_row(
            user.id,
            user.display_name,
            user.mail or user.user_principal_name or "-",
            user.job_title or "-",
        )

    console.print(table)


def print_user_detail(user: User) -> None:
    """Print user details.

    Args:
        user: User object.
    """
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("ID", user.id)
    table.add_row("Name", user.display_name)
    if user.mail:
        table.add_row("Email", user.mail)
    if user.user_principal_name:
        table.add_row("UPN", user.user_principal_name)
    if user.job_title:
        table.add_row("Job Title", user.job_title)

    console.print(table)
