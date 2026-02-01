"""Authentication manager using MSAL Device Code Flow."""

from typing import Any

from msal import PublicClientApplication
from rich.console import Console
from rich.panel import Panel

from planer_cli.auth.cache import FileTokenCache
from planer_cli.config import get_settings


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class AuthManager:
    """Manages authentication using MSAL Device Code Flow."""

    def __init__(self) -> None:
        """Initialize the auth manager."""
        self.settings = get_settings()
        self.settings.validate_client_id()

        self._cache = FileTokenCache(self.settings.token_cache_file)
        self._app = PublicClientApplication(
            client_id=self.settings.client_id,
            authority=self.settings.full_authority,
            token_cache=self._cache,
        )
        self._console = Console()

    def _get_accounts(self) -> list[dict[str, Any]]:
        """Get accounts from cache."""
        return self._app.get_accounts()

    def _try_silent_auth(self) -> str | None:
        """Try to get token silently from cache.

        Returns:
            Access token if available, None otherwise.
        """
        accounts = self._get_accounts()
        if not accounts:
            return None

        result = self._app.acquire_token_silent(
            scopes=self.settings.scopes,
            account=accounts[0],
        )

        if result and "access_token" in result:
            self._cache.save()
            return result["access_token"]

        return None

    def authenticate(self) -> str:
        """Authenticate using device code flow.

        Displays a code for the user to enter at the Microsoft login page.

        Returns:
            Access token.

        Raises:
            AuthenticationError: If authentication fails.
        """
        # Try silent auth first
        token = self._try_silent_auth()
        if token:
            self._console.print("[green]Already authenticated.[/green]")
            return token

        # Initiate device code flow
        flow = self._app.initiate_device_flow(scopes=self.settings.scopes)

        if "user_code" not in flow:
            raise AuthenticationError(
                f"Failed to initiate device code flow: {flow.get('error_description', 'Unknown error')}"
            )

        # Display the device code to the user
        self._console.print(
            Panel(
                f"[bold]To sign in, visit:[/bold] [cyan]{flow['verification_uri']}[/cyan]\n\n"
                f"[bold]Enter code:[/bold] [yellow]{flow['user_code']}[/yellow]",
                title="Microsoft Authentication",
                border_style="blue",
            )
        )

        # Wait for user to complete authentication
        result = self._app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            error = result.get("error_description", result.get("error", "Unknown error"))
            raise AuthenticationError(f"Authentication failed: {error}")

        self._cache.save()
        self._console.print("[green]Authentication successful![/green]")

        return result["access_token"]

    def get_access_token(self) -> str:
        """Get access token, refreshing if necessary.

        Returns:
            Valid access token.

        Raises:
            AuthenticationError: If no valid token is available.
        """
        token = self._try_silent_auth()
        if token:
            return token

        raise AuthenticationError(
            "Not authenticated. Run 'planer login' to authenticate."
        )

    def logout(self) -> None:
        """Clear cached tokens."""
        self._cache.clear()
        self._console.print("[green]Logged out successfully.[/green]")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated.

        Returns:
            True if valid tokens exist in cache.
        """
        try:
            self._try_silent_auth()
            return len(self._get_accounts()) > 0
        except Exception:
            return False
