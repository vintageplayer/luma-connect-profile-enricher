#!/bin/sh

# Load environment variables from .env.local
if [ -f .env.local ]; then
    . .env.local
    export DOCKER_IMAGE_TAG
else
    echo "Error: .env.local file not found"
    exit 1
fi

# Expand variables in DOCKER_IMAGE_TAG
eval "DOCKER_IMAGE_TAG=\"$DOCKER_IMAGE_TAG\""

# Check if DOCKER_IMAGE_TAG is set
if [ -z "$DOCKER_IMAGE_TAG" ]; then
    echo "Error: DOCKER_IMAGE_TAG not set in .env.local"
    exit 1
fi

echo "Running tests in Docker container: $DOCKER_IMAGE_TAG"

# Run the Docker container with tests mounted
# Override WORKDIR to /app so tests can be run from root
# Set PYTHONPATH to /app/src so tests can import lib modules
# Override entrypoint to use shell and set PYTHONPATH properly
docker run --rm \
    -w /app/tests \
    -v $(pwd)/.env.local:/app/.env.local \
    -v $(pwd)/tests:/app/tests \
    "$DOCKER_IMAGE_TAG" "$@"
