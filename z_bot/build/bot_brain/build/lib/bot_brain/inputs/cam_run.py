#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from picamera2 import Picamera2


class PiCamPublisher(Node):
    def __init__(self):
        super().__init__('picam_node')

        # -------- Parameters --------
        self.declare_parameter('width', 320)
        self.declare_parameter('height', 240)
        self.declare_parameter('fps', 10.0)
        self.declare_parameter('topic', '/image_raw')
        self.declare_parameter('frame_id', 'camera')

        self.width = int(self.get_parameter('width').value)
        self.height = int(self.get_parameter('height').value)
        self.fps = float(self.get_parameter('fps').value)
        self.topic = str(self.get_parameter('topic').value)
        self.frame_id = str(self.get_parameter('frame_id').value)

        if self.fps <= 0.0:
            self.get_logger().warn("fps <= 0. Using fps=10.0")
            self.fps = 10.0

        # -------- ROS --------
        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Image, self.topic, qos_profile_sensor_data)

        # -------- Picamera2 Setup --------
        self.picam2 = Picamera2()

        # IMPORTANT: Use BGR888 so colors match OpenCV/ROS
        video_config = self.picam2.create_video_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"}
        )

        self.picam2.configure(video_config)
        self.picam2.start()

        self.get_logger().info(
            f"Pi Camera 3 started at {self.width}x{self.height} @ {self.fps} Hz"
        )

        # Timer
        self.timer = self.create_timer(1.0 / self.fps, self.timer_callback)

    def timer_callback(self):
        try:
            frame = self.picam2.capture_array()
        except Exception as e:
            self.get_logger().error(f"Camera capture failed: {e}")
            return

        if frame is None:
            self.get_logger().warn("Empty frame received")
            return

        # No color conversion needed (already BGR)
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        self.publisher.publish(msg)

    def destroy_node(self):
        try:
            self.picam2.stop()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PiCamPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
