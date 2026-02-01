import json
import time
import pytest
from datetime import timedelta
from unittest.mock import Mock

from google.api_core import exceptions as gcloud_exceptions

import opticedge_cloud_utils.task as ct


# -----------------------
# Fixtures
# -----------------------

@pytest.fixture
def mock_client(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(ct, "_get_client", lambda: mock)
    return mock


@pytest.fixture
def base_args():
    return dict(
        project_id="proj",
        region="us-central1",
        queue_name="queue",
        audience="https://example.com",
        service_account="sa@example.iam.gserviceaccount.com",
        data={"hello": "world"},
    )


# -----------------------
# Core success paths
# -----------------------

def test_create_task_success(mock_client, base_args):
    mock_client.create_task.return_value = Mock(name="task-name")

    name = ct.create_task(**base_args)

    assert name
    mock_client.create_task.assert_called_once()


def test_create_task_with_task_id_idempotent(mock_client, base_args):
    mock_client.create_task.side_effect = gcloud_exceptions.AlreadyExists("exists")

    name = ct.create_task(**base_args, task_id="fixed-id")

    assert name.endswith("/tasks/fixed-id")
    mock_client.create_task.assert_called_once()


# -----------------------
# Retry behavior
# -----------------------

def test_create_task_retries_on_5xx_then_succeeds(mock_client, base_args):
    mock_client.create_task.side_effect = [
        gcloud_exceptions.InternalServerError("500"),
        gcloud_exceptions.ServiceUnavailable("503"),
        Mock(name="ok"),
    ]

    name = ct.create_task(**base_args, retries=3)

    assert name
    assert mock_client.create_task.call_count == 3


def test_create_task_retries_on_429(mock_client, base_args):
    mock_client.create_task.side_effect = [
        gcloud_exceptions.TooManyRequests("429"),
        Mock(name="ok"),
    ]

    name = ct.create_task(**base_args, retries=2)

    assert name
    assert mock_client.create_task.call_count == 2


def test_create_task_fails_after_retries(mock_client, base_args, monkeypatch):
    mock_client.create_task.side_effect = gcloud_exceptions.ServiceUnavailable("503")

    monkeypatch.setattr(ct.time, "sleep", lambda _: None)

    with pytest.raises(RuntimeError):
        ct.create_task(**base_args, retries=2)

    # initial + 2 retries
    assert mock_client.create_task.call_count == 3


def test_create_task_non_retryable_error(mock_client, base_args):
    mock_client.create_task.side_effect = gcloud_exceptions.PermissionDenied("403")

    with pytest.raises(gcloud_exceptions.PermissionDenied):
        ct.create_task(**base_args)

    mock_client.create_task.assert_called_once()


# -----------------------
# Schedule delay
# -----------------------

def test_create_task_with_schedule_delay(mock_client, base_args):
    mock_client.create_task.return_value = Mock(name="delayed-task")

    name = ct.create_task(
        **base_args,
        schedule_delay=timedelta(seconds=30)
    )

    assert name
    _, kwargs = mock_client.create_task.call_args
    assert "schedule_time" in kwargs["task"]


# -----------------------
# Coverage-specific tests
# -----------------------

def test_get_client_initializes(monkeypatch):
    ct._client = None
    fake_client = Mock()

    monkeypatch.setattr(ct.tasks_v2, "CloudTasksClient", lambda: fake_client)

    client = ct._get_client()
    assert client is fake_client


def test_is_retryable_false_for_non_retryable():
    err = gcloud_exceptions.PermissionDenied("403")
    assert ct._is_retryable_cloud_tasks(err) is False


def test_sleep_with_jitter(monkeypatch):
    called = {"sleep": False}

    monkeypatch.setattr(ct.time, "sleep", lambda _: called.update({"sleep": True}))

    ct._sleep_with_jitter(attempt=1)

    assert called["sleep"]


def test_create_task_stops_on_timeout(monkeypatch, mock_client, base_args):
    mock_client.create_task.side_effect = gcloud_exceptions.ServiceUnavailable("503")

    times = iter([0, 20])  # 20s later → exceeds TIMEOUT_MS (15s)
    monkeypatch.setattr(ct.time, "time", lambda: next(times))

    sleep_spy = Mock()
    monkeypatch.setattr(ct.time, "sleep", sleep_spy)

    with pytest.raises(RuntimeError):
        ct.create_task(**base_args, retries=5)

    sleep_spy.assert_not_called()
    assert mock_client.create_task.call_count == 0


def test_create_task_exhausts_retries(monkeypatch, mock_client, base_args):
    mock_client.create_task.side_effect = gcloud_exceptions.ServiceUnavailable("503")

    monkeypatch.setattr(ct.time, "sleep", lambda _: None)

    with pytest.raises(RuntimeError) as err:
        ct.create_task(**base_args, retries=2)

    assert "create_task failed after" in str(err.value)
    assert mock_client.create_task.call_count == 3
