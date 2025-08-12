FROM osrf/ros:humble-desktop-full

# Non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

# Create non-root user (optional, can be used if needed inside the container)
ARG USERNAME=mobile
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Base tooling and ROS repository key (base image already has ROS, this is mostly harmless)
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y \
       sudo curl gnupg2 lsb-release net-tools python3-pip build-essential git \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add - \
    && echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list

# Build and install can-utils (if not available via apt in the chosen base)
RUN git clone https://github.com/linux-can/can-utils.git /tmp/can-utils \
    && cd /tmp/can-utils \
    && make \
    && make install \
    && rm -rf /tmp/can-utils

# Install common ROS 2 packages and GUI dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
      ros-${ROS_DISTRO}-tf2-tools \
      ros-${ROS_DISTRO}-gazebo-ros \
      ros-${ROS_DISTRO}-gazebo-ros-pkgs \
      ros-${ROS_DISTRO}-robot-state-publisher \
      ros-${ROS_DISTRO}-joint-state-publisher \
      ros-${ROS_DISTRO}-xacro \
      ros-${ROS_DISTRO}-rviz2 \
      ros-${ROS_DISTRO}-hardware-interface \
      ros-${ROS_DISTRO}-transmission-interface \
      ros-${ROS_DISTRO}-urdf \
      ros-${ROS_DISTRO}-urdfdom \
      ros-${ROS_DISTRO}-urdfdom-headers \
      ros-${ROS_DISTRO}-urdf-tutorial \
      ros-${ROS_DISTRO}-apriltag-ros \
      ros-${ROS_DISTRO}-gz-ros2-control \
      ros-${ROS_DISTRO}-v4l2-camera \
      ros-${ROS_DISTRO}-camera-calibration \
      ros-${ROS_DISTRO}-nav2-bringup \
      libcanberra-gtk-module \
      libcanberra-gtk3-module \
      at-spi2-core \
      x11-apps \
      xauth \
    --fix-missing \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Initialize rosdep (ignore error if already initialized)
RUN rosdep init || true && rosdep update || true

# Source ROS 2 for the created user (handy for interactive shells)
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/$USERNAME/.bashrc

CMD ["bash"]


