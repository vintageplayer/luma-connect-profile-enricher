#!/bin/sh

# Load environment variables from .env.local
if [ -f .env.local ]; then
    . ./.env.local
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

echo "Running Docker container: $DOCKER_IMAGE_TAG"

# Run the Docker container
docker run --rm \
    --env-file .env.local \
    "$DOCKER_IMAGE_TAG" "$@"
