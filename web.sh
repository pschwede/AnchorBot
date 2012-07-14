#!/bin/bash

echo "Opening it in browser"
x-www-browser http://0.0.0.0:8000 &
echo "Starting web interface"
python $(dirname "$0")/src/server.py $1 $2 $3
