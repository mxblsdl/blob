#! /usr/bin/sh
docker run -d \
 --name dropbox_container \
 -p 80:80 \
 -v /app/data:/app/data \
 dropbox