#!/bin/bash
set -euo pipefail

# MAVROS launcher bound to PX4 SITL default GCS channel (see mavlink status)

FCU_URL_DEFAULT="udp://:14550@127.0.0.1:18570"
FCU_URL="${1:-$FCU_URL_DEFAULT}"

source /opt/ros/humble/setup.bash

export RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}
export RMW_CYCLONEDDS_USE_SHM=${RMW_CYCLONEDDS_USE_SHM:-0}

exec ros2 run mavros mavros_node --ros-args \
  -p fcu_url:=${FCU_URL} \
  --params-file /opt/ros/humble/share/mavros/launch/px4_config.yaml \
  --params-file /opt/ros/humble/share/mavros/launch/px4_pluginlists.yaml


