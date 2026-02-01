"""Tests for CLI task commands."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from planer_cli.api.exceptions import (
    AuthenticationError,
    ETagMismatchError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from planer_cli.cli.tasks import (
    assign_task,
    complete_task,
    create_task,
    delete_task,
    filter_tasks,
    get_task,
    list_bucket_tasks,
    list_tasks,
    my_tasks,
    tasks,
    update_task,
)
from planer_cli.models.task import Task


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI runner for testing.

    Returns:
        CliRunner instance.
    """
    return CliRunner()


@pytest.fixture
def mock_task() -> Task:
    """Create a mock Task instance.

    Returns:
        Task instance for testing.
    """
    return Task(
        id="task-123",
        planId="plan-456",
        bucketId="bucket-789",
        title="Test Task",
        percentComplete=0,
        priority=5,
        dueDateTime=datetime(2024, 1, 20),
        etag='W/"etag-value"',
    )


@pytest.fixture
def mock_completed_task() -> Task:
    """Create a mock completed Task instance.

    Returns:
        Completed Task instance for testing.
    """
    return Task(
        id="task-124",
        planId="plan-456",
        title="Completed Task",
        percentComplete=100,
        priority=5,
    )


class TestFilterTasks:
    """Tests for filter_tasks helper function."""

    def test_filter_tasks_no_filters(self, mock_task: Task) -> None:
        """Test filtering with no filters applied.

        Args:
            mock_task: Mock task fixture.
        """
        result = filter_tasks([mock_task])

        assert len(result) == 1
        assert result[0] == mock_task

    def test_filter_tasks_open_only(
        self, mock_task: Task, mock_completed_task: Task
    ) -> None:
        """Test filtering for open tasks only.

        Args:
            mock_task: Mock task fixture.
            mock_completed_task: Mock completed task fixture.
        """
        tasks_list = [mock_task, mock_completed_task]
        result = filter_tasks(tasks_list, open_only=True)

        assert len(result) == 1
        assert result[0].percent_complete < 100

    def test_filter_tasks_done_only(
        self, mock_task: Task, mock_completed_task: Task
    ) -> None:
        """Test filtering for completed tasks only.

        Args:
            mock_task: Mock task fixture.
            mock_completed_task: Mock completed task fixture.
        """
        tasks_list = [mock_task, mock_completed_task]
        result = filter_tasks(tasks_list, done_only=True)

        assert len(result) == 1
        assert result[0].percent_complete == 100

    def test_filter_tasks_due_today(self) -> None:
        """Test filtering for tasks due today."""
        today = datetime.now().date()
        task_today = Task(
            id="1",
            planId="p1",
            title="Due today",
            dueDateTime=datetime.combine(today, datetime.min.time()),
        )
        task_tomorrow = Task(
            id="2",
            planId="p1",
            title="Due tomorrow",
            dueDateTime=datetime(2099, 12, 31),
        )

        result = filter_tasks([task_today, task_tomorrow], due_today=True)

        assert len(result) == 1
        assert result[0].id == "1"

    def test_filter_tasks_combined_filters(self) -> None:
        """Test filtering with multiple filters combined."""
        today = datetime.now().date()
        task_open_today = Task(
            id="1",
            planId="p1",
            title="Open today",
            percentComplete=50,
            dueDateTime=datetime.combine(today, datetime.min.time()),
        )
        task_done_today = Task(
            id="2",
            planId="p1",
            title="Done today",
            percentComplete=100,
            dueDateTime=datetime.combine(today, datetime.min.time()),
        )

        result = filter_tasks(
            [task_open_today, task_done_today], open_only=True, due_today=True
        )

        assert len(result) == 1
        assert result[0].id == "1"


