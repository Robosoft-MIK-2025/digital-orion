#!/bin/bash
set -euo pipefail

# PX4 SITL + Gazebo (headless)
cd "${HOME}/ros2_ws/PX4-Autopilot"

# Ensure ROS env
source /opt/ros/humble/setup.bash || true

# Prefer CycloneDDS if available
export RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}
export RMW_CYCLONEDDS_USE_SHM=${RMW_CYCLONEDDS_USE_SHM:-0}

export HEADLESS=1
exec make px4_sitl gazebo


