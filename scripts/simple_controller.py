#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from px4_msgs.msg import VehicleCommand
import time

class SimpleController(Node):
    def __init__(self):
        super().__init__('simple_controller')
        self.cmd_pub = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', 10)
        self.timer = self.create_timer(1.0, self.send_takeoff)
        self.get_logger().info('�� Простой контроллер запущен!')
        
    def send_takeoff(self):
        cmd = VehicleCommand()
        cmd.command = 22  # VEHICLE_CMD_NAV_TAKEOFF
        cmd.param1 = 1.0
        cmd.target_system = 1
        cmd.target_component = 1
        cmd.source_system = 1
        cmd.source_component = 1
        cmd.from_external = True
        cmd.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        
        self.cmd_pub.publish(cmd)
        self.get_logger().info('�� Отправлена команда взлета')

if __name__ == '__main__':
    rclpy.init()
    node = SimpleController()
    rclpy.spin(node)
    rclpy.shutdown()
