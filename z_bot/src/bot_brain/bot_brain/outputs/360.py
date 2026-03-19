#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from geometry_msgs.msg import Twist


class Turn360Node(Node):

    def __init__(self):

        super().__init__('turn_360_node')

        self.sub = self.create_subscription(
            Float32,
            '/sensors/heading_deg',
            self.rotation_cb,
            10
        )

        self.pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.start_rotation = None
        self.target = 360

        self.turn_speed = 0.5

        self.get_logger().info("360 turn node started")

    def rotation_cb(self, msg):

        rotation = msg.data

        if self.start_rotation is None:
            self.start_rotation = rotation

        turned = rotation - self.start_rotation

        twist = Twist()

        if turned < self.target:
            twist.angular.z = self.turn_speed
        else:
            twist.angular.z = 0.0
            self.get_logger().info("360 degree turn completed")

        self.pub.publish(twist)


def main(args=None):

    rclpy.init(args=args)

    node = Turn360Node()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
