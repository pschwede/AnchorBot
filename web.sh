#!/bin/bash

echo "Opening it in browser"
xdg-open http://0.0.0.0:8000 &
echo "Starting web interface"
python $(dirname "$0")/src/server.py $*
