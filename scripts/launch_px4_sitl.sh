#!/bin/bash

# Launch PX4 SITL with proper environment setup
echo "Setting up environment for PX4 SITL..."

# Source ROS 2
source /opt/ros/humble/setup.bash

# Set proper environment variables
export DISPLAY=:0
export QT_QPA_PLATFORM=wayland
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir
export LIBGL_ALWAYS_SOFTWARE=1

# Set Gazebo variables
export GZ_IP=127.0.0.1
export GZ_PARTITION=
export GAZEBO_IP=127.0.0.1
export GAZEBO_MASTER_URI=http://127.0.0.1:11345

# Fix permissions if needed
if [ -d "/mnt/wslg/runtime-dir" ]; then
    echo "Checking WSLg runtime permissions..."
    if [ "$(stat -c %a /mnt/wslg/runtime-dir)" != "700" ]; then
        echo "Fixing runtime directory permissions..."
        sudo chmod 700 /mnt/wslg/runtime-dir
    fi
fi

# Check if we're in PX4 directory
if [ ! -f "Makefile" ] || [ ! -d "Tools" ]; then
    echo "Please run this script from PX4-Autopilot directory"
    echo "cd ~/ros2_ws/PX4-Autopilot"
    exit 1
fi

echo "Environment set up. Launching PX4 SITL with Gazebo..."
echo "Using DISPLAY: $DISPLAY"
echo "Using QT_QPA_PLATFORM: $QT_QPA_PLATFORM"

# Launch PX4 SITL
make px4_sitl gazebo
