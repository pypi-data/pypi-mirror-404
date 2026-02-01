"""Tests for PlannerAPI with mocked HTTP responses."""

import pytest
import respx
from httpx import Response

from planer_cli.api.exceptions import (
    AuthenticationError,
    ETagMismatchError,
    PermissionDeniedError,
    PlannerAPIError,
    RateLimitError,
    ResourceNotFoundError,
)
from planer_cli.api.planner import PlannerAPI
from planer_cli.models.bucket import Bucket
from planer_cli.models.plan import Plan
from planer_cli.models.task import Task


class TestPlannerAPITasks:
    """Tests for PlannerAPI task operations."""

    @pytest.mark.asyncio
    async def test_list_my_tasks(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_task_data: dict,
    ) -> None:
        """Test listing tasks assigned to current user.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_task_data: Sample task data fixture.
        """
        respx_mock.get("/me/planner/tasks").mock(
            return_value=Response(200, json={"value": [sample_task_data]})
        )

        tasks = await planner_api.list_my_tasks()

        assert len(tasks) == 1
        assert isinstance(tasks[0], Task)
        assert tasks[0].id == "task-123"
        assert tasks[0].title == "Test Task"

    @pytest.mark.asyncio
    async def test_list_my_tasks_empty(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test listing my tasks when no tasks exist.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.get("/me/planner/tasks").mock(
            return_value=Response(200, json={"value": []})
        )

        tasks = await planner_api.list_my_tasks()

        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_list_tasks(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_task_data: dict,
    ) -> None:
        """Test listing tasks in a plan.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_task_data: Sample task data fixture.
        """
        respx_mock.get("/planner/plans/plan-456/tasks").mock(
            return_value=Response(200, json={"value": [sample_task_data]})
        )

        tasks = await planner_api.list_tasks("plan-456")

        assert len(tasks) == 1
        assert tasks[0].plan_id == "plan-456"

    @pytest.mark.asyncio
    async def test_list_bucket_tasks(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_task_data: dict,
    ) -> None:
        """Test listing tasks in a bucket.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_task_data: Sample task data fixture.
        """
        respx_mock.get("/planner/buckets/bucket-789/tasks").mock(
            return_value=Response(200, json={"value": [sample_task_data]})
        )

        tasks = await planner_api.list_bucket_tasks("bucket-789")

        assert len(tasks) == 1
        assert tasks[0].bucket_id == "bucket-789"

    @pytest.mark.asyncio
    async def test_get_task(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_task_data: dict,
    ) -> None:
        """Test getting a task by ID.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_task_data: Sample task data fixture.
        """
        respx_mock.get("/planner/tasks/task-123").mock(
            return_value=Response(200, json=sample_task_data)
        )

        task = await planner_api.get_task("task-123")

        assert isinstance(task, Task)
        assert task.id == "task-123"
        assert task.title == "Test Task"

    @pytest.mark.asyncio
    async def test_create_task_minimal(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_task_data: dict,
    ) -> None:
        """Test creating a task with minimal fields.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_task_data: Sample task data fixture.
        """
        respx_mock.post("/planner/tasks").mock(
            return_value=Response(201, json=sample_task_data)
        )

        task = await planner_api.create_task(plan_id="plan-456", title="Test Task")

        assert isinstance(task, Task)
        assert task.title == "Test Task"
        assert task.plan_id == "plan-456"

    @pytest.mark.asyncio
    async def test_create_task_with_all_fields(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_task_data: dict,
    ) -> None:
        """Test creating a task with all optional fields.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_task_data: Sample task data fixture.
        """
        respx_mock.post("/planner/tasks").mock(
            return_value=Response(201, json=sample_task_data)
        )

        task = await planner_api.create_task(
            plan_id="plan-456",
            title="Test Task",
            bucket_id="bucket-789",
            due_date="2024-01-20T00:00:00Z",
            priority=1,
        )

        assert isinstance(task, Task)
        assert task.title == "Test Task"

    @pytest.mark.asyncio
    async def test_update_task(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_task_data: dict,
    ) -> None:
        """Test updating a task.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_task_data: Sample task data fixture.
        """
        updated_data = sample_task_data.copy()
        updated_data["title"] = "Updated Task"

        respx_mock.patch("/planner/tasks/task-123").mock(
            return_value=Response(200, json=updated_data)
        )

        task = await planner_api.update_task(
            task_id="task-123",
            data={"title": "Updated Task"},
            etag='W/"etag-value"',
        )

        assert task.title == "Updated Task"

    @pytest.mark.asyncio
    async def test_complete_task(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_task_data: dict,
    ) -> None:
        """Test marking a task as complete.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_task_data: Sample task data fixture.
        """
        completed_data = sample_task_data.copy()
        completed_data["percentComplete"] = 100

        respx_mock.patch("/planner/tasks/task-123").mock(
            return_value=Response(200, json=completed_data)
        )

        task = await planner_api.complete_task(
            task_id="task-123", etag='W/"etag-value"'
        )

        assert task.percent_complete == 100

    @pytest.mark.asyncio
    async def test_delete_task(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test deleting a task.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.delete("/planner/tasks/task-123").mock(
            return_value=Response(204)
        )

        result = await planner_api.delete_task(
            task_id="task-123", etag='W/"etag-value"'
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_assign_task(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_task_data: dict,
    ) -> None:
        """Test assigning a task to a user.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_task_data: Sample task data fixture.
        """
        assigned_data = sample_task_data.copy()
        assigned_data["assignments"] = {"user-123": {}}

        respx_mock.patch("/planner/tasks/task-123").mock(
            return_value=Response(200, json=assigned_data)
        )

        task = await planner_api.assign_task(
            task_id="task-123", user_id="user-123", etag='W/"etag-value"'
        )

        assert "user-123" in task.assignments


class TestPlannerAPIPlans:
    """Tests for PlannerAPI plan operations."""

    @pytest.mark.asyncio
    async def test_list_my_plans(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_plan_data: dict,
        sample_task_data: dict,
    ) -> None:
        """Test listing plans the current user has tasks in.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_plan_data: Sample plan data fixture.
            sample_task_data: Sample task data fixture.
        """
        respx_mock.get("/me/planner/tasks?$select=planId").mock(
            return_value=Response(200, json={"value": [{"planId": "plan-456"}]})
        )
        respx_mock.get("/planner/plans/plan-456").mock(
            return_value=Response(200, json=sample_plan_data)
        )

        plans = await planner_api.list_my_plans()

        assert len(plans) == 1
        assert plans[0].id == "plan-456"

    @pytest.mark.asyncio
    async def test_list_plans(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_plan_data: dict,
    ) -> None:
        """Test listing plans in a group.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_plan_data: Sample plan data fixture.
        """
        respx_mock.get("/groups/group-123/planner/plans").mock(
            return_value=Response(200, json={"value": [sample_plan_data]})
        )

        plans = await planner_api.list_plans("group-123")

        assert len(plans) == 1
        assert plans[0].owner == "group-123"

    @pytest.mark.asyncio
    async def test_get_plan(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_plan_data: dict,
    ) -> None:
        """Test getting a plan by ID.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_plan_data: Sample plan data fixture.
        """
        respx_mock.get("/planner/plans/plan-456").mock(
            return_value=Response(200, json=sample_plan_data)
        )

        plan = await planner_api.get_plan("plan-456")

        assert isinstance(plan, Plan)
        assert plan.id == "plan-456"
        assert plan.title == "Test Plan"

    @pytest.mark.asyncio
    async def test_create_plan(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_plan_data: dict,
    ) -> None:
        """Test creating a new plan.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_plan_data: Sample plan data fixture.
        """
        respx_mock.post("/planner/plans").mock(
            return_value=Response(201, json=sample_plan_data)
        )

        plan = await planner_api.create_plan(group_id="group-123", title="Test Plan")

        assert isinstance(plan, Plan)
        assert plan.title == "Test Plan"

    @pytest.mark.asyncio
    async def test_update_plan(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_plan_data: dict,
    ) -> None:
        """Test updating a plan.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_plan_data: Sample plan data fixture.
        """
        updated_data = sample_plan_data.copy()
        updated_data["title"] = "Updated Plan"

        respx_mock.patch("/planner/plans/plan-456").mock(
            return_value=Response(200, json=updated_data)
        )

        plan = await planner_api.update_plan(
            plan_id="plan-456",
            data={"title": "Updated Plan"},
            etag='W/"etag-value"',
        )

        assert plan.title == "Updated Plan"

    @pytest.mark.asyncio
    async def test_delete_plan(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test deleting a plan.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.delete("/planner/plans/plan-456").mock(
            return_value=Response(204)
        )

        result = await planner_api.delete_plan(
            plan_id="plan-456", etag='W/"etag-value"'
        )

        assert result is True


class TestPlannerAPIBuckets:
    """Tests for PlannerAPI bucket operations."""

    @pytest.mark.asyncio
    async def test_list_buckets(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_bucket_data: dict,
    ) -> None:
        """Test listing buckets in a plan.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_bucket_data: Sample bucket data fixture.
        """
        respx_mock.get("/planner/plans/plan-456/buckets").mock(
            return_value=Response(200, json={"value": [sample_bucket_data]})
        )

        buckets = await planner_api.list_buckets("plan-456")

        assert len(buckets) == 1
        assert isinstance(buckets[0], Bucket)
        assert buckets[0].plan_id == "plan-456"

    @pytest.mark.asyncio
    async def test_get_bucket(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_bucket_data: dict,
    ) -> None:
        """Test getting a bucket by ID.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_bucket_data: Sample bucket data fixture.
        """
        respx_mock.get("/planner/buckets/bucket-789").mock(
            return_value=Response(200, json=sample_bucket_data)
        )

        bucket = await planner_api.get_bucket("bucket-789")

        assert isinstance(bucket, Bucket)
        assert bucket.id == "bucket-789"
        assert bucket.name == "Test Bucket"

    @pytest.mark.asyncio
    async def test_create_bucket(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_bucket_data: dict,
    ) -> None:
        """Test creating a new bucket.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_bucket_data: Sample bucket data fixture.
        """
        respx_mock.post("/planner/buckets").mock(
            return_value=Response(201, json=sample_bucket_data)
        )

        bucket = await planner_api.create_bucket(
            plan_id="plan-456", name="Test Bucket"
        )

        assert isinstance(bucket, Bucket)
        assert bucket.name == "Test Bucket"

    @pytest.mark.asyncio
    async def test_update_bucket(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
        sample_bucket_data: dict,
    ) -> None:
        """Test updating a bucket.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
            sample_bucket_data: Sample bucket data fixture.
        """
        updated_data = sample_bucket_data.copy()
        updated_data["name"] = "Updated Bucket"

        respx_mock.patch("/planner/buckets/bucket-789").mock(
            return_value=Response(200, json=updated_data)
        )

        bucket = await planner_api.update_bucket(
            bucket_id="bucket-789",
            data={"name": "Updated Bucket"},
            etag='W/"etag-value"',
        )

        assert bucket.name == "Updated Bucket"

    @pytest.mark.asyncio
    async def test_delete_bucket(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test deleting a bucket.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.delete("/planner/buckets/bucket-789").mock(
            return_value=Response(204)
        )

        result = await planner_api.delete_bucket(
            bucket_id="bucket-789", etag='W/"etag-value"'
        )

        assert result is True


class TestPlannerAPIErrorHandling:
    """Tests for PlannerAPI error handling."""

    @pytest.mark.asyncio
    async def test_authentication_error(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test handling of authentication errors.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.get("/planner/tasks/task-123").mock(
            return_value=Response(
                401, json={"error": {"message": "Authentication failed"}}
            )
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await planner_api.get_task("task-123")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_permission_denied_error(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test handling of permission denied errors.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.get("/planner/tasks/task-123").mock(
            return_value=Response(
                403, json={"error": {"message": "Permission denied"}}
            )
        )

        with pytest.raises(PermissionDeniedError):
            await planner_api.get_task("task-123")

    @pytest.mark.asyncio
    async def test_resource_not_found_error(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test handling of resource not found errors.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.get("/planner/tasks/task-123").mock(
            return_value=Response(
                404, json={"error": {"message": "Task not found"}}
            )
        )

        with pytest.raises(ResourceNotFoundError):
            await planner_api.get_task("task-123")

    @pytest.mark.asyncio
    async def test_etag_mismatch_error(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test handling of ETag mismatch errors.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.patch("/planner/tasks/task-123").mock(
            return_value=Response(
                409, json={"error": {"message": "ETag mismatch"}}
            )
        )

        with pytest.raises(ETagMismatchError):
            await planner_api.update_task(
                task_id="task-123",
                data={"title": "Updated"},
                etag='W/"old-etag"',
            )

    @pytest.mark.asyncio
    async def test_rate_limit_error(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test handling of rate limit errors.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.get("/planner/tasks/task-123").mock(
            return_value=Response(
                429,
                json={"error": {"message": "Rate limited"}},
                headers={"Retry-After": "60"},
            )
        )

        with pytest.raises(RateLimitError) as exc_info:
            await planner_api.get_task("task-123")

        assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_generic_api_error(
        self,
        planner_api: PlannerAPI,
        respx_mock: respx.MockRouter,
    ) -> None:
        """Test handling of generic API errors.

        Args:
            planner_api: PlannerAPI fixture.
            respx_mock: Respx mock router fixture.
        """
        respx_mock.get("/planner/tasks/task-123").mock(
            return_value=Response(
                500, json={"error": {"message": "Internal server error"}}
            )
        )

        with pytest.raises(PlannerAPIError) as exc_info:
            await planner_api.get_task("task-123")

        assert exc_info.value.status_code == 500
