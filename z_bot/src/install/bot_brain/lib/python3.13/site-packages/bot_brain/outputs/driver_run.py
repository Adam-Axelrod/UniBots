#!/usr/bin/env python3
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from gpiozero import Servo


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


class GpiozeroDualEscNode(Node):
    """
    BBB Antweight Dual ESC v3 control using gpiozero.Servo.

    Subscribes:
      /cmd_vel (geometry_msgs/Twist)

    Maps:
      move.value = clamp(linear.x / max_linear, -1..1)
      turn.value = clamp(angular.z / max_angular, -1..1)

    Assumes your proven mapping:
      move:  +1 forward, -1 backward, 0 neutral
      turn:  +1 right,   -1 left,     0 neutral

    Safety:
      - watchdog timeout -> neutral (0,0)
    """

    def __init__(self):
        super().__init__('gpiozero_dual_esc')

        # ----- Params -----
        self.declare_parameter('move_gpio', 22)       # your motor_pin_2
        self.declare_parameter('turn_gpio', 17)       # your motor_pin_1

        # cmd_vel scaling
        self.declare_parameter('max_linear', 0.25)    # m/s = full forward (+1)
        self.declare_parameter('max_angular', 1.5)    # rad/s = full right (+1)

        # some setups invert turning; set to -1.0 to flip
        self.declare_parameter('turn_sign', 1.0)
        self.declare_parameter('move_sign', 1.0)

        # watchdog: if no cmd_vel, go neutral
        self.declare_parameter('cmd_timeout_s', 0.3)

        # how often we enforce output + watchdog
        self.declare_parameter('update_hz', 50.0)

        self.move_gpio = int(self.get_parameter('move_gpio').value)
        self.turn_gpio = int(self.get_parameter('turn_gpio').value)

        self.max_linear = float(self.get_parameter('max_linear').value)
        self.max_angular = float(self.get_parameter('max_angular').value)

        self.turn_sign = float(self.get_parameter('turn_sign').value)
        self.move_sign = float(self.get_parameter('move_sign').value)

        self.cmd_timeout_s = float(self.get_parameter('cmd_timeout_s').value)
        self.update_hz = float(self.get_parameter('update_hz').value)

        # ----- Hardware -----
        # gpiozero.Servo uses -1..+1 with 0 as mid.
        # This worked for you, so we keep defaults.
        self.turn = Servo(self.turn_gpio)
        self.move = Servo(self.move_gpio)

        # Start neutral
        self.turn.value = 0.0
        self.move.value = 0.0
        time.sleep(0.5)

        # ----- ROS -----
        self.last_cmd_time = time.time()
        self.target_turn = 0.0
        self.target_move = 0.0

        self.sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_cb, 10)

        period = 1.0 / max(self.update_hz, 1.0)
        self.timer = self.create_timer(period, self.update)

        self.get_logger().info(
            f"gpiozero dual ESC node started. turn_gpio={self.turn_gpio}, move_gpio={self.move_gpio}. "
            f"max_linear={self.max_linear}, max_angular={self.max_angular}"
        )

    def cmd_cb(self, msg: Twist):
        self.last_cmd_time = time.time()

        lin = msg.linear.x
        ang = msg.angular.z

        # normalize to [-1..1]
        mv = 0.0 if self.max_linear <= 1e-6 else (lin / self.max_linear)
        tv = 0.0 if self.max_angular <= 1e-6 else (ang / self.max_angular)

        mv = clamp(mv, -1.0, 1.0) * self.move_sign
        tv = clamp(tv, -1.0, 1.0) * self.turn_sign

        self.target_move = clamp(mv, -1.0, 1.0)
        self.target_turn = clamp(tv, -1.0, 1.0)

    def update(self):
        # Watchdog -> neutral
        if (time.time() - self.last_cmd_time) > self.cmd_timeout_s:
            self.turn.value = 0.0
            self.move.value = 0.0
            return

        # Apply command
        self.turn.value = float(self.target_turn)
        self.move.value = float(self.target_move)

    def destroy_node(self):
        try:
            self.turn.value = 0.0
            self.move.value = 0.0
            time.sleep(0.2)
            self.turn.value = None
            self.move.value = None
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GpiozeroDualEscNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