class TestMyTasksCommand:
    """Tests for my_tasks CLI command."""

    def test_my_tasks_success(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test my tasks command with successful response.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.list_my_tasks.return_value = [mock_task]
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["my"], mix_stderr=False)

            assert result.exit_code == 0
            mock_planner_api.list_my_tasks.assert_called_once()
            mock_client.close.assert_called_once()

    def test_my_tasks_empty(self, cli_runner: CliRunner) -> None:
        """Test my tasks command with no tasks.

        Args:
            cli_runner: Click CLI runner fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.list_my_tasks.return_value = []
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["my"], mix_stderr=False)

            assert result.exit_code == 0
            assert "No tasks found" in result.output

    def test_my_tasks_with_filters(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test my tasks command with filter options.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.list_my_tasks.return_value = [mock_task]
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["my", "--open"], mix_stderr=False)

            assert result.exit_code == 0
            mock_planner_api.list_my_tasks.assert_called_once()

    def test_my_tasks_json_output(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test my tasks command with JSON output format.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.list_my_tasks.return_value = [mock_task]
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["my"], obj={"format": "json"}, mix_stderr=False)

            assert result.exit_code == 0


class TestListTasksCommand:
    """Tests for list_tasks CLI command."""

    def test_list_tasks_success(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test list tasks command with successful response.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.list_tasks.return_value = [mock_task]
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["list", "plan-456"])

            assert result.exit_code == 0
            mock_planner_api.list_tasks.assert_called_once_with("plan-456")


class TestGetTaskCommand:
    """Tests for get_task CLI command."""

    @pytest.mark.asyncio
    async def test_get_task_success(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test get task command with successful response.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.return_value = mock_task
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["get", "task-123"])

            assert result.exit_code == 0
            mock_planner_api.get_task.assert_called_once_with("task-123")

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, cli_runner: CliRunner) -> None:
        """Test get task command with task not found error.

        Args:
            cli_runner: Click CLI runner fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.side_effect = ResourceNotFoundError(
                "Task not found"
            )
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["get", "task-999"])

            assert result.exit_code == 1
            assert "Not found" in result.output


class TestCreateTaskCommand:
    """Tests for create_task CLI command."""

    @pytest.mark.asyncio
    async def test_create_task_minimal(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test create task command with minimal arguments.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.create_task.return_value = mock_task
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["create", "plan-456", "New Task"])

            assert result.exit_code == 0
            assert "Created task" in result.output
            mock_planner_api.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_with_options(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test create task command with all options.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.create_task.return_value = mock_task
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(
                tasks,
                [
                    "create",
                    "plan-456",
                    "New Task",
                    "--bucket-id",
                    "bucket-789",
                    "--due-date",
                    "2024-12-31",
                    "--priority",
                    "urgent",
                ],
            )

            assert result.exit_code == 0
            call_args = mock_planner_api.create_task.call_args
            assert call_args.kwargs["plan_id"] == "plan-456"
            assert call_args.kwargs["title"] == "New Task"
            assert call_args.kwargs["bucket_id"] == "bucket-789"
            assert call_args.kwargs["priority"] == 0

    @pytest.mark.asyncio
    async def test_create_task_invalid_date(self, cli_runner: CliRunner) -> None:
        """Test create task command with invalid date format.

        Args:
            cli_runner: Click CLI runner fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(
                tasks,
                ["create", "plan-456", "New Task", "--due-date", "invalid-date"],
            )

            assert result.exit_code == 0
            assert "must be in YYYY-MM-DD format" in result.output


class TestUpdateTaskCommand:
    """Tests for update_task CLI command."""

    @pytest.mark.asyncio
    async def test_update_task_success(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test update task command with successful update.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        updated_task = mock_task.model_copy(update={"title": "Updated Task"})

        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.return_value = mock_task
            mock_planner_api.update_task.return_value = updated_task
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(
                tasks, ["update", "task-123", "--title", "Updated Task"]
            )

            assert result.exit_code == 0
            assert "Updated task" in result.output

    @pytest.mark.asyncio
    async def test_update_task_no_options(self, cli_runner: CliRunner) -> None:
        """Test update task command with no update options provided.

        Args:
            cli_runner: Click CLI runner fixture.
        """
        result = cli_runner.invoke(tasks, ["update", "task-123"])

        assert result.exit_code == 0
        assert "At least one option is required" in result.output

    @pytest.mark.asyncio
    async def test_update_task_invalid_progress(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test update task command with invalid progress value.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.return_value = mock_task
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["update", "task-123", "--progress", "150"])

            assert result.exit_code == 0
            assert "must be between 0 and 100" in result.output

    @pytest.mark.asyncio
    async def test_update_task_etag_mismatch(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test update task command with ETag mismatch error.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.return_value = mock_task
            mock_planner_api.update_task.side_effect = ETagMismatchError(
                "Resource was modified"
            )
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(
                tasks, ["update", "task-123", "--title", "Updated"]
            )

            assert result.exit_code == 1
            assert "Conflict" in result.output


class TestCompleteTaskCommand:
    """Tests for complete_task CLI command."""

    @pytest.mark.asyncio
    async def test_complete_task_success(
        self, cli_runner: CliRunner, mock_task: Task, mock_completed_task: Task
    ) -> None:
        """Test complete task command with successful completion.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
            mock_completed_task: Mock completed task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.return_value = mock_task
            mock_planner_api.complete_task.return_value = mock_completed_task
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["complete", "task-123"])

            assert result.exit_code == 0
            assert "Completed task" in result.output
            mock_planner_api.complete_task.assert_called_once_with(
                "task-123", 'W/"etag-value"'
            )


