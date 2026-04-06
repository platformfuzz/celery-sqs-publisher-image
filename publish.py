#!/usr/bin/env python3
"""Publish SQS messages with Kombu/Celery SQS transport-compatible bodies (SendMessage)."""

from __future__ import annotations

import os
import sys

import boto3
from celery import Celery


def _sqs_client(region: str):
    """SQS client; honors AWS_ENDPOINT_URL for LocalStack / custom endpoints."""
    kw: dict = {"region_name": region}
    endpoint = os.getenv("AWS_ENDPOINT_URL", "").strip()
    if endpoint:
        kw["endpoint_url"] = endpoint
    return boto3.client("sqs", **kw)


def _print_queue_depth(queue_url: str, region: str) -> None:
    """Best-effort SQS depth after publish (visible + in-flight)."""
    client = _sqs_client(region)
    out = client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=[
            "ApproximateNumberOfMessages",
            "ApproximateNumberOfMessagesNotVisible",
        ],
    )
    attrs = out.get("Attributes", {})
    print(
        "queue depth (approx): "
        f"visible={attrs.get('ApproximateNumberOfMessages', '?')} "
        f"in_flight={attrs.get('ApproximateNumberOfMessagesNotVisible', '?')}",
        file=sys.stderr,
    )


def main() -> int:
    try:
        queue_name = os.environ["QUEUE_NAME"]
        queue_url = os.environ["QUEUE_URL"]
    except KeyError as e:
        print(f"missing env: {e}", file=sys.stderr)
        return 1

    region = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
    count = int(os.getenv("ENQUEUE_COUNT", "200"))
    app_name = os.getenv("CELERY_APP_NAME", "celery_demo")
    task_name = os.getenv("CELERY_TASK_NAME", "celery_demo.noop")
    visibility_timeout = int(os.getenv("VISIBILITY_TIMEOUT", "30"))
    polling_interval = int(os.getenv("POLLING_INTERVAL", "1"))

    celery_app = Celery(app_name, broker="sqs://")
    celery_app.conf.task_default_queue = queue_name
    transport_opts: dict = {
        "region": region,
        "visibility_timeout": visibility_timeout,
        "polling_interval": polling_interval,
        "predefined_queues": {queue_name: {"url": queue_url}},
    }
    endpoint = os.getenv("AWS_ENDPOINT_URL", "").strip()
    if endpoint:
        transport_opts["endpoint_url"] = endpoint
    celery_app.conf.broker_transport_options = transport_opts

    # One explicit broker connection for the whole run so each SendMessage completes
    # before the process exits (short-lived scripts + pooled connections can look
    # "successful" while work is still buffered).
    with celery_app.connection_for_write() as conn:
        conn.ensure_connection(max_retries=3)
        for _ in range(count):
            celery_app.send_task(task_name, connection=conn)

    print(f"published {count} task message(s): {task_name}")

    if os.getenv("PRINT_QUEUE_ATTRIBUTES", "").lower() in ("1", "true", "yes"):
        _print_queue_depth(queue_url, region)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
