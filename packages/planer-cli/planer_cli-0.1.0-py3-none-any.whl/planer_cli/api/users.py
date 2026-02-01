"""Users API operations."""

from planer_cli.api.client import GraphClient
from planer_cli.models.user import User


class UsersAPI:
    """API for User operations."""

    def __init__(self, client: GraphClient) -> None:
        """Initialize the API.

        Args:
            client: GraphClient instance.
        """
        self.client = client

    async def get_me(self) -> User:
        """Get current user.

        Returns:
            Current user.
        """
        response = await self.client.get("/me")
        return User.model_validate(response)

    async def list_users(self, search: str | None = None) -> list[User]:
        """List users in the organization.

        Args:
            search: Optional search term for display name or mail.

        Returns:
            List of users.
        """
        if search:
            # Search by displayName or mail (no orderby with filter)
            query = (
                f"/users?$filter=startswith(displayName,'{search}') "
                f"or startswith(mail,'{search}')"
                f"&$top=999"
            )
        else:
            query = "/users?$top=999&$orderby=displayName"

        response = await self.client.get(query)
        users = [User.model_validate(u) for u in response.get("value", [])]
        # Sort locally when using filter
        if search:
            users.sort(key=lambda u: u.display_name.lower())
        return users

    async def get_user(self, user_id: str) -> User:
        """Get a user by ID.

        Args:
            user_id: The user ID or userPrincipalName.

        Returns:
            User object.
        """
        response = await self.client.get(f"/users/{user_id}")
        return User.model_validate(response)
