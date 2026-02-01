"""Planner Bucket model."""

from pydantic import BaseModel, Field


class Bucket(BaseModel):
    """Planner Bucket."""

    id: str
    plan_id: str = Field(alias="planId")
    name: str
    order_hint: str | None = Field(default=None, alias="orderHint")
    etag: str | None = Field(default=None, alias="@odata.etag")

    model_config = {"populate_by_name": True}
