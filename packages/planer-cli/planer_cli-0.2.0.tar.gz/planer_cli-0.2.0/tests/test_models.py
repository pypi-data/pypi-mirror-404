"""Tests for Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from planer_cli.models.bucket import Bucket
from planer_cli.models.plan import Plan, PlanDetails
from planer_cli.models.task import Task, TaskDetails


class TestTaskModel:
    """Tests for Task model."""

    def test_task_from_api_data(self, sample_task_data: dict) -> None:
        """Test creating Task from API response data.

        Args:
            sample_task_data: Sample task data fixture.
        """
        task = Task.model_validate(sample_task_data)

        assert task.id == "task-123"
        assert task.plan_id == "plan-456"
        assert task.bucket_id == "bucket-789"
        assert task.title == "Test Task"
        assert task.percent_complete == 0
        assert task.priority == 5
        assert task.etag == 'W/"JzEtVGFzayAgQEBAQEBAQEBAQEBAQEBARCc="'

    def test_task_with_snake_case_fields(self) -> None:
        """Test Task accepts both snake_case and camelCase field names."""
        data = {
            "id": "task-123",
            "plan_id": "plan-456",
            "title": "Test",
            "percent_complete": 50,
        }
        task = Task.model_validate(data)

        assert task.id == "task-123"
        assert task.plan_id == "plan-456"
        assert task.percent_complete == 50

    def test_task_datetime_parsing(self, sample_task_data: dict) -> None:
        """Test datetime fields are parsed correctly.

        Args:
            sample_task_data: Sample task data fixture.
        """
        task = Task.model_validate(sample_task_data)

        assert isinstance(task.start_date_time, datetime)
        assert isinstance(task.due_date_time, datetime)
        assert task.completed_date_time is None

    def test_task_is_completed_property(self) -> None:
        """Test is_completed property returns correct value."""
        task_open = Task(id="1", planId="p1", title="Open", percentComplete=50)
        task_done = Task(id="2", planId="p1", title="Done", percentComplete=100)

        assert not task_open.is_completed
        assert task_done.is_completed

    def test_task_priority_label_property(self) -> None:
        """Test priority_label property returns human-readable labels."""
        task_urgent = Task(id="1", planId="p1", title="Urgent", priority=0)
        task_important = Task(id="2", planId="p1", title="Important", priority=1)
        task_normal = Task(id="3", planId="p1", title="Normal", priority=5)
        task_low = Task(id="4", planId="p1", title="Low", priority=9)

        assert task_urgent.priority_label == "Urgent"
        assert task_important.priority_label == "Important"
        assert task_normal.priority_label == "Normal"
        assert task_low.priority_label == "Low"

    def test_task_priority_label_unknown(self) -> None:
        """Test priority_label returns 'Normal' for unknown priority values."""
        task = Task(id="1", planId="p1", title="Test", priority=99)

        assert task.priority_label == "Normal"

    def test_task_missing_required_fields(self) -> None:
        """Test Task validation fails when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            Task.model_validate({"id": "1"})

        errors = exc_info.value.errors()
        field_names = {error["loc"][0] for error in errors}
        assert "planId" in field_names
        assert "title" in field_names

    def test_task_optional_fields(self) -> None:
        """Test Task with only required fields."""
        task = Task(id="task-1", planId="plan-1", title="Minimal Task")

        assert task.bucket_id is None
        assert task.percent_complete == 0
        assert task.priority == 5
        assert task.start_date_time is None
        assert task.due_date_time is None
        assert task.completed_date_time is None
        assert task.assignments is None
        assert task.etag is None


class TestTaskDetailsModel:
    """Tests for TaskDetails model."""

    def test_task_details_from_api_data(self) -> None:
        """Test creating TaskDetails from API response data."""
        data = {
            "id": "task-123",
            "description": "Test description",
            "checklist": {},
            "references": {},
            "@odata.etag": 'W/"etag-value"',
        }
        details = TaskDetails.model_validate(data)

        assert details.id == "task-123"
        assert details.description == "Test description"
        assert details.etag == 'W/"etag-value"'

    def test_task_details_optional_fields(self) -> None:
        """Test TaskDetails with only required fields."""
        details = TaskDetails(id="task-1")

        assert details.id == "task-1"
        assert details.description is None
        assert details.checklist is None
        assert details.references is None
        assert details.etag is None


