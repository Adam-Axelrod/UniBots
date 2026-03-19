#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from gpiozero import PWMOutputDevice, DigitalOutputDevice


class MotorNode(Node):

    def __init__(self):
        super().__init__('motor_driver')

        # ---------------------------
        # Pin Setup
        # ---------------------------

        # Motor A (left)
        self.pwm_a = PWMOutputDevice(12)
        self.ain1 = DigitalOutputDevice(17)
        self.ain2 = DigitalOutputDevice(27)

        # Motor B (right)
        self.pwm_b = PWMOutputDevice(13)
        self.bin1 = DigitalOutputDevice(23)
        self.bin2 = DigitalOutputDevice(24)

        # Standby pin
        self.stby = DigitalOutputDevice(22)

        # Enable driver
        self.stby.on()

        # ROS subscriber
        self.sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_callback,
            10
        )

        self.get_logger().info("Motor driver node started")

    # ---------------------------
    # Motor Functions
    # ---------------------------

    def motor_forward(self, speed):

        self.ain1.on()
        self.ain2.off()
        self.pwm_a.value = speed

        self.bin1.off()
        self.bin2.on()
        self.pwm_b.value = speed


    def motor_backward(self, speed):

        self.ain1.off()
        self.ain2.on()
        self.pwm_a.value = speed

        self.bin1.on()
        self.bin2.off()
        self.pwm_b.value = speed


    def motor_right(self, speed):

        # left wheel forward
        self.ain1.on()
        self.ain2.off()
        self.pwm_a.value = speed

        # right wheel backward
        self.bin1.on()
        self.bin2.off()
        self.pwm_b.value = speed


    def motor_left(self, speed):

        # left wheel backward
        self.ain1.off()
        self.ain2.on()
        self.pwm_a.value = speed

        # right wheel forward
        self.bin1.off()
        self.bin2.on()
        self.pwm_b.value = speed


    def motor_stop(self):

        self.pwm_a.value = 0
        self.pwm_b.value = 0


    # ---------------------------
    # ROS cmd_vel callback
    # ---------------------------
    def cmd_callback(self, msg):

        lin = msg.linear.x
        ang = msg.angular.z

        self.get_logger().info(
            f"CMD lin={lin:.2f} ang={ang:.2f}"
        )

        # ---------------------------
        # Forward / Backward
        # ---------------------------

        if abs(lin) > 0.05:

            speed = min(abs(lin), 1.0)

            # prevent stall
            speed = max(speed, 0.5)

            if lin > 0:
                self.motor_forward(speed)
            else:
                self.motor_backward(speed)

        # ---------------------------
        # Turning
        # ---------------------------

        elif abs(ang) > 0.05:

            speed = min(abs(ang), 0.4)


            if ang < 0:
                self.motor_left(speed)
            else:
                self.motor_right(speed)

        # ---------------------------
        # Stop
        # ---------------------------

        else:
            self.motor_stop()

def main(args=None):

    rclpy.init(args=args)

    node = MotorNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.motor_stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
