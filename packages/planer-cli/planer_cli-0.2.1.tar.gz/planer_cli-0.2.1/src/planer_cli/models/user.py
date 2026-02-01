"""User models."""

from pydantic import BaseModel, Field


class User(BaseModel):
    """Microsoft Graph User."""

    id: str
    display_name: str = Field(alias="displayName")
    mail: str | None = None
    user_principal_name: str | None = Field(default=None, alias="userPrincipalName")
    job_title: str | None = Field(default=None, alias="jobTitle")

    model_config = {"populate_by_name": True}
