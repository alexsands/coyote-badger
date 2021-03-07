#!/usr/bin/env bash

cd -- "$(dirname "$0")"
docker build . -t coyotebadger:latest
docker run -it \
  --rm \
  --name coyotebadger \
  --memory="2g" \
  --cpus="2" \
  --tmpfs /tmp/coyotebadger/chrome \
  -v "$(pwd)"/_projects:/opt/coyotebadger/_projects \
  -p 5000:5000 \
  coyotebadger:latest
