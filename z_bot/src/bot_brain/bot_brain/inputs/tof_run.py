#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

import board
import busio
import adafruit_vl53l0x


class TOFNode(Node):
    def __init__(self):
        super().__init__("tof_node")

        # Publisher (FLOAT, in cm)
        self.pub = self.create_publisher(Float32, "/sensors/range", 10)

        # Init I2C + TOF sensor
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.tof = adafruit_vl53l0x.VL53L0X(i2c)
            self.get_logger().info("VL53L0X initialized successfully")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize TOF sensor: {e}")
            self.tof = None

        # Timer (10 Hz)
        self.timer = self.create_timer(0.1, self.publish_distance)

        # Moving average filter
        self.history = []
        self.window_size = 5

    def publish_distance(self):

        if self.tof is None:
            return

        try:
            dist_mm = self.tof.range  # mm

            # Ignore garbage values
            if dist_mm == 0 or dist_mm > 2000:
                return

            # Moving average
            self.history.append(dist_mm)
            if len(self.history) > self.window_size:
                self.history.pop(0)

            avg_mm = sum(self.history) / len(self.history)

            # ✅ Convert to cm
            dist_cm = avg_mm / 10.0

            # Publish
            msg = Float32()
            msg.data = dist_cm
            self.pub.publish(msg)

            self.get_logger().info(f"TOF: {dist_cm:.2f} cm")

        except Exception as e:
            self.get_logger().warn(f"Read error: {e}")


def main(args=None):
    rclpy.init(args=args)

    node = TOFNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
