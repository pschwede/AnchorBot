#!/bin/bash

nice -n 19 python $(dirname "$0")/src/anchorbot.py $*
