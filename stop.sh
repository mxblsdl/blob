#! /usr/bin/sh

CONTAINER_NAME="dropbox_container"
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping existing container..."
    docker stop $CONTAINER_NAME
fi