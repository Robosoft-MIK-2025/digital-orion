#!/bin/bash
set -eo pipefail

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}
export RMW_CYCLONEDDS_USE_SHM=${RMW_CYCLONEDDS_USE_SHM:-0}

pub() {
  ros2 topic pub -r 10 /mavros/setpoint_position/local geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: map}, pose: {position: {x: $1, y: $2, z: $3}, orientation: {w: 1.0}}}" &
  PID=$!
  sleep ${4}
  kill ${PID}
}

# Fly a 2x2m square at 2m altitude, ~5s per leg
pub 0 0 2 3
pub 2 0 2 5
pub 2 2 2 5
pub 0 2 2 5
pub 0 0 2 5


