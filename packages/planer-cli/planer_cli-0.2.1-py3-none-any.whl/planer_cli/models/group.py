"""Microsoft 365 Group model."""

from pydantic import BaseModel, Field


class Group(BaseModel):
    """Microsoft 365 Group."""

    id: str
    display_name: str = Field(alias="displayName")
    description: str | None = None
    mail: str | None = None

    model_config = {"populate_by_name": True}
