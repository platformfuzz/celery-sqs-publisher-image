# celery-sqs-publisher-image

[![Docker push](https://github.com/platformfuzz/celery-sqs-publisher-image/actions/workflows/docker-push.yml/badge.svg)](https://github.com/platformfuzz/celery-sqs-publisher-image/actions/workflows/docker-push.yml)

Python/Celery image: SendMessage with Kombu-compatible bodies to AWS SQS.

Workers must use a **compatible Celery SQS transport** configuration (region, `predefined_queues`, visibility timeout, etc.) and **task names** that match what you publish.

## Environment variables

| Variable | Required | Default | Description |
| -------- | -------- | ------- | ----------- |
| `QUEUE_NAME` | yes | — | SQS queue name (Celery default queue) |
| `QUEUE_URL` | yes | — | Full queue URL |
| `AWS_DEFAULT_REGION` | no | `ap-southeast-2` | AWS region for SQS |
| `AWS_ENDPOINT_URL` | no | — | Custom SQS API endpoint (e.g. `http://localstack:4566` for LocalStack). Passed to Kombu and boto3. |
| `ENQUEUE_COUNT` | no | `200` | Number of task messages to send |
| `CELERY_APP_NAME` | no | `celery_demo` | Celery app name passed to `Celery(...)` |
| `CELERY_TASK_NAME` | no | `celery_demo.noop` | Task name for `send_task()` |
| `VISIBILITY_TIMEOUT` | no | `30` | SQS visibility timeout (seconds) in broker options |
| `POLLING_INTERVAL` | no | `1` | Broker polling interval (seconds) |
| `PRINT_QUEUE_ATTRIBUTES` | no | — | Set to `1` / `true` / `yes` to print approximate **visible** and **in-flight** message counts to stderr after publishing (uses `GetQueueAttributes`) |

Credentials use the **default AWS SDK chain** (e.g. environment variables, `~/.aws` when mounted into the container, or the container’s IAM role on AWS).

**AWS SSO and Docker:** If you use **`aws sso login`**, Botocore may **refresh tokens** and write under **`~/.aws/sso/cache/`**. Mounting **`~/.aws:ro`** then fails with **`Read-only file system`** when it tries to create a temp file there. Use a **writable** mount (omit `:ro`), or use **long-lived access keys** via env vars instead of SSO.

## Run locally

```bash
docker build -t celery-sqs-publisher:local .

docker run --rm \
  -v "${HOME}/.aws:/root/.aws" \
  -e AWS_PROFILE \
  -e AWS_DEFAULT_REGION=ap-southeast-2 \
  -e QUEUE_NAME=your-queue-name \
  -e QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/ACCOUNT/your-queue-name \
  -e ENQUEUE_COUNT=50 \
  celery-sqs-publisher:local
```

### Did messages actually land in SQS?

The script only prints **published N** after Celery finishes **SendMessage** for each task on a single broker connection. If you still doubt delivery:

1. **`PRINT_QUEUE_ATTRIBUTES=1`** — prints approximate visible and in-flight counts **right after** the run (see env table). With **many workers** or **KEDA at high replica count**, messages are often **received immediately** → **visible ≈ 0** while **in_flight** is briefly non-zero, then messages are **deleted** after the worker ACKs — so both numbers can drop to **0** within seconds.
2. **AWS CLI:** `aws sqs get-queue-attributes --queue-url "$QUEUE_URL" --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible`
3. **Worker logs** — you should see task execution lines for `celery_demo.noop` if bodies are valid.
4. **Isolation test** — scale workers to **0** or pause consumers, publish a small `ENQUEUE_COUNT`, then check **visible** depth before re-enabling workers.

## Image from GitHub Container Registry

After CI pushes to **GHCR**, replace `OWNER` with your GitHub org or user (lowercase):

```text
ghcr.io/OWNER/celery-sqs-publisher-image:latest
ghcr.io/OWNER/celery-sqs-publisher-image:<git-short-sha>
```

Tag pushes `v*` also produce a matching image tag (e.g. `v1.0.0`).

Example:

```bash
docker run --rm \
  -v "${HOME}/.aws:/root/.aws" \
  -e AWS_DEFAULT_REGION=ap-southeast-2 \
  -e QUEUE_NAME=my-queue \
  -e QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/123456789012/my-queue \
  ghcr.io/OWNER/celery-sqs-publisher-image:latest
```

## Python and Celery versions

The image uses **`python:3-slim-bookworm`** (current stable Python 3.x on Debian Bookworm from Docker Hub). **Celery** is pinned in the `Dockerfile` (`CELERY_VERSION`, default **5.4.0**). If a new Python minor breaks the pinned Celery release, bump Celery in the `Dockerfile` / `pyproject.toml` or cap the base image (e.g. `python:3.13-slim-bookworm`) until upstream supports it.

## Development

- Optional local env: `python3 -m venv .venv && .venv/bin/pip install -e .` (see [`pyproject.toml`](pyproject.toml)).
- Format/lint: [Ruff](https://docs.astral.sh/ruff/) (`ruff check`, `ruff format`) — VS Code recommendations in [`.vscode/extensions.json`](.vscode/extensions.json).
