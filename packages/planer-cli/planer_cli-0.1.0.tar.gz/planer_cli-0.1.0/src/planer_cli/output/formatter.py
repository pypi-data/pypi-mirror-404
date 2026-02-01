"""Output formatting utilities."""

import csv
import json
from pathlib import Path
from typing import Any

from rich.console import Console

from planer_cli.config import get_settings

console = Console()
error_console = Console(stderr=True)


def output_data(
    data: Any,
    format_override: str | None = None,
) -> None:
    """Output data in the configured format.

    Args:
        data: Data to output (Pydantic model, list, or dict).
        format_override: Override the default format.
    """
    settings = get_settings()
    output_format = format_override or settings.output_format

    if output_format == "json":
        output_json(data)
    else:
        # Table format is handled by specific table functions
        # This is a fallback for simple data
        if hasattr(data, "model_dump"):
            console.print_json(data=data.model_dump(mode="json", by_alias=True))
        elif isinstance(data, list) and data and hasattr(data[0], "model_dump"):
            console.print_json(
                data=[item.model_dump(mode="json", by_alias=True) for item in data]
            )
        else:
            console.print(data)


def output_json(data: Any) -> None:
    """Output data as JSON.

    Args:
        data: Data to output.
    """
    if hasattr(data, "model_dump"):
        print(json.dumps(data.model_dump(mode="json", by_alias=True), indent=2))
    elif isinstance(data, list) and data and hasattr(data[0], "model_dump"):
        items = [item.model_dump(mode="json", by_alias=True) for item in data]
        print(json.dumps(items, indent=2))
    elif isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(json.dumps(str(data)))


def output_error(message: str) -> None:
    """Output an error message.

    Args:
        message: Error message.
    """
    error_console.print(f"[red]Error:[/red] {message}")


def output_success(message: str) -> None:
    """Output a success message.

    Args:
        message: Success message.
    """
    console.print(f"[green]{message}[/green]")


def output_warning(message: str) -> None:
    """Output a warning message.

    Args:
        message: Warning message.
    """
    console.print(f"[yellow]Warning:[/yellow] {message}")


def export_to_csv(tasks: list[Any], filepath: str) -> None:
    """Export tasks to a CSV file.

    Args:
        tasks: List of Task objects to export.
        filepath: Path to the output CSV file.
    """
    path = Path(filepath)
    fieldnames = [
        "id", "title", "status", "priority", "due_date", "bucket_id", "plan_id"
    ]

    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for task in tasks:
            # Map percent_complete to status
            if task.percent_complete == 100:
                status = "completed"
            elif task.percent_complete > 0:
                status = "in_progress"
            else:
                status = "not_started"

            # Format due date
            due_date = ""
            if task.due_date_time:
                due_date = task.due_date_time.strftime("%Y-%m-%d")

            writer.writerow(
                {
                    "id": task.id,
                    "title": task.title,
                    "status": status,
                    "priority": task.priority_label.lower(),
                    "due_date": due_date,
                    "bucket_id": task.bucket_id or "",
                    "plan_id": task.plan_id,
                }
            )


def export_to_json_file(tasks: list[Any], filepath: str) -> None:
    """Export tasks to a JSON file.

    Args:
        tasks: List of Task objects to export.
        filepath: Path to the output JSON file.
    """
    path = Path(filepath)
    export_data = []

    for task in tasks:
        # Map percent_complete to status
        if task.percent_complete == 100:
            status = "completed"
        elif task.percent_complete > 0:
            status = "in_progress"
        else:
            status = "not_started"

        # Format due date
        due_date = None
        if task.due_date_time:
            due_date = task.due_date_time.strftime("%Y-%m-%d")

        export_data.append(
            {
                "id": task.id,
                "title": task.title,
                "status": status,
                "priority": task.priority_label.lower(),
                "due_date": due_date,
                "bucket_id": task.bucket_id,
                "plan_id": task.plan_id,
            }
        )

    with path.open("w", encoding="utf-8") as jsonfile:
        json.dump(export_data, jsonfile, indent=2)
