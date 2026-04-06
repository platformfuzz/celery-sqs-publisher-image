# Current stable Python 3.x on Bookworm (see docker-library official-images library/python).
FROM python:3-slim-bookworm

ARG CELERY_VERSION=5.4.0

RUN pip install --no-cache-dir "celery[sqs]==${CELERY_VERSION}"

COPY publish.py /publish.py

ENTRYPOINT ["python", "/publish.py"]
