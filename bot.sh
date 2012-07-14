#!/bin/bash

echo "Starting bot"
python $(dirname "$0")/src/anchorbot.py $1 $2 $3
