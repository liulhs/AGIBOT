#!/bin/bash
# x2_api/debug_run.sh — Launch the X2 Debug Terminal
set -e
cd /home/run/x2_api
exec python3 debug_terminal.py "$@"
