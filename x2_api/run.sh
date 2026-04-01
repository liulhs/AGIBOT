#!/bin/bash
# x2_api/run.sh — Launch the X2 Motion API with correct environment
set -e

# Source ROS2 and AIMDK
source /opt/ros/humble/setup.bash
source /home/run/aimdk/install/setup.bash

# Add DRP package (required for LinkCraft motion types)
export AMENT_PREFIX_PATH=/agibot/software/drp:$AMENT_PREFIX_PATH
export PYTHONPATH=/agibot/software/drp/local/lib/python3.10/dist-packages:$PYTHONPATH
export LD_LIBRARY_PATH=/agibot/software/drp/lib:$LD_LIBRARY_PATH

# Optional: override API key
export X2_API_KEY="${X2_API_KEY:-x2-dev-key-change-me}"

cd /home/run/x2_api
exec python3 server.py "$@"
