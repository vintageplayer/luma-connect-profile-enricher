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

echo "Building Docker image: $DOCKER_IMAGE_TAG"

# Build the Docker image
# Add --secret id=github_token,env=GITHUB_TOKEN for private repos if needed
# Add --ssh default for SSH-based private repos if needed
docker build . -t "$DOCKER_IMAGE_TAG"
