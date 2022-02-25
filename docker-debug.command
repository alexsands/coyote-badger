#!/usr/bin/env bash

cd -- "$(dirname "$0")"
docker build \
  -t coyotebadger:latest \
  --platform="linux/x86_64" \
  --progress="plain" \
  --no-cache \
  .
docker run \
  -it \
  --rm \
  --name coyotebadger \
  --platform="linux/x86_64" \
  --ipc="host" \
  --shm-size="1gb" \
  --memory="2g" \
  --cpus="2" \
  -v "$(pwd)"/_projects:/opt/coyotebadger/_projects \
  -p 3000:3000 \
  coyotebadger:latest
