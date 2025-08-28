#!/bin/bash
set -eo pipefail

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}
export RMW_CYCLONEDDS_USE_SHM=${RMW_CYCLONEDDS_USE_SHM:-0}

# Start publishing local position setpoints at 10 Hz (hover at z=2m)
exec ros2 topic pub -r 10 /mavros/setpoint_position/local geometry_msgs/msg/PoseStamped \
"{header: {frame_id: map}, pose: {position: {x: 0.0, y: 0.0, z: 2.0}, orientation: {w: 1.0}}}"


