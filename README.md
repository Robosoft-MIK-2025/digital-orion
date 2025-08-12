# digital_oreon – ROS 2 Humble + WSLg Docker env

## Quick start (WSLg on Windows 11)

1) Build image
```bash
cd /home/romix38/digital_oreon
docker build -t fabook/mik:common -f docker/Dockerfile .
```

2) Start terminal container
```bash
cd docker
docker compose up -d terminal
```

3) Enter the container
```bash
docker compose exec terminal bash
```

4) GUI check (inside container)
```bash
xeyes | cat
rviz2 | cat
```

5) ROS 2 demo check (two terminals)
```bash
# terminal A (inside container)
ros2 run demo_nodes_cpp talker | cat
# terminal B (inside container)
ros2 run demo_nodes_cpp listener | cat
```

## Project structure
```
./
├─ docker/
│  ├─ Dockerfile
│  └─ compose.yaml
├─ ros2_ws/
│  └─ src/
└─ docs/
```

## Notes
- WSLg provides GUI support; no extra Windows X-server required.
- If RViz fails due to OpenGL, try: `export LIBGL_ALWAYS_SOFTWARE=1` inside container.
- Workspace sources are mounted at `/root/ros2_ws/src` inside the container.
