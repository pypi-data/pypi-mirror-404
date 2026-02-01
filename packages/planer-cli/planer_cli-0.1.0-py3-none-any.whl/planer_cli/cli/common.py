"""Common CLI utilities."""

import asyncio
import sys
from functools import wraps
from typing import Any, Callable, TypeVar

import click
from rich.console import Console

from planer_cli.api.client import GraphClient
from planer_cli.api.exceptions import (
    AuthenticationError,
    ETagMismatchError,
    PermissionDeniedError,
    PlannerAPIError,
    RateLimitError,
    ResourceNotFoundError,
)
from planer_cli.auth.manager import AuthManager
from planer_cli.auth.manager import AuthenticationError as AuthManagerError

console = Console(stderr=True)

F = TypeVar("F", bound=Callable[..., Any])


def async_command(f: F) -> F:
    """Decorator to run async click commands.

    Args:
        f: Async function to wrap.

    Returns:
        Wrapped function.
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(f(*args, **kwargs))

    return wrapper  # type: ignore


def handle_api_errors(f: F) -> F:
    """Decorator to handle API errors gracefully.

    Args:
        f: Function to wrap.

    Returns:
        Wrapped function.
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except (AuthenticationError, AuthManagerError) as e:
            console.print(f"[red]Authentication error:[/red] {e}")
            console.print("Run [cyan]planer login[/cyan] to authenticate.")
            sys.exit(1)
        except ResourceNotFoundError as e:
            console.print(f"[red]Not found:[/red] {e}")
            sys.exit(1)
        except PermissionDeniedError as e:
            console.print(f"[red]Permission denied:[/red] {e}")
            sys.exit(1)
        except ETagMismatchError as e:
            console.print(f"[red]Conflict:[/red] {e}")
            console.print("The resource was modified. Please retry.")
            sys.exit(1)
        except RateLimitError as e:
            console.print(f"[yellow]Rate limited:[/yellow] {e}")
            console.print(f"Retry after {e.retry_after} seconds.")
            sys.exit(1)
        except PlannerAPIError as e:
            console.print(f"[red]API error:[/red] {e}")
            sys.exit(1)
        except ValueError as e:
            console.print(f"[red]Configuration error:[/red] {e}")
            sys.exit(1)

    return wrapper  # type: ignore


def get_client_and_api() -> tuple[GraphClient, "Any", "Any"]:
    """Get initialized client and API instances.

    Returns:
        Tuple of (GraphClient, PlannerAPI, GroupsAPI).
    """
    from planer_cli.api.groups import GroupsAPI
    from planer_cli.api.planner import PlannerAPI

    auth = AuthManager()
    client = GraphClient(auth)
    planner_api = PlannerAPI(client)
    groups_api = GroupsAPI(client)

    return client, planner_api, groups_api


class OutputFormat(click.ParamType):
    """Custom click type for output format."""

    name = "format"

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> str:
        if value in ("table", "json"):
            return value
        self.fail(f"Invalid format: {value}. Use 'table' or 'json'.", param, ctx)


output_format_type = OutputFormat()
