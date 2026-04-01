#!/bin/bash
# x2_api/mqtt_run.sh — Launch the X2 MQTT client with correct environment
set -e

# Source ROS2 and AIMDK
source /opt/ros/humble/setup.bash
source /home/run/aimdk/install/setup.bash

# Add DRP package
export AMENT_PREFIX_PATH=/agibot/software/drp:$AMENT_PREFIX_PATH
export PYTHONPATH=/agibot/software/drp/local/lib/python3.10/dist-packages:$PYTHONPATH
export LD_LIBRARY_PATH=/agibot/software/drp/lib:$LD_LIBRARY_PATH

# MQTT config (override these per robot)
export X2_ROBOT_ID="${X2_ROBOT_ID:-x2-001}"
export X2_IOT_ENDPOINT="${X2_IOT_ENDPOINT:?Set X2_IOT_ENDPOINT to your AWS IoT endpoint}"
export X2_CERT_PATH="${X2_CERT_PATH:-/home/run/x2_api/certs}"

cd /home/run/x2_api
exec python3 mqtt_client.py "$@"
