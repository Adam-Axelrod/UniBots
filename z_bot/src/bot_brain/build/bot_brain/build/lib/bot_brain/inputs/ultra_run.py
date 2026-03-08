#!/usr/bin/env python3

import math
import time
from collections import deque
from statistics import median

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None  # Allows you to import/run on non-Pi for dev (won't measure)


class UltrasonicNode(Node):
    """
    Publishes ultrasonic distance (cm) to a ROS topic.

    Safety features:
    - Timeouts so it never hangs if echo is missing
    - Median filter over last N valid readings
    - Invalid reading handling (publish NaN or keep last good)
    """

    def __init__(self):
        super().__init__('ultra_node')

        # ------------ Parameters ------------
        self.declare_parameter('topic', '/sensors/range')
        self.declare_parameter('rate_hz', 10.0)

        # GPIO BCM pins
        self.declare_parameter('trig_pin', 23)
        self.declare_parameter('echo_pin', 24)

        # Timing / physics
        self.declare_parameter('trigger_us', 10)          # trigger pulse length
        self.declare_parameter('echo_timeout_s', 0.025)   # 25ms ~ up to ~4m range

        # Validation / filtering
        self.declare_parameter('min_cm', 2.0)
        self.declare_parameter('max_cm', 400.0)
        self.declare_parameter('median_window', 5)        # odd number recommended
        self.declare_parameter('invalid_mode', 'nan')     # 'nan' or 'hold_last'

        # ------------ Load parameters ------------
        self.topic = self.get_parameter('topic').value
        self.rate_hz = float(self.get_parameter('rate_hz').value)

        self.trig_pin = int(self.get_parameter('trig_pin').value)
        self.echo_pin = int(self.get_parameter('echo_pin').value)

        self.trigger_us = int(self.get_parameter('trigger_us').value)
        self.echo_timeout_s = float(self.get_parameter('echo_timeout_s').value)

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

        # ------------ GPIO init ------------
        if GPIO is None:
            self.get_logger().warning("RPi.GPIO not available. Ultrasonic won't measure on this machine.")
        else:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trig_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
            GPIO.output(self.trig_pin, False)
            time.sleep(0.2)  # settle

        period = 1.0 / max(self.rate_hz, 0.1)
        self.timer = self.create_timer(period, self.tick)

        self.get_logger().info(
            f"Ultrasonic node publishing to {self.topic} at {self.rate_hz:.1f} Hz "
            f"(TRIG BCM{self.trig_pin}, ECHO BCM{self.echo_pin}, median_window={self.median_window}, invalid_mode={self.invalid_mode})"
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

        # Optional: log less aggressively (can spam)
        # self.get_logger().info(f"range_cm={msg.data:.2f}")

    def handle_invalid(self) -> float:
        if self.invalid_mode == 'hold_last' and not math.isnan(self.last_good):
            return float(self.last_good)
        return float('nan')

    def read_distance_cm(self):
        """
        Returns:
          distance_cm (float) if successful, else None if timeout / GPIO missing.
        """
        if GPIO is None:
            return None

        # Send trigger pulse
        GPIO.output(self.trig_pin, True)
        time.sleep(self.trigger_us / 1_000_000.0)
        GPIO.output(self.trig_pin, False)

        # Wait for echo to go HIGH (start), with timeout
        t0 = time.perf_counter()
        while GPIO.input(self.echo_pin) == 0:
            if (time.perf_counter() - t0) > self.echo_timeout_s:
                return None

        start = time.perf_counter()

        # Wait for echo to go LOW (end), with timeout
        while GPIO.input(self.echo_pin) == 1:
            if (time.perf_counter() - start) > self.echo_timeout_s:
                return None

        end = time.perf_counter()

        # Convert time -> distance
        dt = end - start
        # Speed of sound ~343 m/s => 34300 cm/s; divide by 2 for round trip
        distance_cm = (dt * 34300.0) / 2.0
        return distance_cm

    def destroy_node(self):
        # Clean GPIO on shutdown
        try:
            if GPIO is not None:
                GPIO.cleanup()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UltrasonicNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
