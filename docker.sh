#!/usr/bin/env bash

export DISPLAY=:99
Xvfb $DISPLAY -screen 0 1280x780x24 &

export FLASK_ENV=development
python3 -m coyote_badger.app
