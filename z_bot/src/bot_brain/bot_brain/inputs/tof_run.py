#!/usr/bin/env python3

import math
from collections import deque
from statistics import median

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

try:
    import board
    import busio
    import adafruit_vl53l0x
    VL53_AVAILABLE = True
except ImportError:
    VL53_AVAILABLE = False  # Allows import/run on non-Pi for dev (won't measure)


class TOFNode(Node):
    """
    Publishes VL53L0X time-of-flight distance (cm) to a ROS topic.

    Safety features:
    - Median filter over last N valid readings
    - Invalid reading handling (publish NaN or keep last good)
    - Graceful fallback when sensor/hardware unavailable
    """

    def __init__(self):
        super().__init__('tof_node')

        # ------------ Parameters ------------
        self.declare_parameter('topic', '/sensors/range')
        self.declare_parameter('rate_hz', 10.0)

        # I2C (i2c_bus not used with Adafruit Blinka; board.SCL/SDA use default)
        self.declare_parameter('i2c_bus', 1)
        self.declare_parameter('i2c_address', 0x29)
        self.declare_parameter('timing_budget_us', 33000)

        # Validation / filtering
        self.declare_parameter('min_cm', 3.0)   # VL53L0X range ~30mm-1000mm
        self.declare_parameter('max_cm', 100.0)
        self.declare_parameter('median_window', 5)        # odd number recommended
        self.declare_parameter('invalid_mode', 'nan')     # 'nan' or 'hold_last'

        # ------------ Load parameters ------------
        self.topic = self.get_parameter('topic').value
        self.rate_hz = float(self.get_parameter('rate_hz').value)

        self.i2c_bus = int(self.get_parameter('i2c_bus').value)
        self.i2c_address = int(self.get_parameter('i2c_address').value)
        self.timing_budget_us = int(self.get_parameter('timing_budget_us').value)

        self.min_cm = float(self.get_parameter('min_cm').value)
        self.max_cm = float(self.get_parameter('max_cm').value)
        self.median_window = int(self.get_parameter('median_window').value)
        self.invalid_mode = str(self.get_parameter('invalid_mode').value).strip().lower()

        if self.median_window < 1:
            self.median_window = 1

        self.history = deque(maxlen=self.median_window)
        self.last_good = float('nan')

        # ------------ ROS publisher ------------
        self.pub = self.create_publisher(Float32, self.topic, 10)

        # ------------ VL53L0X init ------------
        self.vl53 = None
        if VL53_AVAILABLE:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.vl53 = adafruit_vl53l0x.VL53L0X(i2c, address=self.i2c_address)
                self.vl53.measurement_timing_budget = self.timing_budget_us
            except Exception as e:
                self.get_logger().warning(
                    f"VL53L0X init failed: {e}. TOF won't measure on this machine."
                )
                self.vl53 = None
        else:
            self.get_logger().warning(
                "adafruit_vl53l0x not available. TOF won't measure on this machine."
            )

        period = 1.0 / max(self.rate_hz, 0.1)
        self.timer = self.create_timer(period, self.tick)

        self.get_logger().info(
            f"TOF node publishing to {self.topic} at {self.rate_hz:.1f} Hz "
            f"(VL53L0X addr=0x{self.i2c_address:02x}, median_window={self.median_window}, invalid_mode={self.invalid_mode})"
        )

    def tick(self):
        dist = self.read_distance_cm()

        # Handle invalid reading
        if dist is None or not (self.min_cm <= dist <= self.max_cm):
            value = self.handle_invalid()
        else:
            self.last_good = dist
            self.history.append(dist)
            value = median(self.history) if len(self.history) > 0 else dist

        msg = Float32()
        msg.data = float(value)
        self.pub.publish(msg)

    def handle_invalid(self) -> float:
        if self.invalid_mode == 'hold_last' and not math.isnan(self.last_good):
            return float(self.last_good)
        return float('nan')

    def read_distance_cm(self):
        """
        Returns:
          distance_cm (float) if successful, else None if sensor unavailable or timeout.
        """
        if self.vl53 is None:
            return None

        try:
            range_mm = self.vl53.range
            # VL53L0X returns 65535 or similar for out-of-range / invalid
            if range_mm is None or range_mm <= 0 or range_mm > 10000:
                return None
            return range_mm / 10.0
        except (OSError, RuntimeError) as e:
            self.get_logger().debug(f"VL53L0X read error: {e}")
            return None

    def destroy_node(self):
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TOFNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
