#!/usr/bin/env python3
import os
import sys
import json
import signal
import datetime as dt
from dataclasses import dataclass

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from mavros_msgs.msg import State
from geometry_msgs.msg import PoseStamped


@dataclass
class Last:
    armed: bool | None = None
    mode: str | None = None
    offboard: bool = False
    z: float | None = None
    setpoint_xyz: tuple[float, float, float] | None = None


class EventProcessor(Node):
    def __init__(self, out_file: str, z_takeoff: float = 0.5, dev_thresh: float = 0.8):
        super().__init__("event_processor")
        self.last = Last()
        self.out_file = out_file
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        self.fp = open(out_file, "a", buffering=1)
        qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=10)

        self.create_subscription(State, "/mavros/state", self.on_state, qos)
        self.create_subscription(PoseStamped, "/mavros/local_position/pose", self.on_pose, qos)
        self.create_subscription(PoseStamped, "/mavros/setpoint_position/local", self.on_setpoint, qos)

        self.get_logger().info(f"event_processor writing to {self.out_file}")
        self.dev_thresh = float(dev_thresh)
        self.z_takeoff = float(z_takeoff)

    def write(self, kind: str, **payload):
        t = self.get_clock().now().to_msg()
        rec = {
            "t": {"sec": int(t.sec), "nsec": int(t.nanosec)},
            "event": kind,
            **payload,
        }
        self.fp.write(json.dumps(rec) + "\n")
        self.get_logger().info(f"{kind}: {payload}")

    def on_state(self, msg: State):
        if self.last.armed is None:
            self.last.armed = bool(msg.armed)
            self.last.mode = msg.mode
            self.last.offboard = (msg.mode == "OFFBOARD")
            return

        if bool(msg.armed) != self.last.armed:
            self.write("armed" if msg.armed else "disarmed")
            self.last.armed = bool(msg.armed)

        if msg.mode != self.last.mode:
            self.write("mode_change", from_mode=self.last.mode, to_mode=msg.mode)
            self.last.mode = msg.mode

        off = (msg.mode == "OFFBOARD")
        if off != self.last.offboard:
            self.write("offboard_active" if off else "offboard_inactive")
            self.last.offboard = off

    def on_pose(self, msg: PoseStamped):
        z = float(msg.pose.position.z)
        if self.last.z is None:
            self.last.z = z
            return
        # takeoff detection
        if self.last.z < self.z_takeoff <= z:
            self.write("takeoff", z=z)
        # landing detection
        if z < 0.1 and self.last.z >= 0.1:
            self.write("landing", z=z)
        self.last.z = z

        # deviation from setpoint
        if self.last.setpoint_xyz is not None:
            sx, sy, sz = self.last.setpoint_xyz
            dx = float(msg.pose.position.x) - sx
            dy = float(msg.pose.position.y) - sy
            dz = float(msg.pose.position.z) - sz
            dev = (dx * dx + dy * dy + dz * dz) ** 0.5
            if dev > self.dev_thresh:
                self.write("deviation", meters=dev)

    def on_setpoint(self, msg: PoseStamped):
        p = msg.pose.position
        self.last.setpoint_xyz = (float(p.x), float(p.y), float(p.z))

    def close(self):
        try:
            self.fp.flush()
            self.fp.close()
        except Exception:
            pass


def main():
    rclpy.init()
    base = os.environ.get("LOGGER_DIR", os.path.join(os.path.expanduser("~"), "ros2_ws", "runs"))
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = os.path.join(base, stamp)
    out_file = os.path.join(out_dir, "events.jsonl")
    node = EventProcessor(out_file)

    def _shutdown(*_):
        node.get_logger().info("Shutting down event_processor")
        node.close()
        node.destroy_node()
        rclpy.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    rclpy.spin(node)


if __name__ == "__main__":
    main()


