#!/usr/bin/env python3

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from picamera2 import Picamera2
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class PiCamPublisher(Node):
    def __init__(self):
        super().__init__('picam_node')

        # Parameters
        self.declare_parameter('width', 1080)
        self.declare_parameter('height', 720)
        self.declare_parameter('fps', 10.0)
        self.declare_parameter('topic', '/image_raw')
        self.declare_parameter('frame_id', 'camera')
        self.declare_parameter('rotation', 270)

        self.width = int(self.get_parameter('width').value)
        self.height = int(self.get_parameter('height').value)
        self.fps = float(self.get_parameter('fps').value)
        self.topic = str(self.get_parameter('topic').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        self.rotation = int(self.get_parameter('rotation').value)

        # CV bridge
        self.bridge = CvBridge()

        # QoS for camera: BEST_EFFORT, keep_last, depth 5
        camera_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        self.publisher = self.create_publisher(Image, self.topic, camera_qos)

        # Picamera2 setup
        self.picam2 = Picamera2()
        video_config = self.picam2.create_video_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"}
        )
        self.picam2.configure(video_config)
        self.picam2.start()

        self.get_logger().info(f"Pi Camera started at {self.width}x{self.height} @ {self.fps} Hz")

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

        # Apply rotation if camera is mounted sideways
        if self.rotation != 0:
            rotate_map = {
                90: cv2.ROTATE_90_CLOCKWISE,
                180: cv2.ROTATE_180,
                270: cv2.ROTATE_90_COUNTERCLOCKWISE,
            }
            if self.rotation in rotate_map:
                frame = cv2.rotate(frame, rotate_map[self.rotation])

        # Convert to ROS Image and publish
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = f"{self.frame_id}_{self.rotation}" if self.rotation != 0 else self.frame_id
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
