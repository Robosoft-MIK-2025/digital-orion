#!/usr/bin/env python3
import os
import sys
import json
import signal
import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from std_msgs.msg import Header
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import Imu
from geometry_msgs.msg import PoseStamped
from mavros_msgs.msg import State

# Optional: pandas/pyarrow for Parquet
try:
    import pandas as pd
except Exception:
    pd = None


def to_time_ns(header: Header | None, now_ns: int) -> int:
    if header is not None and header.stamp is not None:
        return int(header.stamp.sec) * 1_000_000_000 + int(header.stamp.nanosec)
    return now_ns


@dataclass
class Buffer:
    name: str
    rows: List[Dict[str, Any]]

    def append(self, row: Dict[str, Any]):
        self.rows.append(row)

    def flush_parquet(self, base_dir: str):
        if not self.rows:
            return
        if pd is None:
            # Fallback: CSV
            import csv
            path = os.path.join(base_dir, f"{self.name}.csv")
            write_header = not os.path.exists(path)
            with open(path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(self.rows[0].keys()))
                if write_header:
                    w.writeheader()
                w.writerows(self.rows)
        else:
            df = pd.DataFrame(self.rows)
            path = os.path.join(base_dir, f"{self.name}.parquet")
            df.to_parquet(path, engine="pyarrow", index=False)
        self.rows.clear()


class Ros2Logger(Node):
    def __init__(self, out_dir: str, flush_every: float = 5.0):
        super().__init__("ros2_logger")
        os.makedirs(out_dir, exist_ok=True)
        self.out_dir = out_dir

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.buf_state = Buffer("mavros_state", [])
        self.buf_imu = Buffer("imu", [])
        self.buf_pose = Buffer("local_pose", [])
        self.buf_setpt = Buffer("setpoint_local", [])
        self.buf_clock = Buffer("clock", [])

        self.create_subscription(State, "/mavros/state", self.on_state, qos)
        self.create_subscription(Imu, "/mavros/imu/data", self.on_imu, qos)
        self.create_subscription(PoseStamped, "/mavros/local_position/pose", self.on_pose, qos)
        self.create_subscription(PoseStamped, "/mavros/setpoint_position/local", self.on_setpoint, qos)
        self.create_subscription(Clock, "/clock", self.on_clock, qos)

        self.timer = self.create_timer(flush_every, self.flush_all)
        self.get_logger().info(f"ros2_logger started. Writing into: {self.out_dir}")

    def on_state(self, msg: State):
        now = self.get_clock().now().nanoseconds
        self.buf_state.append(
            {
                "t_ns": now,
                "connected": bool(msg.connected),
                "armed": bool(msg.armed),
                "guided": bool(msg.guided),
                "manual_input": bool(msg.manual_input),
                "mode": msg.mode,
                "system_status": int(msg.system_status),
            }
        )

    def on_imu(self, msg: Imu):
        now = self.get_clock().now().nanoseconds
        t_ns = to_time_ns(msg.header, now)
        self.buf_imu.append(
            {
                "t_ns": t_ns,
                "ax": float(msg.linear_acceleration.x),
                "ay": float(msg.linear_acceleration.y),
                "az": float(msg.linear_acceleration.z),
                "gx": float(msg.angular_velocity.x),
                "gy": float(msg.angular_velocity.y),
                "gz": float(msg.angular_velocity.z),
                "qw": float(msg.orientation.w),
                "qx": float(msg.orientation.x),
                "qy": float(msg.orientation.y),
                "qz": float(msg.orientation.z),
            }
        )

    def on_pose(self, msg: PoseStamped):
        now = self.get_clock().now().nanoseconds
        t_ns = to_time_ns(msg.header, now)
        p = msg.pose.position
        q = msg.pose.orientation
        self.buf_pose.append(
            {
                "t_ns": t_ns,
                "x": float(p.x),
                "y": float(p.y),
                "z": float(p.z),
                "qw": float(q.w),
                "qx": float(q.x),
                "qy": float(q.y),
                "qz": float(q.z),
            }
        )

    def on_setpoint(self, msg: PoseStamped):
        now = self.get_clock().now().nanoseconds
        t_ns = to_time_ns(msg.header, now)
        p = msg.pose.position
        q = msg.pose.orientation
        self.buf_setpt.append(
            {
                "t_ns": t_ns,
                "x": float(p.x),
                "y": float(p.y),
                "z": float(p.z),
                "qw": float(q.w),
                "qx": float(q.x),
                "qy": float(q.y),
                "qz": float(q.z),
            }
        )

    def on_clock(self, msg: Clock):
        t = msg.clock
        self.buf_clock.append({"t_ns": int(t.sec) * 1_000_000_000 + int(t.nanosec)})

    def flush_all(self):
        for b in (self.buf_state, self.buf_imu, self.buf_pose, self.buf_setpt, self.buf_clock):
            b.flush_parquet(self.out_dir)


def main():
    rclpy.init()
    start = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base = os.environ.get("LOGGER_DIR", os.path.join(os.path.expanduser("~"), "ros2_ws", "runs"))
    out_dir = os.path.join(base, start)
    os.makedirs(out_dir, exist_ok=True)

    manifest = {
        "started_at": start,
        "topics": [
            "/mavros/state",
            "/mavros/imu/data",
            "/mavros/local_position/pose",
            "/mavros/setpoint_position/local",
            "/clock",
        ],
    }
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    node = Ros2Logger(out_dir)

    def _shutdown(*_):
        node.get_logger().info("Shutting down, flushing buffers...")
        node.flush_all()
        node.destroy_node()
        rclpy.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    rclpy.spin(node)


if __name__ == "__main__":
    main()


