"""Pytest configuration and shared fixtures."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
import respx

from planer_cli.api.client import GraphClient
from planer_cli.api.planner import PlannerAPI
from planer_cli.auth.manager import AuthManager
from planer_cli.models.bucket import Bucket
from planer_cli.models.plan import Plan
from planer_cli.models.task import Task


@pytest.fixture
def mock_auth_manager() -> Mock:
    """Create a mock AuthManager.

    Returns:
        Mock AuthManager with get_access_token method.
    """
    mock = Mock(spec=AuthManager)
    mock.get_access_token.return_value = "mock_access_token"
    return mock


@pytest.fixture
async def graph_client(mock_auth_manager: Mock) -> GraphClient:
    """Create a GraphClient instance with mocked auth.

    Args:
        mock_auth_manager: Mocked AuthManager fixture.

    Returns:
        GraphClient instance for testing.
    """
    client = GraphClient(auth_manager=mock_auth_manager)
    yield client
    await client.close()


@pytest.fixture
def planner_api(graph_client: GraphClient) -> PlannerAPI:
    """Create a PlannerAPI instance.

    Args:
        graph_client: GraphClient fixture.

    Returns:
        PlannerAPI instance for testing.
    """
    return PlannerAPI(client=graph_client)


@pytest.fixture
def sample_task_data() -> dict:
    """Sample task data from Graph API.

    Returns:
        Dictionary representing a task response.
    """
    return {
        "id": "task-123",
        "planId": "plan-456",
        "bucketId": "bucket-789",
        "title": "Test Task",
        "percentComplete": 0,
        "priority": 5,
        "startDateTime": "2024-01-15T00:00:00Z",
        "dueDateTime": "2024-01-20T00:00:00Z",
        "completedDateTime": None,
        "assignments": {},
        "@odata.etag": 'W/"JzEtVGFzayAgQEBAQEBAQEBAQEBAQEBARCc="',
    }


@pytest.fixture
def sample_task(sample_task_data: dict) -> Task:
    """Sample Task model instance.

    Args:
        sample_task_data: Sample task data fixture.

    Returns:
        Task model instance.
    """
    return Task.model_validate(sample_task_data)


@pytest.fixture
def sample_plan_data() -> dict:
    """Sample plan data from Graph API.

    Returns:
        Dictionary representing a plan response.
    """
    return {
        "id": "plan-456",
        "title": "Test Plan",
        "owner": "group-123",
        "createdDateTime": "2024-01-01T00:00:00Z",
        "@odata.etag": 'W/"JzEtUGxhbiAgQEBAQEBAQEBAQEBAQEBARCc="',
    }


@pytest.fixture
def sample_plan(sample_plan_data: dict) -> Plan:
    """Sample Plan model instance.

    Args:
        sample_plan_data: Sample plan data fixture.

    Returns:
        Plan model instance.
    """
    return Plan.model_validate(sample_plan_data)


@pytest.fixture
def sample_bucket_data() -> dict:
    """Sample bucket data from Graph API.

    Returns:
        Dictionary representing a bucket response.
    """
    return {
        "id": "bucket-789",
        "planId": "plan-456",
        "name": "Test Bucket",
        "orderHint": "8585269235419339237",
        "@odata.etag": 'W/"JzEtQnVja2V0QEBAQEBAQEBAQEBAQEBARCc="',
    }


@pytest.fixture
def sample_bucket(sample_bucket_data: dict) -> Bucket:
    """Sample Bucket model instance.

    Args:
        sample_bucket_data: Sample bucket data fixture.

    Returns:
        Bucket model instance.
    """
    return Bucket.model_validate(sample_bucket_data)


@pytest.fixture
def respx_mock() -> respx.MockRouter:
    """Create a respx mock router.

    Returns:
        Respx router for mocking HTTP requests.
    """
    with respx.mock(base_url="https://graph.microsoft.com/v1.0") as router:
        yield router
