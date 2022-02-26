#!/usr/bin/env bash

echo "Starting Coyote Badger..."

# Start VNC server
export MACHINE=`uname -m`
if [ "$MACHINE" = "aarch64" ] ; then
  echo "Found aarch64 processor."
  export LD_PRELOAD=/lib/aarch64-linux-gnu/libgcc_s.so.1
elif [ "$MACHINE" = "arm" ] ; then
  echo "Found arm processor."
  export LD_PRELOAD=/lib/arm-linux-gnueabihf/libgcc_s.so.1
elif [ "$MACHINE" = "x86_64" ] ; then
  echo "Found x86 processor."
else
  echo "Found other $MACHINE processor."
fi
export DISPLAY=:2
vncserver \
  -geometry 1200x860 \
  -SecurityTypes None --I-KNOW-THIS-IS-INSECURE \
  $DISPLAY 1>/dev/null 2>/dev/null&

# Start noVNC server
./noVNC/utils/launch.sh --listen 3001 --vnc localhost:5902 1>/dev/null 2>/dev/null&

# Run flask
export FLASK_ENV=development
python3 -m coyote_badger.app