class TestPlanModel:
    """Tests for Plan model."""

    def test_plan_from_api_data(self, sample_plan_data: dict) -> None:
        """Test creating Plan from API response data.

        Args:
            sample_plan_data: Sample plan data fixture.
        """
        plan = Plan.model_validate(sample_plan_data)

        assert plan.id == "plan-456"
        assert plan.title == "Test Plan"
        assert plan.owner == "group-123"
        assert isinstance(plan.created_date_time, datetime)
        assert plan.etag == 'W/"JzEtUGxhbiAgQEBAQEBAQEBAQEBAQEBARCc="'

    def test_plan_with_snake_case_fields(self) -> None:
        """Test Plan accepts both snake_case and camelCase field names."""
        data = {
            "id": "plan-1",
            "title": "Test Plan",
            "owner": "group-1",
            "created_date_time": "2024-01-01T00:00:00Z",
        }
        plan = Plan.model_validate(data)

        assert plan.id == "plan-1"
        assert plan.owner == "group-1"

    def test_plan_missing_required_fields(self) -> None:
        """Test Plan validation fails when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            Plan.model_validate({"id": "1"})

        errors = exc_info.value.errors()
        field_names = {error["loc"][0] for error in errors}
        assert "title" in field_names
        assert "owner" in field_names

    def test_plan_optional_fields(self) -> None:
        """Test Plan with only required fields."""
        plan = Plan(id="plan-1", title="Test Plan", owner="group-1")

        assert plan.created_date_time is None
        assert plan.etag is None


class TestPlanDetailsModel:
    """Tests for PlanDetails model."""

    def test_plan_details_from_api_data(self) -> None:
        """Test creating PlanDetails from API response data."""
        data = {
            "id": "plan-123",
            "sharedWith": {"user-1": True},
            "categoryDescriptions": {"category1": "Description"},
            "@odata.etag": 'W/"etag-value"',
        }
        details = PlanDetails.model_validate(data)

        assert details.id == "plan-123"
        assert details.shared_with == {"user-1": True}
        assert details.category_descriptions == {"category1": "Description"}
        assert details.etag == 'W/"etag-value"'

    def test_plan_details_optional_fields(self) -> None:
        """Test PlanDetails with only required fields."""
        details = PlanDetails(id="plan-1")

        assert details.id == "plan-1"
        assert details.shared_with is None
        assert details.category_descriptions is None
        assert details.etag is None


class TestBucketModel:
    """Tests for Bucket model."""

    def test_bucket_from_api_data(self, sample_bucket_data: dict) -> None:
        """Test creating Bucket from API response data.

        Args:
            sample_bucket_data: Sample bucket data fixture.
        """
        bucket = Bucket.model_validate(sample_bucket_data)

        assert bucket.id == "bucket-789"
        assert bucket.plan_id == "plan-456"
        assert bucket.name == "Test Bucket"
        assert bucket.order_hint == "8585269235419339237"
        assert bucket.etag == 'W/"JzEtQnVja2V0QEBAQEBAQEBAQEBAQEBARCc="'

    def test_bucket_with_snake_case_fields(self) -> None:
        """Test Bucket accepts both snake_case and camelCase field names."""
        data = {
            "id": "bucket-1",
            "plan_id": "plan-1",
            "name": "Test Bucket",
        }
        bucket = Bucket.model_validate(data)

        assert bucket.id == "bucket-1"
        assert bucket.plan_id == "plan-1"

    def test_bucket_missing_required_fields(self) -> None:
        """Test Bucket validation fails when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            Bucket.model_validate({"id": "1"})

        errors = exc_info.value.errors()
        field_names = {error["loc"][0] for error in errors}
        assert "planId" in field_names
        assert "name" in field_names

    def test_bucket_optional_fields(self) -> None:
        """Test Bucket with only required fields."""
        bucket = Bucket(id="bucket-1", planId="plan-1", name="Test Bucket")

        assert bucket.order_hint is None
        assert bucket.etag is None


class TestModelSerialization:
    """Tests for model serialization and deserialization."""

    def test_task_model_dump(self, sample_task: Task) -> None:
        """Test Task can be dumped back to dictionary.

        Args:
            sample_task: Sample Task fixture.
        """
        data = sample_task.model_dump(by_alias=True)

        assert data["id"] == "task-123"
        assert data["planId"] == "plan-456"
        assert data["bucketId"] == "bucket-789"
        assert data["title"] == "Test Task"
        assert data["percentComplete"] == 0

    def test_plan_model_dump(self, sample_plan: Plan) -> None:
        """Test Plan can be dumped back to dictionary.

        Args:
            sample_plan: Sample Plan fixture.
        """
        data = sample_plan.model_dump(by_alias=True)

        assert data["id"] == "plan-456"
        assert data["title"] == "Test Plan"
        assert data["owner"] == "group-123"

    def test_bucket_model_dump(self, sample_bucket: Bucket) -> None:
        """Test Bucket can be dumped back to dictionary.

        Args:
            sample_bucket: Sample Bucket fixture.
        """
        data = sample_bucket.model_dump(by_alias=True)

        assert data["id"] == "bucket-789"
        assert data["planId"] == "plan-456"
        assert data["name"] == "Test Bucket"
