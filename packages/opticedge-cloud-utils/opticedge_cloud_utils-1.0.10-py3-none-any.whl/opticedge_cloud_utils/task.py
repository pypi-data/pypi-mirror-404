import json
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from google.cloud import tasks_v2
from google.api_core import exceptions as gcloud_exceptions
from google.protobuf import timestamp_pb2

# Retry defaults (same intent as your TS version)
DEFAULT_RETRIES = 3
BASE_DELAY_MS = 300
MAX_DELAY_MS = 2000
TIMEOUT_MS = 15000

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = tasks_v2.CloudTasksClient()
    return _client


def _is_retryable_cloud_tasks(err: Exception) -> bool:
    """Return True if error is retryable."""
    if isinstance(err, gcloud_exceptions.AlreadyExists):
        return False

    if isinstance(err, (
        gcloud_exceptions.ServiceUnavailable,   # gRPC 14
        gcloud_exceptions.DeadlineExceeded,
        gcloud_exceptions.TooManyRequests,       # 429
        gcloud_exceptions.InternalServerError,   # 500
        gcloud_exceptions.BadGateway,             # 502
        gcloud_exceptions.GatewayTimeout          # 504
    )):
        return True

    return False


def _sleep_with_jitter(attempt: int):
    exp = min(MAX_DELAY_MS, BASE_DELAY_MS * (2 ** attempt))
    delay_ms = random.randint(0, exp)
    time.sleep(delay_ms / 1000)


def create_task(
    project_id: str,
    region: str,
    queue_name: str,
    audience: str,
    service_account: str,
    data: dict,
    schedule_delay: Optional[timedelta] = None,
    task_id: Optional[str] = None,
    retries: int = DEFAULT_RETRIES,
):
    if not all([project_id, region, queue_name, service_account, audience]):
        raise ValueError("Missing required Cloud Tasks parameters")

    client = _get_client()
    parent = client.queue_path(project_id, region, queue_name)

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": audience,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(data).encode(),
            "oidc_token": {
                "service_account_email": service_account,
                "audience": audience,
            },
        }
    }

    if schedule_delay:
        ts = timestamp_pb2.Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc) + schedule_delay)
        task["schedule_time"] = ts

    # Idempotent task creation
    if task_id:
        task["name"] = f"{parent}/tasks/{task_id}"

    start_time = time.time()
    attempt = 0
    last_err = None

    while attempt <= retries:
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms >= TIMEOUT_MS:
            break

        try:
            response = client.create_task(parent=parent, task=task)
            print(f"✅ Created Cloud Task: {response.name}")
            return response.name

        except gcloud_exceptions.AlreadyExists:
            # Treat idempotent create as success
            task_name = f"{parent}/tasks/{task_id}" if task_id else None
            print(f"⚠️ Task already exists: {task_name}")
            return task_name

        except Exception as err:
            last_err = err

            if not _is_retryable_cloud_tasks(err):
                raise

            if attempt >= retries:
                break

            print(f"⚠️ create_task retry #{attempt + 1}: {err}")
            _sleep_with_jitter(attempt + 1)
            attempt += 1

    raise RuntimeError(f"create_task failed after {attempt} retries") from last_err
