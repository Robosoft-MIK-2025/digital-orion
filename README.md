
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

6) Quick data recording (rosbag2)
```bash
# inside container, after `source /opt/ros/humble/setup.bash`
ros2 bag record -a -o sample
# Stop after 30–60s (Ctrl+C), then play back:
ros2 bag play sample
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
- WSLg provides GUI; if RViz fails due to OpenGL, try: `export LIBGL_ALWAYS_SOFTWARE=1`.
- Workspace sources are mounted at `/root/ros2_ws/src` inside the container.

## Next steps
- PX4 SITL (iris/x500) with Gazebo and ROS 2 bridge.
- Define data topics to record; move from `ros2 bag record -a` to a curated list.
- Add simple analysis notebook to parse `.db3` into Parquet.