class TestAssignTaskCommand:
    """Tests for assign_task CLI command."""

    @pytest.mark.asyncio
    async def test_assign_task_success(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test assign task command with successful assignment.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.return_value = mock_task
            mock_planner_api.assign_task.return_value = mock_task
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["assign", "task-123", "user-456"])

            assert result.exit_code == 0
            assert "Assigned task" in result.output


class TestDeleteTaskCommand:
    """Tests for delete_task CLI command."""

    @pytest.mark.asyncio
    async def test_delete_task_with_confirmation(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test delete task command with user confirmation.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.return_value = mock_task
            mock_planner_api.delete_task.return_value = True
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["delete", "task-123", "--yes"])

            assert result.exit_code == 0
            assert "Deleted task" in result.output
            mock_planner_api.delete_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_task_without_confirmation(
        self, cli_runner: CliRunner, mock_task: Task
    ) -> None:
        """Test delete task command without --yes flag requires confirmation.

        Args:
            cli_runner: Click CLI runner fixture.
            mock_task: Mock task fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.return_value = mock_task
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["delete", "task-123"], input="n\n")

            assert result.exit_code == 1
            mock_planner_api.delete_task.assert_not_called()


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, cli_runner: CliRunner) -> None:
        """Test CLI handles authentication errors gracefully.

        Args:
            cli_runner: Click CLI runner fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.list_my_tasks.side_effect = AuthenticationError(
                "Auth failed", 401
            )
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["my"])

            assert result.exit_code == 1
            assert "Authentication error" in result.output

    @pytest.mark.asyncio
    async def test_permission_denied_error_handling(
        self, cli_runner: CliRunner
    ) -> None:
        """Test CLI handles permission denied errors gracefully.

        Args:
            cli_runner: Click CLI runner fixture.
        """
        with patch("planer_cli.cli.tasks.get_client_and_api") as mock_get:
            mock_client = AsyncMock()
            mock_planner_api = AsyncMock()
            mock_planner_api.get_task.side_effect = PermissionDeniedError(
                "Access denied"
            )
            mock_get.return_value = (mock_client, mock_planner_api, None)

            result = cli_runner.invoke(tasks, ["get", "task-123"])

            assert result.exit_code == 1
            assert "Permission denied" in result.output
