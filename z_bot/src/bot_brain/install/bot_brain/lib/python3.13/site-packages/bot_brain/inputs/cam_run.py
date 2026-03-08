#!/usr/bin/env python3

import time
import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class CamPublisher(Node):
    def __init__(self):
        super().__init__('cam_node')

        # -------- Parameters --------
        self.declare_parameter('device', 0)             # /dev/videoX (integer index)
        self.declare_parameter('width', 320)
        self.declare_parameter('height', 240)
        self.declare_parameter('fps', 10.0)
        self.declare_parameter('topic', '/image_raw')
        self.declare_parameter('frame_id', 'camera')
        self.declare_parameter('retry_open', True)      # keep trying if camera not ready
        self.declare_parameter('retry_period_s', 1.0)   # seconds between retries

        self.device = int(self.get_parameter('device').value)
        self.width = int(self.get_parameter('width').value)
        self.height = int(self.get_parameter('height').value)
        self.fps = float(self.get_parameter('fps').value)
        self.topic = str(self.get_parameter('topic').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        self.retry_open = bool(self.get_parameter('retry_open').value)
        self.retry_period_s = float(self.get_parameter('retry_period_s').value)

        if self.fps <= 0.0:
            self.get_logger().warn("fps <= 0. Using fps=10.0")
            self.fps = 10.0

        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Image, self.topic, qos_profile_sensor_data)

        self.cap = None
        self._last_warn_time = 0.0

        # Try open camera once now
        self.try_open_camera()

        self.timer = self.create_timer(1.0 / self.fps, self.timer_callback)

        self.get_logger().info(
            f"Publishing {self.topic} from /dev/video{self.device} "
            f"target {self.width}x{self.height} @ {self.fps} Hz"
        )

    def try_open_camera(self):
        if self.cap is not None and self.cap.isOpened():
            return True

        cap = cv2.VideoCapture(self.device)
        if not cap.isOpened():
            self.cap = None
            return False

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)

        self.cap = cap
        self.get_logger().info(f"Camera opened: /dev/video{self.device}")
        return True

    def timer_callback(self):
        # Ensure camera is open
        if self.cap is None or not self.cap.isOpened():
            if self.retry_open:
                ok = self.try_open_camera()
                if not ok:
                    now = time.time()
                    if now - self._last_warn_time > self.retry_period_s:
                        self.get_logger().warn(f"Waiting for camera /dev/video{self.device}...")
                        self._last_warn_time = now
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            now = time.time()
            if now - self._last_warn_time > 1.0:
                self.get_logger().warn("Failed to grab frame")
                self._last_warn_time = now
            return

        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        self.publisher.publish(msg)

    def destroy_node(self):
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CamPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
