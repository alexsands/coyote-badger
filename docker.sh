#!/usr/bin/env bash

echo "Starting Coyote Badger...."

# Start VNC server
export LD_PRELOAD=/lib/aarch64-linux-gnu/libgcc_s.so.1
export DISPLAY=:2
vncserver \
  -geometry 1200x860 \
  -SecurityTypes None --I-KNOW-THIS-IS-INSECURE \
  $DISPLAY &

# Start noVNC server
./noVNC/utils/launch.sh --listen 3001 --vnc localhost:5902 &

# Run flask
export FLASK_ENV=development
python3 -m coyote_badger.app
