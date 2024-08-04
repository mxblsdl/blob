#! /usr/bin/sh

# Variables
IMAGE_NAME="dropbox"
CONTAINER_NAME="dropbox_container"
HOST_STATIC_DIR="/app/data"
CONTAINER_STATIC_DIR="/app/data"

# Build the new image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Stop and remove the existing container if it exists
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping existing container..."
    docker stop $CONTAINER_NAME
fi

if [ "$(docker ps -aq -f status=exited -f name=$CONTAINER_NAME)" ]; then
    echo "Removing existing container..."
    docker rm $CONTAINER_NAME
fi

# Run the new container
echo "Running new container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p 80:80 \
  -v $HOST_STATIC_DIR:$CONTAINER_STATIC_DIR \
  $IMAGE_NAME

echo "Deployment complete."