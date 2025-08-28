
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

## PX4 + Gazebo Garden + ROS 2 (Containerized)

### Build and start
```bash
cd /home/romix38/digital_oreon
docker build -t digital-oreon:humble -f docker/Dockerfile .
cd docker
docker compose up -d terminal
docker compose exec terminal bash
```

Inside the container:
```bash
source /opt/ros/humble/setup.bash
# Quick GUI check
xeyes | cat
rviz2 | cat
```

### Launch Gazebo Garden and bridge camera topics
In a first shell (inside the container):
```bash
gz sim -r shapes.sdf | cat
# or load your world/model as needed
```

In a second shell (inside the container), bridge image topics. Install was added already to the image:
```bash
source /opt/ros/humble/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  /camera@sensor_msgs/msg/Image@ignition.msgs.Image \
  /camera_info@sensor_msgs/msg/CameraInfo@ignition.msgs.CameraInfo \
  /depth_camera/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked \
  /depth_camera@sensor_msgs/msg/Image@ignition.msgs.Image

# Alternatively, use the dedicated image bridge
ros2 run ros_gz_image image_bridge /camera
```

### PX4 SITL (optional, prepared deps)
The container includes PX4 build dependencies. To run a quick SITL with Gazebo-classic or Gazebo Garden, clone PX4 and follow upstream docs. Example for SITL/Gazebo-classic:
```bash
cd ~/ros2_ws
git clone https://github.com/PX4/PX4-Autopilot.git
cd PX4-Autopilot
git submodule update --init --recursive
make px4_sitl gazebo
```

### Troubleshooting
- If PX4 shows:
  - `ERROR [gz_bridge] timed out waiting for clock message`
  - `ERROR [gz_bridge] Task start failed (-1)`
  - `ERROR [init] gz_bridge failed to start`
  - `ERROR [px4] Startup script returned with return value: 256`

  Run inside the container before launching:
  ```bash
  pkill -9 ruby || true
  unset GZ_IP
  unset GZ_PARTITION
  ```

- On WSLg, if RViz or Gazebo fails due to OpenGL, try:
  ```bash
  export LIBGL_ALWAYS_SOFTWARE=1
  ```

- If camera topics are not visible in ROS 2, confirm the bridge is running and topic names match your world/model.

## Runbook (SITL, MAVROS, logger, planner, metrics)

### Start the container
```bash
cd /home/romix38/digital_oreon
docker build -t digital-oreon:humble -f docker/Dockerfile .
cd docker && docker compose up -d terminal && docker compose exec terminal bash
```

Inside the container, ensure ROS env and RMW:
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export RMW_CYCLONEDDS_USE_SHM=0
```

### A) PX4 SITL + Gazebo
GUI:
```bash
~/ros2_ws/../scripts/run_sitl_gui.sh
```
Headless:
```bash
~/ros2_ws/../scripts/run_sitl_headless.sh
```

### B) MAVROS
```bash
~/ros2_ws/../scripts/run_mavros.sh
```

### C) Logger (Parquet/CSV)
```bash
~/ros2_ws/../scripts/ros2_logger.py
```
Outputs stored under `~/ros2_ws/runs/<timestamp>/` (+manifest.json).

### D) Online event processor
```bash
~/ros2_ws/../scripts/event_processor.py
```
Writes `events.jsonl` to the same run directory (ARM/DISARM, mode, OFFBOARD, takeoff/landing, deviation).

### E) Offboard helpers / route planner
Hover setpoints:
```bash
~/ros2_ws/../scripts/offboard_hover.sh
```
Square:
```bash
~/ros2_ws/../scripts/offboard_square.sh
```
Route planner (reads WAYPOINTS_FILE or flies square):
```bash
~/ros2_ws/../scripts/route_planner_offboard.py
```

### F) Metrics
```bash
~/ros2_ws/../scripts/compute_metrics.py
```
Reports deviation stats, armed ratio, events counts for last runs.

### G) Stop everything
```bash
~/ros2_ws/../scripts/stop_all.sh
```

## Test plan (short)

1. Bring-up: start SITL (GUI or headless) and MAVROS — verify `/mavros/state` shows `connected: true`.
2. OFFBOARD hover: run `offboard_hover.sh`, then set mode OFFBOARD + ARM (or use planner) — verify z≈2 m.
3. Route: run `route_planner_offboard.py` — UAV visits 4 waypoints, no mode drop.
4. Logging: run `ros2_logger.py` during flight — confirm Parquet files: `local_pose.parquet`, `setpoint_local.parquet`, `mavros_state.parquet`, `clock.parquet`.
5. Events: run `event_processor.py` — confirm `events.jsonl` contains ARM/DISARM, takeoff/landing, mode changes.
6. Metrics: run `compute_metrics.py` — confirm non-empty JSON with deviation/armed stats.
7. Replay (optional): use recorded bags or Parquet for analysis by `scripts/analyze_px4_data.py`.

Notes:
- Ensure both terminals use `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` and `RMW_CYCLONEDDS_USE_SHM=0`.
- If GUI issues on WSLg, prefer headless + QGC.
