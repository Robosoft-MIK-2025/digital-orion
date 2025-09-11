FROM osrf/ros:humble-desktop-full

# --- базовые env
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

# --- пользователь без root
ARG USERNAME=mobile
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
 && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
 && apt-get update \
 && apt-get install -y sudo \
 && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
 && chmod 0440 /etc/sudoers.d/$USERNAME

# --- инструменты и ключи репозитория ROS
RUN apt-get update && apt-get upgrade -y \
 && apt-get install -y \
    sudo curl gnupg2 lsb-release net-tools python3-pip build-essential git wget ca-certificates \
 && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add - \
 && echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list

# --- репозиторий Gazebo (Jammy)
RUN wget -qO- https://packages.osrfoundation.org/gazebo.key | apt-key add - \
 && echo "deb https://packages.osrfoundation.org/gazebo/ubuntu-stable jammy main" > /etc/apt/sources.list.d/gazebo-stable.list

# --- can-utils
RUN git clone https://github.com/linux-can/can-utils.git /tmp/can-utils \
 && cd /tmp/can-utils && make && make install \
 && rm -rf /tmp/can-utils

# --- Gazebo + X11/Wayland deps для WSLg
RUN apt-get update && apt-get install -y \
    gazebo \
    libgazebo-dev \
    qtwayland5 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libgl1-mesa-dri \
    mesa-utils \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    at-spi2-core \
    x11-apps \
    xauth \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- ROS 2 пакеты (частями)
RUN apt-get update && apt-get install -y \
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
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    ros-${ROS_DISTRO}-mavros \
    ros-${ROS_DISTRO}-mavros-extras \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- инструменты сборки/bridge, gstreamer
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-rosinstall-generator \
    python3-vcstool \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- попытка поставить Gazebo Garden/bridge (если доступно)
RUN apt-get update && apt-get install -y \
    ros-${ROS_DISTRO}-ros-gzgarden \
    ros-${ROS_DISTRO}-ros-gz-bridge \
    ros-${ROS_DISTRO}-ros-gz-image \
    gz-garden \
  || echo "Some Gazebo Garden packages not available, skipping" \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Remove conflicting system packages and install Python deps via pip
RUN apt-get remove -y python3-pandas python3-numpy || true \
 && apt-get autoremove -y \
 && apt-get clean \
 && pip3 install --no-cache-dir --upgrade pip \
 && pip3 install --no-cache-dir --force-reinstall numpy==1.24.3 \
 && pip3 install --no-cache-dir --force-reinstall pandas==2.0.3 \
 && pip3 install --no-cache-dir pyarrow pyulog

# --- rosdep
RUN rosdep init || true && rosdep update || true

# --- PX4 deps
RUN apt-get update && apt-get install -y \
    git cmake ninja-build exiftool ccache \
    python3-dev python3-empy python3-jinja2 python3-numpy python3-toml python3-yaml \
    python3-setuptools python3-packaging python3-jsonschema python3-requests clang \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Python инструменты PX4
RUN pip3 install --no-cache-dir --upgrade \
    pip wheel kconfiglib pyserial pyulog empy==3.3.4 toml numpy packaging jsonschema

RUN apt-get update && apt-get install -y python3-genmsg python3-genpy \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Java JDK & jMAVSim (for PX4 HITL/SITL alternative sim)
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk ant \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Build and install jMAVSim in the correct location for PX4
RUN git clone --recursive https://github.com/PX4/jMAVSim.git /opt/jmavsim \
  && cd /opt/jmavsim \
  && git submodule update --init --recursive \
  && ant \
  && ln -sf /opt/jmavsim /home/${USERNAME}/jmavsim

# --- Удобные defaults для GUI внутри контейнера
ENV QT_QPA_PLATFORM=xcb
ENV QT_X11_NO_MITSHM=1
# XDG_RUNTIME_DIR выставляем в compose; здесь можно оставить как fallback:
ENV XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV RMW_CYCLONEDDS_USE_SHM=0

# --- окружение ROS для пользователя
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/${USERNAME}/.bashrc

# --- рабочая папка пользователя + совместимость с /root
RUN mkdir -p /home/${USERNAME}/ros2_ws \
 && chown -R ${USER_UID}:${USER_GID} /home/${USERNAME}/ros2_ws \
 && ln -s /home/${USERNAME}/ros2_ws /root/ros2_ws || true

# --- Создаем структуру директорий для PX4 и jMAVSim
RUN mkdir -p /home/${USERNAME}/ros2_ws/PX4-Autopilot/Tools/simulation \
 && ln -sf /opt/jmavsim /home/${USERNAME}/ros2_ws/PX4-Autopilot/Tools/simulation/jmavsim \
 && chown -R ${USER_UID}:${USER_GID} /home/${USERNAME}/ros2_ws/PX4-Autopilot

# --- Скрипт для проверки и исправления jMAVSim ссылки
RUN echo '#!/bin/bash\n\
echo "Checking jMAVSim installation..."\n\
if [ ! -L ~/ros2_ws/PX4-Autopilot/Tools/simulation/jmavsim ]; then\n\
  echo "Creating jMAVSim symbolic link..."\n\
  mkdir -p ~/ros2_ws/PX4-Autopilot/Tools/simulation\n\
  ln -sf /opt/jmavsim ~/ros2_ws/PX4-Autopilot/Tools/simulation/jmavsim\n\
  echo "jMAVSim linked successfully"\n\
else\n\
  echo "jMAVSim link already exists"\n\
fi\n\
echo "jMAVSim location: $(readlink ~/ros2_ws/PX4-Autopilot/Tools/simulation/jmavsim)"\n\
echo "jMAVSim contents:"\n\
ls -la ~/ros2_ws/PX4-Autopilot/Tools/simulation/jmavsim/ | head -5' > /home/${USERNAME}/check_jmavsim.sh \
 && chmod +x /home/${USERNAME}/check_jmavsim.sh

USER ${USERNAME}
WORKDIR /home/${USERNAME}/ros2_ws

CMD ["bash"]
