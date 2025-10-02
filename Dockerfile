# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.13.7
FROM python:${PYTHON_VERSION}-alpine3.22 AS builder

# Install git for private GitHub packages
RUN apk add --no-cache git

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set uv environment variables for optimal performance
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies separately for better caching
# Copy only dependency files first
COPY pyproject.toml uv.lock README.md ./

# Install dependencies with cache mount (excludes project itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy source code for project installation
COPY ./src ./src

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Final stage - minimal runtime image
FROM python:${PYTHON_VERSION}-alpine3.22

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=1000
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Copy the virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy source code
COPY --chown=appuser:appuser ./src ./src

# Switch to the non-privileged user to run the application.
USER appuser

# Add virtualenv to PATH
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/src

# Run the application - script name provided dynamically at runtime
ENTRYPOINT ["python"]
