"""Planner API operations for plans, buckets, and tasks."""

from typing import Any

from planer_cli.api.client import GraphClient
from planer_cli.models.bucket import Bucket
from planer_cli.models.plan import Plan, PlanDetails
from planer_cli.models.task import Task, TaskDetails


class PlannerAPI:
    """API for Planner operations."""

    def __init__(self, client: GraphClient) -> None:
        """Initialize the API.

        Args:
            client: GraphClient instance.
        """
        self.client = client

    # ========== Plans ==========

    async def list_my_tasks(self) -> list[Task]:
        """List all tasks assigned to the current user.

        Returns:
            List of tasks.
        """
        response = await self.client.get("/me/planner/tasks")
        return [Task.model_validate(t) for t in response.get("value", [])]

    async def list_my_plans(self) -> list[Plan]:
        """List plans the current user has tasks in.

        Extracts unique plan IDs from user's tasks and fetches plan details.

        Returns:
            List of plans.
        """
        # Get all my tasks to extract plan IDs
        response = await self.client.get("/me/planner/tasks?$select=planId")
        plan_ids = set()
        for task in response.get("value", []):
            plan_ids.add(task["planId"])

        # Fetch each plan's details
        plans = []
        for plan_id in plan_ids:
            try:
                plan = await self.get_plan(plan_id)
                plans.append(plan)
            except Exception:
                # Skip plans we can't access
                pass

        return sorted(plans, key=lambda p: p.title.lower())

    async def list_all_my_plans(self) -> list[Plan]:
        """List all plans the user has access to.

        Combines plans from:
        - Groups the user is a member of
        - Plans where the user has tasks assigned

        Returns:
            List of all accessible plans.
        """
        seen_plan_ids: set[str] = set()
        plans = []

        # 1. Get plans from groups the user is a member of
        try:
            response = await self.client.get(
                "/me/memberOf/microsoft.graph.group"
                "?$filter=groupTypes/any(g:g eq 'Unified')"
                "&$select=id"
            )
            for group in response.get("value", []):
                group_id = group.get("id")
                if not group_id:
                    continue
                try:
                    group_plans = await self.list_plans(group_id)
                    for plan in group_plans:
                        if plan.id not in seen_plan_ids:
                            seen_plan_ids.add(plan.id)
                            plans.append(plan)
                except Exception:
                    pass
        except Exception:
            pass

        # 2. Get plans from user's assigned tasks
        try:
            response = await self.client.get("/me/planner/tasks?$select=planId")
            for task in response.get("value", []):
                plan_id = task.get("planId")
                if plan_id and plan_id not in seen_plan_ids:
                    try:
                        plan = await self.get_plan(plan_id)
                        seen_plan_ids.add(plan.id)
                        plans.append(plan)
                    except Exception:
                        pass
        except Exception:
            pass

        return sorted(plans, key=lambda p: p.title.lower())

    async def list_plans(self, group_id: str) -> list[Plan]:
        """List plans in a group.

        Args:
            group_id: The group ID.

        Returns:
            List of plans.
        """
        response = await self.client.get(f"/groups/{group_id}/planner/plans")
        return [Plan.model_validate(p) for p in response.get("value", [])]

    async def get_plan(self, plan_id: str) -> Plan:
        """Get a plan by ID.

        Args:
            plan_id: The plan ID.

        Returns:
            Plan object.
        """
        response = await self.client.get(f"/planner/plans/{plan_id}")
        return Plan.model_validate(response)

    async def create_plan(self, group_id: str, title: str) -> Plan:
        """Create a new plan.

        Args:
            group_id: The group ID (owner).
            title: Plan title.

        Returns:
            Created plan.
        """
        data = {"owner": group_id, "title": title}
        response = await self.client.post("/planner/plans", data)
        return Plan.model_validate(response)

    async def update_plan(
        self, plan_id: str, data: dict[str, Any], etag: str
    ) -> Plan:
        """Update a plan.

        Args:
            plan_id: The plan ID.
            data: Fields to update.
            etag: Current ETag for optimistic concurrency.

        Returns:
            Updated plan.
        """
        response = await self.client.patch(f"/planner/plans/{plan_id}", data, etag)
        return Plan.model_validate(response)

    async def delete_plan(self, plan_id: str, etag: str) -> bool:
        """Delete a plan.

        Args:
            plan_id: The plan ID.
            etag: Current ETag for optimistic concurrency.

        Returns:
            True if successful.
        """
        return await self.client.delete(f"/planner/plans/{plan_id}", etag)

    # ========== Plan Details ==========

    async def get_plan_details(self, plan_id: str) -> PlanDetails:
        """Get plan details (category descriptions, shared users).

        Args:
            plan_id: The plan ID.

        Returns:
            PlanDetails object.
        """
        response = await self.client.get(f"/planner/plans/{plan_id}/details")
        return PlanDetails.model_validate(response)

    async def update_plan_details(
        self, plan_id: str, data: dict[str, Any], etag: str
    ) -> PlanDetails:
        """Update plan details.

        Args:
            plan_id: The plan ID.
            data: Fields to update (categoryDescriptions, etc.).
            etag: Current ETag for optimistic concurrency.

        Returns:
            Updated PlanDetails object.
        """
        response = await self.client.patch(
            f"/planner/plans/{plan_id}/details", data, etag
        )
        return PlanDetails.model_validate(response)

    # ========== Buckets ==========

    async def list_buckets(self, plan_id: str) -> list[Bucket]:
        """List buckets in a plan.

        Args:
            plan_id: The plan ID.

        Returns:
            List of buckets.
        """
        response = await self.client.get(f"/planner/plans/{plan_id}/buckets")
        return [Bucket.model_validate(b) for b in response.get("value", [])]

    async def get_bucket(self, bucket_id: str) -> Bucket:
        """Get a bucket by ID.

        Args:
            bucket_id: The bucket ID.

        Returns:
            Bucket object.
        """
        response = await self.client.get(f"/planner/buckets/{bucket_id}")
        return Bucket.model_validate(response)

    async def create_bucket(self, plan_id: str, name: str) -> Bucket:
        """Create a new bucket.

        Args:
            plan_id: The plan ID.
            name: Bucket name.

        Returns:
            Created bucket.
        """
        data = {"planId": plan_id, "name": name}
        response = await self.client.post("/planner/buckets", data)
        return Bucket.model_validate(response)

    async def update_bucket(
        self, bucket_id: str, data: dict[str, Any], etag: str
    ) -> Bucket:
        """Update a bucket.

        Args:
            bucket_id: The bucket ID.
            data: Fields to update.
            etag: Current ETag for optimistic concurrency.

        Returns:
            Updated bucket.
        """
        response = await self.client.patch(
            f"/planner/buckets/{bucket_id}", data, etag
        )
        return Bucket.model_validate(response)

    async def delete_bucket(self, bucket_id: str, etag: str) -> bool:
        """Delete a bucket.

        Args:
            bucket_id: The bucket ID.
            etag: Current ETag for optimistic concurrency.

        Returns:
            True if successful.
        """
        return await self.client.delete(f"/planner/buckets/{bucket_id}", etag)

    # ========== Tasks ==========

    async def list_tasks(self, plan_id: str) -> list[Task]:
        """List tasks in a plan.

        Args:
            plan_id: The plan ID.

        Returns:
            List of tasks.
        """
        response = await self.client.get(f"/planner/plans/{plan_id}/tasks")
        return [Task.model_validate(t) for t in response.get("value", [])]

    async def list_bucket_tasks(self, bucket_id: str) -> list[Task]:
        """List tasks in a bucket.

        Args:
            bucket_id: The bucket ID.

        Returns:
            List of tasks.
        """
        response = await self.client.get(f"/planner/buckets/{bucket_id}/tasks")
        return [Task.model_validate(t) for t in response.get("value", [])]

    async def get_task(self, task_id: str) -> Task:
        """Get a task by ID.

        Args:
            task_id: The task ID.

        Returns:
            Task object.
        """
        response = await self.client.get(f"/planner/tasks/{task_id}")
        return Task.model_validate(response)

    async def create_task(
        self,
        plan_id: str,
        title: str,
        bucket_id: str | None = None,
        due_date: str | None = None,
        priority: int | None = None,
    ) -> Task:
        """Create a new task.

        Args:
            plan_id: The plan ID.
            title: Task title.
            bucket_id: Optional bucket ID.
            due_date: Optional due date (ISO format).
            priority: Optional priority (0=urgent, 1=important, 5=normal, 9=low).

        Returns:
            Created task.
        """
        data: dict[str, Any] = {"planId": plan_id, "title": title}

        if bucket_id:
            data["bucketId"] = bucket_id
        if due_date:
            data["dueDateTime"] = due_date
        if priority is not None:
            data["priority"] = priority

        response = await self.client.post("/planner/tasks", data)
        return Task.model_validate(response)

    async def update_task(
        self, task_id: str, data: dict[str, Any], etag: str
    ) -> Task:
        """Update a task.

        Args:
            task_id: The task ID.
            data: Fields to update.
            etag: Current ETag for optimistic concurrency.

        Returns:
            Updated task.
        """
        response = await self.client.patch(f"/planner/tasks/{task_id}", data, etag)
        # Handle empty response - fetch updated task
        if not response:
            return await self.get_task(task_id)
        return Task.model_validate(response)

    async def complete_task(self, task_id: str, etag: str) -> Task:
        """Mark a task as complete.

        Args:
            task_id: The task ID.
            etag: Current ETag for optimistic concurrency.

        Returns:
            Updated task.
        """
        return await self.update_task(task_id, {"percentComplete": 100}, etag)

    async def delete_task(self, task_id: str, etag: str) -> bool:
        """Delete a task.

        Args:
            task_id: The task ID.
            etag: Current ETag for optimistic concurrency.

        Returns:
            True if successful.
        """
        return await self.client.delete(f"/planner/tasks/{task_id}", etag)

    async def assign_task(
        self, task_id: str, user_id: str, etag: str
    ) -> Task:
        """Assign a task to a user.

        Args:
            task_id: The task ID.
            user_id: The user ID to assign.
            etag: Current ETag for optimistic concurrency.

        Returns:
            Updated task.
        """
        data = {
            "assignments": {
                user_id: {
                    "@odata.type": "#microsoft.graph.plannerAssignment",
                    "orderHint": " !",
                }
            }
        }
        return await self.update_task(task_id, data, etag)

    # ========== Task Details ==========

    async def get_task_details(self, task_id: str) -> TaskDetails:
        """Get task details (description, checklist, references).

        Args:
            task_id: The task ID.

        Returns:
            TaskDetails object.
        """
        response = await self.client.get(f"/planner/tasks/{task_id}/details")
        return TaskDetails.model_validate(response)

    async def update_task_details(
        self, task_id: str, data: dict[str, Any], etag: str
    ) -> TaskDetails:
        """Update task details.

        Args:
            task_id: The task ID.
            data: Fields to update (description, checklist, references).
            etag: Current ETag for optimistic concurrency.

        Returns:
            Updated TaskDetails object.
        """
        response = await self.client.patch(
            f"/planner/tasks/{task_id}/details", data, etag
        )
        return TaskDetails.model_validate(response)
