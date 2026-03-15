#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import smbus2

MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
GYRO_XOUT = 0x43

class IMUDebug(Node):

    def __init__(self):

        super().__init__('imu_debug')

        self.bus = smbus2.SMBus(1)
        self.bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)

        self.timer = self.create_timer(0.1, self.read_imu)

        self.get_logger().info("IMU Debug Node Started")

    def read_word(self, reg):

        high = self.bus.read_byte_data(MPU6050_ADDR, reg)
        low = self.bus.read_byte_data(MPU6050_ADDR, reg + 1)

        value = (high << 8) + low

        if value > 32768:
            value -= 65536

        return value

    def read_imu(self):

        gx = self.read_word(GYRO_XOUT) / 131.0
        gy = self.read_word(GYRO_XOUT + 2) / 131.0
        gz = self.read_word(GYRO_XOUT + 4) / 131.0

        print(
            f"gyro_x: {gx:7.2f}  "
            f"gyro_y: {gy:7.2f}  "
            f"gyro_z: {gz:7.2f}"
        )


def main(args=None):

    rclpy.init(args=args)

    node = IMUDebug()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
