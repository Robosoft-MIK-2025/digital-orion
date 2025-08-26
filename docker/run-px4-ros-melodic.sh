#!/bin/bash

USER_UID=$(id -u)
TAG='px4-ros-melodic-dev'
IMAGE='px4io/px4-dev-ros-melodic:latest'
TTY='--device=/dev/ttyACM0'   # оставь как есть, если нужно железо; иначе можно сделать пустой: TTY=''

# Разрешаем X11 для Docker GUI
xhost +local:docker

echo "IMAGE= $IMAGE"
echo "TAG= $TAG"
echo "USER_UID= $USER_UID"
echo "USER= $USER"
echo "IPADDR= $(hostname -I | cut -d' ' -f1)"
echo "TTY= $TTY"

ENV_PARAMS=()
OTHER_PARAMS=()
args=("$@")
for ((a=0; a<"${#args[@]}"; ++a)); do
    case ${args[a]} in
        -e) ENV_PARAMS+=("${args[a]} ${args[a+1]}"); ((++a)); ;;
        --env=*) ENV_PARAMS+=("${args[a]}"); ;;
        *) OTHER_PARAMS+=("${args[a]}"); ;;
    esac
done

docker run -it --rm \
  --name px4-ros-melodic-dev \
  --ipc=host --shm-size=8g \
  --privileged \
  -e DISPLAY=$DISPLAY \
  -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
  -e XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir \
  -e PULSE_SERVER=/mnt/wslg/PulseServer \
  -e QT_X11_NO_MITSHM=1 \
  -v /mnt/wslg:/mnt/wslg \
  -v /mnt/wslg/.X11-unix:/tmp/.X11-unix \
  -v $HOME/workspace:/workspace \
  -v $HOME/catkin_ws:/root/catkin_ws \
  px4io/px4-dev-ros-melodic:latest bash



export containerId=$(docker ps -l -q)

