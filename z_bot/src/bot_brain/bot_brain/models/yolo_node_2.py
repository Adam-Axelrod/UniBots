#!/usr/bin/env python3

#!/usr/bin/env python3
import os
import time
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge

import cv2
from ultralytics import YOLO


class YoloPiNode(Node):
    def __init__(self):
        super().__init__('yolo_pi_node')

        # ---------- Parameters ----------
        self.declare_parameter('image_topic', '/image_raw')
        self.declare_parameter('model_path', 'last.pt')
        self.declare_parameter('target_width', 320)
        self.declare_parameter('target_height', 240)
        self.declare_parameter('fps', 5.0)
        self.declare_parameter('conf', 0.35)
        self.declare_parameter('iou', 0.45)
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('imgsz', 256)              # IMPORTANT for Pi speed
        self.declare_parameter('class_id', 0)             # ping pong ball class id (usually 0 if single-class)
        self.declare_parameter('max_det', 20)

        self.declare_parameter('publish_annotated', True)
        self.declare_parameter('annotated_topic', '/yolo/annotated')
        self.declare_parameter('show_window', False)      # headless default
        self.declare_parameter('window_name', 'YOLO Pi')

        # Thread limits help on Pi sometimes
        self.declare_parameter('torch_threads', 2)

        self.image_topic = str(self.get_parameter('image_topic').value)
        self.model_path = str(self.get_parameter('model_path').value)
        self.tw = int(self.get_parameter('target_width').value)
        self.th = int(self.get_parameter('target_height').value)
        self.fps = float(self.get_parameter('fps').value)
        self.conf = float(self.get_parameter('conf').value)
        self.iou = float(self.get_parameter('iou').value)
        self.device = str(self.get_parameter('device').value)
        self.imgsz = int(self.get_parameter('imgsz').value)
        self.class_id = int(self.get_parameter('class_id').value)
        self.max_det = int(self.get_parameter('max_det').value)

        self.publish_annotated = bool(self.get_parameter('publish_annotated').value)
        self.annotated_topic = str(self.get_parameter('annotated_topic').value)
        self.show_window = bool(self.get_parameter('show_window').value)
        self.window_name = str(self.get_parameter('window_name').value)

        torch_threads = int(self.get_parameter('torch_threads').value)

        # ---------- Threading / performance tweaks ----------
        os.environ["OMP_NUM_THREADS"] = str(torch_threads)
        os.environ["OPENBLAS_NUM_THREADS"] = str(torch_threads)
        os.environ["MKL_NUM_THREADS"] = str(torch_threads)
        os.environ["NUMEXPR_NUM_THREADS"] = str(torch_threads)

        try:
            import torch
            torch.set_num_threads(torch_threads)
        except Exception:
            pass

        # ---------- YOLO ----------
        self.get_logger().info(f"Loading YOLO model: {self.model_path}")
        self.model = YOLO(self.model_path)
        try:
            self.model.fuse()
        except Exception:
            pass

        # ---------- ROS I/O ----------
        self.bridge = CvBridge()
        self.sub = self.create_subscription(
            Image,
            self.image_topic,
            self.image_cb,
            qos_profile_sensor_data
        )

        # Publish all ball centers & confidences (Option A)
        self.centers_pub = self.create_publisher(Float32MultiArray, '/ball/centers_x', 10)
        self.confs_pub = self.create_publisher(Float32MultiArray, '/ball/confs', 10)

        self.ann_pub = None
        if self.publish_annotated:
            self.ann_pub = self.create_publisher(Image, self.annotated_topic, 10)

        # ---------- Frame handling ----------
        self._lock = threading.Lock()
        self._latest_frame = None

        # Timer for processing rate
        period = 1.0 / max(self.fps, 0.1)
        self.timer = self.create_timer(period, self.process_latest)

        self.get_logger().info(
            f"Subscribed to {self.image_topic} | "
            f"Proc {self.fps} FPS | Resize {self.tw}x{self.th} | imgsz={self.imgsz} | conf={self.conf}"
        )

        if self.show_window:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def image_cb(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"cv_bridge failed: {e}")
            return

        with self._lock:
            self._latest_frame = frame

    def process_latest(self):
        with self._lock:
            if self._latest_frame is None:
                return
            frame = self._latest_frame.copy()

        # Resize down for speed
        frame_small = cv2.resize(frame, (self.tw, self.th), interpolation=cv2.INTER_AREA)

        t0 = time.time()

        # YOLO inference
        results = self.model.predict(
            source=frame_small,
            imgsz=self.imgsz,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False,
            classes=[self.class_id],     # only ball class
            max_det=self.max_det
        )

        dt = time.time() - t0
        inf_fps = (1.0 / dt) if dt > 0 else 0.0

        annotated = frame_small.copy()

        # Draw a vertical red origin line (for debug)
        h, w = annotated.shape[:2]
        cx = w // 2
        cv2.line(annotated, (cx, 0), (cx, h - 1), (0, 0, 255), 2)

        centers_x = []
        confs = []

        if len(results) > 0:
            r = results[0]
            if r.boxes is not None and len(r.boxes) > 0:
                for b in r.boxes:
                    conf = float(b.conf[0].item()) if b.conf is not None else 0.0
                    x1, y1, x2, y2 = b.xyxy[0].tolist()
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                    bx = (x1 + x2) // 2
                    by = (y1 + y2) // 2

                    centers_x.append(float(bx))
                    confs.append(float(conf))

                    # draw
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(annotated, (bx, by), 4, (0, 255, 255), -1)
                    cv2.putText(
                        annotated, f"ball {conf:.2f}", (x1, max(0, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA
                    )

        # Publish centers and confidences (even if empty)
        msg_x = Float32MultiArray()
        msg_x.data = centers_x
        self.centers_pub.publish(msg_x)

        msg_c = Float32MultiArray()
        msg_c.data = confs
        self.confs_pub.publish(msg_c)

        # Overlay inference speed
        cv2.putText(
            annotated,
            f"Infer: {inf_fps:.1f} FPS  ({dt*1000:.0f} ms)  balls={len(centers_x)}",
            (8, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        if self.ann_pub is not None:
            try:
                out = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
                self.ann_pub.publish(out)
            except Exception as e:
                self.get_logger().error(f"Publish annotated failed: {e}")

        if self.show_window:
            cv2.imshow(self.window_name, annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.get_logger().info("Quit requested (q). Shutting down.")
                rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = YoloPiNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

