#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import time
from typing import List, Tuple
import threading
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

# ------------------ Clustering utilities ------------------
def cluster_by_distance(pts: List[Tuple[float, float]], dist_thresh: float) -> List[List[int]]:
    n = len(pts)
    if n == 0:
        return []

    visited = [False] * n
    clusters: List[List[int]] = []
    dist2 = dist_thresh * dist_thresh

    for i in range(n):
        if visited[i]:
            continue
        queue = [i]
        visited[i] = True
        cluster = [i]
        while queue:
            a = queue.pop()
            ax, ay = pts[a]
            for b in range(n):
                if visited[b]:
                    continue
                bx, by = pts[b]
                dx = bx - ax
                dy = by - ay
                if (dx * dx + dy * dy) <= dist2:
                    visited[b] = True
                    queue.append(b)
                    cluster.append(b)
        clusters.append(cluster)
    return clusters

def cluster_centroid(pts: List[Tuple[float, float]], idxs: List[int]) -> Tuple[float, float]:
    sx = sum(pts[i][0] for i in idxs)
    sy = sum(pts[i][1] for i in idxs)
    return sx / len(idxs), sy / len(idxs)

# ------------------ YOLO clustering headless ------------------
class YoloClusterHeadlessNode(Node):
    def __init__(self):
        super().__init__('yolo_cluster_headless_node')

        # Parameters
        self.declare_parameter('image_topic', '/image_raw')
        self.declare_parameter('annotated_topic', '/yolo/annotated')
        self.declare_parameter('model_path', '/home/gautam/best.pt')
        self.declare_parameter('conf', 0.25)
        self.declare_parameter('iou', 0.45)
        self.declare_parameter('imgsz', 256)
        self.declare_parameter('max_det', 50)

        self.declare_parameter('cluster_dist_px', 45.0)
        self.declare_parameter('cluster_dist_scale', 1.8)
        self.declare_parameter('min_cluster_size', 1)
        self.declare_parameter('center_deadband_px', 50.0)

        # Read parameters
        self.image_topic = str(self.get_parameter('image_topic').value)
        self.annotated_topic = str(self.get_parameter('annotated_topic').value)
        self.model_path = str(self.get_parameter('model_path').value)
        self.conf = float(self.get_parameter('conf').value)
        self.iou = float(self.get_parameter('iou').value)
        self.imgsz = int(self.get_parameter('imgsz').value)
        self.max_det = int(self.get_parameter('max_det').value)

        self.cluster_dist_px = float(self.get_parameter('cluster_dist_px').value)
        self.cluster_dist_scale = float(self.get_parameter('cluster_dist_scale').value)
        self.min_cluster_size = int(self.get_parameter('min_cluster_size').value)
        self.center_deadband_px = float(self.get_parameter('center_deadband_px').value)

        # ROS I/O
        self.bridge = CvBridge()

        # Subscriber QoS must match PiCam BEST_EFFORT
        camera_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        self.sub = self.create_subscription(Image, self.image_topic, self.image_cb, camera_qos)

        # Annotated publisher: BEST_EFFORT for smooth streaming
        annotated_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        self.ann_pub = self.create_publisher(Image, self.annotated_topic, annotated_qos)

        # Cluster publisher
        self.cluster_pub = self.create_publisher(Float32MultiArray, '/ball/cluster', 10)

        # Frame buffer
        self._lock = threading.Lock()
        self._latest_frame = None

        # Load YOLO
        self.get_logger().info(f"Loading YOLO model from {self.model_path}")
        self.model = YOLO(self.model_path)
        self.prev_time = time.time()

        # Timer
        self.timer = self.create_timer(0.05, self.process_latest)  # ~20 FPS
        self.get_logger().info("YOLO clustering headless node started.")

    def image_cb(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"cv_bridge conversion failed: {e}")
            return
        with self._lock:
            self._latest_frame = frame

    def process_latest(self):
        with self._lock:
            if self._latest_frame is None:
                return
            frame = self._latest_frame.copy()

        # YOLO inference
        results = self.model(frame, conf=self.conf, iou=self.iou, imgsz=self.imgsz, verbose=False, max_det=self.max_det)
        annotated = frame.copy()
        h, w = annotated.shape[:2]
        mid = w // 2

        centers: List[Tuple[float, float]] = []
        bbox_widths: List[float] = []

        if len(results) > 0:
            r = results[0]
            if r.boxes is not None and len(r.boxes) > 0:
                for b in r.boxes:
                    x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
                    bx = (x1 + x2) / 2.0
                    by = (y1 + y2) / 2.0
                    centers.append((bx, by))
                    bbox_widths.append(max(1, x2 - x1))
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Clustering
        if bbox_widths:
            med_w = sorted(bbox_widths)[len(bbox_widths)//2]
            dist_thresh = max(self.cluster_dist_px, self.cluster_dist_scale * med_w)
        else:
            dist_thresh = self.cluster_dist_px

        cluster_indices = cluster_by_distance(centers, dist_thresh)
        cluster_indices = [c for c in cluster_indices if len(c) >= self.min_cluster_size]

        cluster_infos: List[Tuple[int, float, float, float]] = []
        for idxs in cluster_indices:
            cx, cy = cluster_centroid(centers, idxs)
            cluster_infos.append((len(idxs), abs(cx-mid), cx, cy))

        # Major cluster
        major = None
        for info in cluster_infos:
            if major is None or info[0] > major[0] or (info[0]==major[0] and info[1]<major[1]):
                major = info

        # Publish cluster info
        msg = Float32MultiArray()
        if major is None:
            msg.data = []
        else:
            major_count, _, major_cx, major_cy = major
            if abs(major_cx - mid) <= self.center_deadband_px:
                major_side = 0.0
            elif major_cx < mid:
                major_side = -1.0
            else:
                major_side = 1.0
            msg.data = [major_side, major_cx, major_cy, major_count, len(cluster_infos)]
        self.cluster_pub.publish(msg)

        # Draw centroids
        for size, _, cx, cy in cluster_infos:
            cv2.circle(annotated, (int(cx), int(cy)), 10, (255, 255, 0), 2)
            cv2.putText(annotated, f"C{size}", (int(cx)-10, int(cy)-12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

        if major is not None:
            _, _, mcx, mcy = major
            cv2.circle(annotated, (int(mcx), int(mcy)), 14, (255,0,0), 2)
            cv2.putText(annotated, "MAJOR", (int(mcx)-30, int(mcy)-20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0),2)

        # FPS overlay
        curr_time = time.time()
        fps = 1 / (curr_time - self.prev_time) if (curr_time - self.prev_time) > 0 else 0
        self.prev_time = curr_time
        cv2.putText(annotated, f"FPS: {fps:.1f} balls={len(centers)} clusters={len(cluster_infos)}",
                    (8,20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 2)

        # Publish annotated frame
        try:
            out_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
            out_msg.header.stamp = self.get_clock().now().to_msg()
            self.ann_pub.publish(out_msg)
        except Exception as e:
            self.get_logger().error(f"Failed to publish annotated frame: {e}")

# ------------------ Main ------------------
def main(args=None):
    rclpy.init(args=args)
    node = YoloClusterHeadlessNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
