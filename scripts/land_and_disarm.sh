#!/bin/bash
set -eo pipefail

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}
export RMW_CYCLONEDDS_USE_SHM=${RMW_CYCLONEDDS_USE_SHM:-0}

ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'AUTO.LAND'}" || true
sleep 2
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: false}"


