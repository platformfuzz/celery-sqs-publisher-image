# celery-sqs-publisher-image

[![Deploy](https://github.com/platformfuzz/celery-sqs-publisher-image/actions/workflows/docker-push.yml/badge.svg)](https://github.com/platformfuzz/celery-sqs-publisher-image/actions/workflows/docker-push.yml)

Container entrypoint: publish **Celery/Kombu-shaped** task messages to **AWS SQS** (`SendMessage`). Consumers must use a matching Celery SQS setup (queue name, URL, region, task names).

## Environment

| Variable | Required | Default | Notes |
| -------- | -------- | ------- | ----- |
| `QUEUE_NAME` | yes | — | Celery default queue name |
| `QUEUE_URL` | yes | — | Full queue URL |
| `AWS_DEFAULT_REGION` | no | `ap-southeast-2` | |
| `AWS_ENDPOINT_URL` | no | — | e.g. `http://localstack:4566` (LocalStack) |
| `ENQUEUE_COUNT` | no | `200` | |
| `CELERY_APP_NAME` | no | `celery_demo` | |
| `CELERY_TASK_NAME` | no | `celery_demo.noop` | |
| `VISIBILITY_TIMEOUT` | no | `30` | Broker option (seconds) |
| `POLLING_INTERVAL` | no | `1` | Broker option (seconds) |
| `PRINT_QUEUE_ATTRIBUTES` | no | — | `1` / `true` / `yes` → stderr: approx visible + in-flight after publish |

Credentials: default **AWS SDK chain** (env vars, `~/.aws`, or task/instance role).

**SSO:** do not mount `~/.aws` **read-only** — token refresh writes `~/.aws/sso/cache/`.

## Run

```bash
docker build -t celery-sqs-publisher:local .

docker run --rm \
  -v "${HOME}/.aws:/root/.aws" \
  -e AWS_PROFILE -e AWS_DEFAULT_REGION=ap-southeast-2 \
  -e QUEUE_NAME=my-queue \
  -e QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/ACCOUNT/my-queue \
  -e ENQUEUE_COUNT=50 \
  celery-sqs-publisher:local
```

**GHCR:** `ghcr.io/<owner>/celery-sqs-publisher-image:latest` (and `:sha`, `:v*` from CI). Same `docker run`, swap the image name.

**Verify depth:** `PRINT_QUEUE_ATTRIBUTES=1` or `aws sqs get-queue-attributes` on `QUEUE_URL`. With active consumers, visible count often drops quickly.

## Versions

`Dockerfile`: `python:3-slim-bookworm`, `CELERY_VERSION` (default **5.4.0**). Bump Celery or pin an older base image if a new Python minor breaks the install.

## Dev

`python3 -m venv .venv && pip install -e .` — see [`pyproject.toml`](pyproject.toml). **Ruff** for lint/format.
