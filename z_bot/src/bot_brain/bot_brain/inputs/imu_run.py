#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

from mpu9250_jmdev.mpu_9250 import MPU9250
from mpu9250_jmdev.registers import (
    MPU9050_ADDRESS_68,
    AK8963_ADDRESS,
    GFS_250,
    AFS_2G,
    AK8963_BIT_16,
    AK8963_MODE_C100HZ,
)


def wrap_360(deg: float) -> float:
    deg = deg % 360.0
    if deg < 0:
        deg += 360.0
    return deg


class ImuCompassNode(Node):
    """
    Publishes compass heading (degrees 0..360) based on MPU9250 magnetometer.
    Topic: /sensors/heading_deg (Float32)
    """

    def __init__(self):
        super().__init__('imu_node')

        # ---- Parameters ----
        self.declare_parameter('topic', '/sensors/heading_deg')
        self.declare_parameter('rate_hz', 10.0)
        self.declare_parameter('declination_deg', 0.0)  # set if you want true-north-ish correction

        # Simple hard-iron offsets (optional quick calibration)
        self.declare_parameter('mag_offset_x', 0.0)
        self.declare_parameter('mag_offset_y', 0.0)

        # Smoothing on heading (0..1). 1=no smoothing, 0=no update.
        self.declare_parameter('alpha', 0.25)

        self.topic = str(self.get_parameter('topic').value)
        self.rate_hz = float(self.get_parameter('rate_hz').value)
        self.declination_deg = float(self.get_parameter('declination_deg').value)
        self.mag_offset_x = float(self.get_parameter('mag_offset_x').value)
        self.mag_offset_y = float(self.get_parameter('mag_offset_y').value)
        self.alpha = float(self.get_parameter('alpha').value)

        self.pub = self.create_publisher(Float32, self.topic, 10)

        # ---- Init MPU9250 ----
        # Note: On most boards, IMU is at 0x68; if yours is 0x69, change MPU9050_ADDRESS_68 accordingly.
        self.get_logger().info("Initializing MPU9250 (I2C)...")
        self.mpu = MPU9250(
            address_ak=AK8963_ADDRESS,
            address_mpu_master=MPU9050_ADDRESS_68,
            bus=1,
            gfs=GFS_250,
            afs=AFS_2G,
            mfs=AK8963_BIT_16,
            mode=AK8963_MODE_C100HZ,
        )

        # This configures the sensor + enables the mag through the MPU
        self.mpu.configure()

        self.filtered_heading = None

        period = 1.0 / max(self.rate_hz, 0.1)
        self.timer = self.create_timer(period, self.tick)

        self.get_logger().info(
            f"Publishing heading to {self.topic} @ {self.rate_hz:.1f} Hz "
            f"(declination={self.declination_deg:.2f}°, alpha={self.alpha:.2f})"
        )

    def tick(self):
        try:
            mx, my, mz = self.mpu.readMagnetometerMaster()  # returns (x,y,z)
        except Exception as e:
            self.get_logger().warn(f"Mag read failed: {e}")
            return

        # Apply offsets
        mx = float(mx) - self.mag_offset_x
        my = float(my) - self.mag_offset_y

        # Compute heading.
        # Depending on how your IMU board is mounted, you may need to flip axes/signs.
        heading_rad = math.atan2(my, mx)
        heading_deg = wrap_360(math.degrees(heading_rad) + self.declination_deg)

        # Wrap-safe low-pass filter
        if self.filtered_heading is None:
            self.filtered_heading = heading_deg
        else:
            prev = self.filtered_heading
            diff = (heading_deg - prev + 540.0) % 360.0 - 180.0
            self.filtered_heading = wrap_360(prev + self.alpha * diff)

        msg = Float32()
        msg.data = float(self.filtered_heading)
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImuCompassNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
