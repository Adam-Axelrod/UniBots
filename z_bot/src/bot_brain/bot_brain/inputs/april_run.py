#!/usr/bin/env python3

import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge

from bot_brain.logic.april import AprilTagDetector


class AprilTagNode(Node):
    def __init__(self):
        super().__init__("april_tag_node")

        self.declare_parameter("image_topic", "/image_raw")
        self.declare_parameter("detections_topic", "/apriltags/detections")
        self.declare_parameter("home_zone", "all")

        self.image_topic = str(self.get_parameter("image_topic").value)
        self.detections_topic = str(self.get_parameter("detections_topic").value)
        home_zone = str(self.get_parameter("home_zone").value)
        if home_zone == "all":
            home_zone = None

        self.bridge = CvBridge()
        self._detector = AprilTagDetector(home_zone)
        self._lock = threading.Lock()
        self._latest_frame = None

        camera_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )
        self._sub = self.create_subscription(
            Image, self.image_topic, self._image_cb, camera_qos
        )
        self._pub = self.create_publisher(Float32MultiArray, self.detections_topic, 10)

        self.timer = self.create_timer(0.05, self._process_latest)
        self.get_logger().info(
            f"AprilTag node: sub={self.image_topic} pub={self.detections_topic}"
        )

    def _image_cb(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"cv_bridge failed: {e}")
            return
        with self._lock:
            self._latest_frame = frame

    def _process_latest(self):
        with self._lock:
            if self._latest_frame is None:
                return
            frame = self._latest_frame.copy()

        detections = self._detector.detect(frame, frame_rgb=False)

        data = [float(len(detections))]
        for d in detections:
            data.extend([float(d.tag_id), d.center_x, d.center_y, d.area])
            for cx, cy in d.corners:
                data.extend([cx, cy])

        msg = Float32MultiArray()
        msg.data = data
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = AprilTagNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
