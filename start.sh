#!/bin/bash

HERE=$(dirname $0)

redis-server &
while true; do $HERE/bot.py; sleep 3600; done &
$HERE/web.py -d
