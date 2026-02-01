"""Planner Task models."""

from datetime import datetime

from pydantic import BaseModel, Field


class Task(BaseModel):
    """Planner Task."""

    id: str
    plan_id: str = Field(alias="planId")
    bucket_id: str | None = Field(default=None, alias="bucketId")
    title: str
    percent_complete: int = Field(default=0, alias="percentComplete")
    priority: int = 5  # 0=urgent, 1=important, 5=normal, 9=low
    start_date_time: datetime | None = Field(default=None, alias="startDateTime")
    due_date_time: datetime | None = Field(default=None, alias="dueDateTime")
    completed_date_time: datetime | None = Field(
        default=None, alias="completedDateTime"
    )
    assignments: dict | None = None
    applied_categories: dict | None = Field(default=None, alias="appliedCategories")
    etag: str | None = Field(default=None, alias="@odata.etag")

    model_config = {"populate_by_name": True}

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.percent_complete == 100

    @property
    def priority_label(self) -> str:
        """Get human-readable priority label."""
        labels = {0: "Urgent", 1: "Important", 5: "Normal", 9: "Low"}
        return labels.get(self.priority, "Normal")

    @property
    def category_keys(self) -> list[str]:
        """Get list of applied category keys (category1, category2, etc.)."""
        if not self.applied_categories:
            return []
        return [k for k, v in self.applied_categories.items() if v]


class TaskDetails(BaseModel):
    """Planner Task details."""

    id: str = Field(alias="id")
    description: str | None = None
    checklist: dict | None = None
    references: dict | None = None
    etag: str | None = Field(default=None, alias="@odata.etag")

    model_config = {"populate_by_name": True}
