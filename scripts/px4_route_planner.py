#!/usr/bin/env python3
"""
Планирование маршрутов для PX4 SITL
Отправка команд в топики /fmu/in/ для управления дроном
"""

import rclpy
from rclpy.node import Node
from px4_msgs.msg import (
    TrajectorySetpoint,
    VehicleCommand,
    OffboardControlMode,
    VehicleStatus
)
import numpy as np
import time

class PX4RouteController(Node):
    def __init__(self):
        super().__init__('px4_route_controller')
        
        # Publishers для отправки команд в PX4
        self.trajectory_setpoint_pub = self.create_publisher(
            TrajectorySetpoint, '/fmu/in/trajectory_setpoint', 10)
        
        self.vehicle_command_pub = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', 10)
        
        self.offboard_control_mode_pub = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', 10)
        
        # Subscriber для получения статуса
        self.vehicle_status_sub = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status_v1',
            self.vehicle_status_callback, 10)
        
        # Состояние
        self.vehicle_status = None
        self.armed = False
        self.offboard_mode = False
        
        # Таймеры
        self.timer = self.create_timer(0.1, self.control_loop)  # 10 Hz
        self.command_timer = self.create_timer(1.0, self.send_commands)  # 1 Hz
        
        # Маршрут (простой квадрат)
        self.waypoints = [
            [0.0, 0.0, -5.0],   # Взлёт на 5м
            [10.0, 0.0, -5.0],  # Вперёд 10м
            [10.0, 10.0, -5.0], # Вправо 10м
            [0.0, 10.0, -5.0],  # Назад 10м
            [0.0, 0.0, -5.0],   # Домой
            [0.0, 0.0, -1.0]    # Посадка
        ]
        self.current_waypoint = 0
        self.mission_started = False
        
        self.get_logger().info('🚁 PX4 Route Controller запущен!')
        self.get_logger().info(f'📍 Маршрут: {len(self.waypoints)} точек')

    def vehicle_status_callback(self, msg):
        """Обработка статуса дрона"""
        self.vehicle_status = msg
        
        # Проверка состояния
        prev_armed = self.armed
        prev_offboard = self.offboard_mode
        
        self.armed = (msg.arming_state == VehicleStatus.ARMING_STATE_ARMED)
        self.offboard_mode = (msg.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD)
        
        # Логирование изменений
        if prev_armed != self.armed:
            self.get_logger().info(f'🔧 Armed: {self.armed}')
        
        if prev_offboard != self.offboard_mode:
            self.get_logger().info(f'🎮 Offboard: {self.offboard_mode}')

    def send_arm_command(self):
        """Постановка на охрану"""
        msg = VehicleCommand()
        msg.command = VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM
        msg.param1 = 1.0  # arm
        msg.param2 = 0.0
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        
        self.vehicle_command_pub.publish(msg)
        self.get_logger().info('📡 Отправлена команда ARM')

    def send_offboard_command(self):
        """Переключение в режим Offboard"""
        msg = VehicleCommand()
        msg.command = VehicleCommand.VEHICLE_CMD_DO_SET_MODE
        msg.param1 = 1.0  # main mode
        msg.param2 = 6.0  # offboard mode
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        
        self.vehicle_command_pub.publish(msg)
        self.get_logger().info('📡 Отправлена команда OFFBOARD')

    def send_takeoff_command(self):
        """Команда взлёта"""
        msg = VehicleCommand()
        msg.command = VehicleCommand.VEHICLE_CMD_NAV_TAKEOFF
        msg.param7 = 5.0  # altitude
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        
        self.vehicle_command_pub.publish(msg)
        self.get_logger().info('📡 Отправлена команда TAKEOFF')

    def send_trajectory_setpoint(self, x, y, z):
        """Отправка точки маршрута"""
        msg = TrajectorySetpoint()
        msg.position = [x, y, z]
        msg.velocity = [0.0, 0.0, 0.0]
        msg.acceleration = [0.0, 0.0, 0.0]
        msg.jerk = [0.0, 0.0, 0.0]
        msg.yaw = 0.0
        msg.yawspeed = 0.0
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        
        self.trajectory_setpoint_pub.publish(msg)

    def send_offboard_control_mode(self):
        """Режим управления Offboard"""
        msg = OffboardControlMode()
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.thrust_and_torque = False
        msg.direct_actuator = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        
        self.offboard_control_mode_pub.publish(msg)

    def control_loop(self):
        """Основной цикл управления"""
        # Всегда отправляем режим управления для поддержания Offboard
        self.send_offboard_control_mode()
        
        # Отправляем текущую точку маршрута
        if self.current_waypoint < len(self.waypoints):
            waypoint = self.waypoints[self.current_waypoint]
            self.send_trajectory_setpoint(waypoint[0], waypoint[1], waypoint[2])

    def send_commands(self):
        """Отправка команд с частотой 1 Гц"""
        if not self.mission_started:
            if not self.armed:
                self.send_arm_command()
                time.sleep(0.1)
            elif not self.offboard_mode:
                self.send_offboard_command()
                time.sleep(0.1)
            else:
                self.mission_started = True
                self.get_logger().info('🚀 Миссия начата!')
        
        # Управление прогрессом по точкам (упрощённо)
        if self.mission_started and self.current_waypoint < len(self.waypoints):
            # Переход к следующей точке каждые 10 секунд (упрощённо)
            elapsed = time.time() % 60  # сброс каждую минуту
            waypoint_time = int(elapsed / 10)
            
            if waypoint_time != self.current_waypoint and waypoint_time < len(self.waypoints):
                self.current_waypoint = waypoint_time
                waypoint = self.waypoints[self.current_waypoint]
                self.get_logger().info(
                    f'📍 Waypoint {self.current_waypoint + 1}/{len(self.waypoints)}: '
                    f'[{waypoint[0]:.1f}, {waypoint[1]:.1f}, {waypoint[2]:.1f}]'
                )

def main(args=None):
    rclpy.init(args=args)
    
    node = PX4RouteController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Остановка контроллера...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
