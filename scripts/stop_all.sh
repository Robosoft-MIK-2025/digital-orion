#!/bin/bash
set -euo pipefail

# Stop PX4, Gazebo, MAVROS
pkill -f mavros_node || true
pkill -f gzserver || true
pkill -f gzclient || true
pkill -f gazebo || true
pkill -f px4 || true
pkill -f px4_sitl || true

echo "Stopped PX4/Gazebo/MAVROS if they were running."


