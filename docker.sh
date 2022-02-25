#!/usr/bin/env bash

export DISPLAY=:99
Xvfb $DISPLAY -screen 0 1400x900x24 &

export FLASK_ENV=development
python3 -m coyote_badger.app
