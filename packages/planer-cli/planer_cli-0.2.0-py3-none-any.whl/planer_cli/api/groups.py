"""Microsoft 365 Groups API operations."""

from planer_cli.api.client import GraphClient
from planer_cli.models.group import Group


class GroupsAPI:
    """API for Microsoft 365 Groups operations."""

    def __init__(self, client: GraphClient) -> None:
        """Initialize the API.

        Args:
            client: GraphClient instance.
        """
        self.client = client

    async def list_my_groups(self) -> list[Group]:
        """List Microsoft 365 groups the current user is a member of.

        Returns:
            List of groups.
        """
        # Filter for Microsoft 365 groups (unified groups) only
        # These are the groups that can have Planner plans
        response = await self.client.get(
            "/me/memberOf/microsoft.graph.group"
            "?$filter=groupTypes/any(g:g eq 'Unified')"
            "&$select=id,displayName,description,mail"
            "&$top=999"
        )

        groups = []
        for item in response.get("value", []):
            groups.append(Group.model_validate(item))

        # Sort locally (orderby not supported with filter)
        return sorted(groups, key=lambda g: g.display_name.lower())

    async def get_group(self, group_id: str) -> Group:
        """Get a group by ID.

        Args:
            group_id: The group ID.

        Returns:
            Group object.
        """
        response = await self.client.get(
            f"/groups/{group_id}?$select=id,displayName,description,mail"
        )
        return Group.model_validate(response)
