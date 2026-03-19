#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

import smbus2

# MPU6050 registers
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
GYRO_ZOUT = 0x47  # Gyro Z (0x43 + 4)
GYRO_SCALE = 131.0  # LSB per deg/s at ±250°/s


class IMUNode(Node):

    def __init__(self):
        super().__init__('imu_node')

        self.pub = self.create_publisher(Float32, '/sensors/heading_deg', 10)

        self.bus = None
        self.gyro_bias = 0.0
        self.heading_deg = 0.0
        self.last_time = None

        try:
            self.bus = smbus2.SMBus(1)
            self.bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
            self._calibrate_gyro()
            self.get_logger().info("MPU6050 initialized successfully")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize MPU6050: {e}")

        self.timer = self.create_timer(0.1, self.publish_heading)

    def _read_word(self, reg):
        high = self.bus.read_byte_data(MPU6050_ADDR, reg)
        low = self.bus.read_byte_data(MPU6050_ADDR, reg + 1)
        value = (high << 8) + low
        if value > 32768:
            value -= 65536
        return value

    def _calibrate_gyro(self):
        self.get_logger().info("Calibrating gyro... keep robot still")
        samples = 200
        total = 0
        for _ in range(samples):
            total += self._read_word(GYRO_ZOUT)
            time.sleep(0.005)
        self.gyro_bias = total / samples
        self.get_logger().info(f"Gyro bias: {self.gyro_bias:.2f}")

    def publish_heading(self):
        if self.bus is None:
            return

        try:
            now = time.time()
            if self.last_time is None:
                self.last_time = now
                return
            dt = now - self.last_time
            self.last_time = now

            gyro_raw = self._read_word(GYRO_ZOUT) - self.gyro_bias
            gyro_deg_s = gyro_raw / GYRO_SCALE

            # Dead zone
            if abs(gyro_deg_s) < 0.5:
                gyro_deg_s = 0.0

            self.heading_deg += gyro_deg_s * dt

            msg = Float32()
            msg.data = float(self.heading_deg)
            self.pub.publish(msg)

            self.get_logger().info(f"Heading: {self.heading_deg:.1f} deg")

        except Exception as e:
            self.get_logger().warn(f"IMU read error: {e}")


def main(args=None):
    rclpy.init(args=args)

    node = IMUNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
