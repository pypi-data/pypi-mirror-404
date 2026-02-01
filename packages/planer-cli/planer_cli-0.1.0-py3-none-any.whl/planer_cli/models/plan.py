"""Planner Plan models."""

from datetime import datetime

from pydantic import BaseModel, Field


class Plan(BaseModel):
    """Planner Plan."""

    id: str
    title: str
    owner: str  # Group ID
    created_date_time: datetime | None = Field(default=None, alias="createdDateTime")
    etag: str | None = Field(default=None, alias="@odata.etag")

    model_config = {"populate_by_name": True}


class PlanDetails(BaseModel):
    """Planner Plan details."""

    id: str = Field(alias="id")
    shared_with: dict | None = Field(default=None, alias="sharedWith")
    category_descriptions: dict | None = Field(
        default=None, alias="categoryDescriptions"
    )
    etag: str | None = Field(default=None, alias="@odata.etag")

    model_config = {"populate_by_name": True}
