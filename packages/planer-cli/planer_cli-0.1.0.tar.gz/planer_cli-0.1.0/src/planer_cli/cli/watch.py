"""Watch mode for task changes."""

import asyncio
import platform
import subprocess
import sys
from datetime import datetime

import click

from planer_cli.cli.common import get_client_and_api
from planer_cli.config.settings import get_settings


def send_notification(title: str, message: str) -> None:
    """Send a desktop notification.

    Args:
        title: Notification title.
        message: Notification message.
    """
    system = platform.system()

    try:
        if system == "Darwin":
            # macOS - use osascript
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                check=False,
            )
        elif system == "Linux":
            # Linux - use notify-send
            subprocess.run(
                ["notify-send", title, message],
                capture_output=True,
                check=False,
            )
        # Windows not supported yet
    except Exception:
        pass  # Silently ignore notification errors


def format_task_change(change_type: str, task) -> str:
    """Format a task change for display.

    Args:
        change_type: Type of change (new, updated, completed, assigned).
        task: Task object.

    Returns:
        Formatted string.
    """
    due = ""
    if task.due_date_time:
        due = f" (due: {task.due_date_time.strftime('%Y-%m-%d')})"

    icons = {
        "new": "+",
        "updated": "~",
        "completed": "x",
        "assigned": "@",
    }
    icon = icons.get(change_type, "?")

    return f"[{icon}] {task.title}{due}"


def detect_changes(old_tasks: dict, new_tasks: dict) -> list[tuple[str, object]]:
    """Detect changes between two task snapshots.

    Args:
        old_tasks: Dict of task_id -> task from previous poll.
        new_tasks: Dict of task_id -> task from current poll.

    Returns:
        List of (change_type, task) tuples.
    """
    changes = []

    # New tasks
    for task_id, task in new_tasks.items():
        if task_id not in old_tasks:
            changes.append(("new", task))

    # Updated/completed tasks
    for task_id, new_task in new_tasks.items():
        if task_id in old_tasks:
            old_task = old_tasks[task_id]

            # Check for completion
            if old_task.percent_complete < 100 and new_task.percent_complete == 100:
                changes.append(("completed", new_task))
            # Check for other updates (title, due date, priority, etc.)
            elif (
                old_task.title != new_task.title
                or old_task.due_date_time != new_task.due_date_time
                or old_task.priority != new_task.priority
                or old_task.percent_complete != new_task.percent_complete
            ):
                changes.append(("updated", new_task))

    return changes


async def watch_loop(interval: int, notify: bool) -> None:
    """Main watch loop.

    Args:
        interval: Polling interval in seconds.
        notify: Whether to send desktop notifications.
    """
    client, planner_api, _ = get_client_and_api()
    previous_tasks: dict = {}
    first_run = True

    click.echo(f"Watching for task changes (polling every {interval}s)...")
    click.echo("Press Ctrl+C to stop.\n")

    try:
        while True:
            try:
                # Fetch current tasks
                task_list = await planner_api.list_my_tasks()
                current_tasks = {t.id: t for t in task_list}

                if first_run:
                    click.echo(f"Monitoring {len(current_tasks)} tasks.")
                    previous_tasks = current_tasks
                    first_run = False
                else:
                    # Detect changes
                    changes = detect_changes(previous_tasks, current_tasks)

                    if changes:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        click.echo(f"\n[{timestamp}] {len(changes)} change(s):")

                        for change_type, task in changes:
                            msg = format_task_change(change_type, task)
                            click.echo(f"  {msg}")

                            # Send notification
                            if notify:
                                titles = {
                                    "new": "New Task",
                                    "updated": "Task Updated",
                                    "completed": "Task Completed",
                                    "assigned": "Task Assigned",
                                }
                                send_notification(
                                    titles.get(change_type, "Task Change"),
                                    task.title,
                                )

                    previous_tasks = current_tasks

                # Wait for next poll
                await asyncio.sleep(interval)

            except Exception as e:
                click.echo(f"Error: {e}", err=True)
                await asyncio.sleep(interval)

    except asyncio.CancelledError:
        pass
    finally:
        await client.close()


@click.command("watch")
@click.option(
    "--interval", "-i",
    type=int,
    default=None,
    help="Polling interval in seconds.",
)
@click.option(
    "--no-notify", "-n",
    is_flag=True,
    help="Disable desktop notifications.",
)
def watch(interval: int | None, no_notify: bool) -> None:
    """Watch for task changes with notifications.

    Monitors your tasks for changes and shows desktop notifications
    when tasks are added, updated, or completed.
    """
    settings = get_settings()

    # Use config setting if not specified
    if interval is None:
        interval = settings.watch_interval

    if interval < 10:
        click.echo("Error: Interval must be at least 10 seconds.")
        sys.exit(1)

    notify = not no_notify

    try:
        asyncio.run(watch_loop(interval, notify))
    except KeyboardInterrupt:
        click.echo("\nWatch stopped.")
