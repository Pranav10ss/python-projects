ARG PYTHON_VERSION=3.14.0
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /python_app/server

ARG UID=9000
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# enable the below command if any external libraries are added later
# COPY requirements.txt .
# RUN pip install -r requirements.txt   

USER appuser
COPY server/ .
EXPOSE 5050
CMD ["python3", "server.py"]