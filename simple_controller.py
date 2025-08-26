#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float64MultiArray
import time

class SimpleController(Node):
    def __init__(self):
        super().__init__('simple_controller')
        self.cmd_pub = self.create_publisher(String, '/fmu/in/vehicle_command', 10)
        self.pos_pub = self.create_publisher(Float64MultiArray, '/fmu/in/trajectory_setpoint', 10)
        self.timer = self.create_timer(1.0, self.send_command)
        self.get_logger().info(' Простой контроллер запущен!')
        
    def send_command(self):
        # Команда взлета
        cmd_msg = String()
        cmd_msg.data = "TAKEOFF"
        self.cmd_pub.publish(cmd_msg)
        
        # Позиция взлета
        pos_msg = Float64MultiArray()
        pos_msg.data = [0.0, 0.0, 5.0, 0.0]  # x, y, z, yaw
        self.pos_pub.publish(pos_msg)
        
        self.get_logger().info(' Отправлена команда: TAKEOFF + позиция [0, 0, 5]')

if __name__ == '__main__':
    rclpy.init()
    node = SimpleController()
    rclpy.spin(node)
    rclpy.shutdown()
