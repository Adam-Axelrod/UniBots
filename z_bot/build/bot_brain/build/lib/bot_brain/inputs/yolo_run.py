#!/usr/bin/env python3
import os
import time
import threading
from typing import List, Tuple

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge

import cv2
from ultralytics import YOLO


def cluster_by_distance(pts: List[Tuple[float, float]], dist_thresh: float) -> List[List[int]]:
    """
    Cluster 2D points using a simple BFS/graph approach:
    points are in the same cluster if they are within dist_thresh of ANY point in that cluster.

    Returns clusters as lists of indices into pts.

    Complexity is O(n^2) which is fine because n = #balls is small.
    """
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
    sx = 0.0
    sy = 0.0
    for i in idxs:
        sx += pts[i][0]
        sy += pts[i][1]
    return sx / len(idxs), sy / len(idxs)


class YoloClusterNode(Node):
    """
    Subscribes to one camera topic, runs YOLO at a controlled rate,
    clusters detected ball centers in 2D, and publishes the major cluster guidance.

    Subscribes:
      - image_topic (default: /image_raw) sensor_msgs/Image

    Publishes:
      - /ball/cluster (std_msgs/Float32MultiArray)
          [] if no detections
          otherwise:
          [
            major_side,      # -1 left, 0 centered, +1 right
            major_cx,        # cluster centroid x (pixels in resized frame)
            major_cy,        # cluster centroid y
            major_count,     # balls in the major cluster
            num_clusters     # total clusters found
          ]

      - /yolo/annotated (sensor_msgs/Image) optional
        Draws:
          - bounding boxes
          - midline
          - cluster centroids with counts
          - highlight major cluster centroid
    """

    def __init__(self):
        super().__init__('yolo_cluster_node')

        # ---------- Parameters ----------
        self.declare_parameter('image_topic', '/image_raw')
        self.declare_parameter('model_path', 'last.pt')

        self.declare_parameter('target_width', 320)
        self.declare_parameter('target_height', 240)
        self.declare_parameter('fps', 5.0)

        # YOLO parameters
        self.declare_parameter('conf', 0.25)
        self.declare_parameter('iou', 0.45)
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('imgsz', 256)
        self.declare_parameter('class_id', 0)
        self.declare_parameter('max_det', 50)

        # Clustering parameters (IMPORTANT)
        # base minimum distance threshold in pixels
        self.declare_parameter('cluster_dist_px', 45.0)
        # adaptive scaling using median bbox width (dist = max(base, scale*median_bbox_width))
        self.declare_parameter('cluster_dist_scale', 1.8)
        # ignore clusters smaller than this many balls
        self.declare_parameter('min_cluster_size', 1)
        # treat as centered if within this many pixels of midline
        self.declare_parameter('center_deadband_px', 12.0)

        # Annotated output
        self.declare_parameter('publish_annotated', True)
        self.declare_parameter('annotated_topic', '/yolo/annotated')
        self.declare_parameter('frame_id', 'camera')

        self.declare_parameter('show_window', False)
        self.declare_parameter('window_name', 'YOLO Cluster')

        # Thread limits help on Pi sometimes
        self.declare_parameter('torch_threads', 2)

        # ---------- Read parameters ----------
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

        self.cluster_dist_px = float(self.get_parameter('cluster_dist_px').value)
        self.cluster_dist_scale = float(self.get_parameter('cluster_dist_scale').value)
        self.min_cluster_size = int(self.get_parameter('min_cluster_size').value)
        self.center_deadband_px = float(self.get_parameter('center_deadband_px').value)

        self.publish_annotated = bool(self.get_parameter('publish_annotated').value)
        self.annotated_topic = str(self.get_parameter('annotated_topic').value)
        self.frame_id = str(self.get_parameter('frame_id').value)

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

        self.cluster_pub = self.create_publisher(Float32MultiArray, '/ball/cluster', 10)

        self.ann_pub = None
        if self.publish_annotated:
            self.ann_pub = self.create_publisher(Image, self.annotated_topic, 10)

        # ---------- Frame handling ----------
        self._lock = threading.Lock()
        self._latest_frame = None

        period = 1.0 / max(self.fps, 0.1)
        self.timer = self.create_timer(period, self.process_latest)

        self.get_logger().info(
            f"Sub: {self.image_topic} | YOLO {self.fps} Hz | Resize {self.tw}x{self.th} | imgsz={self.imgsz} | conf={self.conf} | "
            f"cluster_dist_px={self.cluster_dist_px} | scale={self.cluster_dist_scale} | deadband={self.center_deadband_px}"
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
            frame = self._latest_frame

        frame_small = cv2.resize(frame, (self.tw, self.th), interpolation=cv2.INTER_AREA)

        t0 = time.time()
        results = self.model.predict(
            source=frame_small,
            imgsz=self.imgsz,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False,
            classes=[self.class_id],
            max_det=self.max_det
        )
        dt = time.time() - t0
        inf_fps = (1.0 / dt) if dt > 0 else 0.0

        annotated = frame_small.copy()
        h, w = annotated.shape[:2]
        mid = w // 2

        # Draw midline (red)
        cv2.line(annotated, (mid, 0), (mid, h - 1), (0, 0, 255), 2)

        # Collect detections
        centers: List[Tuple[float, float]] = []  # (bx, by)
        bbox_widths: List[float] = []
        boxes_to_draw: List[Tuple[int, int, int, int, float]] = []  # x1,y1,x2,y2,conf

        if len(results) > 0:
            r = results[0]
            if r.boxes is not None and len(r.boxes) > 0:
                for b in r.boxes:
                    conf = float(b.conf[0].item()) if b.conf is not None else 0.0
                    x1, y1, x2, y2 = b.xyxy[0].tolist()
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                    bx = (x1 + x2) / 2.0
                    by = (y1 + y2) / 2.0

                    centers.append((bx, by))
                    bbox_widths.append(float(max(1, x2 - x1)))
                    boxes_to_draw.append((x1, y1, x2, y2, conf))

        # Adaptive cluster threshold based on median bbox width (helps across distances)
        if bbox_widths:
            bw_sorted = sorted(bbox_widths)
            med_w = bw_sorted[len(bw_sorted) // 2]
            dist_thresh = max(self.cluster_dist_px, self.cluster_dist_scale * med_w)
        else:
            dist_thresh = self.cluster_dist_px

        # Cluster 2D centers
        cluster_indices = cluster_by_distance(centers, dist_thresh)

        # Filter small clusters
        cluster_indices = [idxs for idxs in cluster_indices if len(idxs) >= self.min_cluster_size]

        # Compute cluster centroids and pick major (biggest, tie-break by closeness to midline)
        # store: (size, abs(cx-mid), cx, cy)
        cluster_infos: List[Tuple[int, float, float, float]] = []
        for idxs in cluster_indices:
            cx, cy = cluster_centroid(centers, idxs)
            cluster_infos.append((len(idxs), abs(cx - mid), cx, cy))

        major = None
        for info in cluster_infos:
            if major is None:
                major = info
            else:
                # bigger wins; tie-break closer to midline
                if info[0] > major[0] or (info[0] == major[0] and info[1] < major[1]):
                    major = info

        # Publish cluster guidance
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

            msg.data = [
                float(major_side),
                float(major_cx),
                float(major_cy),
                float(major_count),
                float(len(cluster_infos)),
            ]

        self.cluster_pub.publish(msg)

        # ----- Draw annotations -----
        # Draw boxes and centers
        for (x1, y1, x2, y2, conf) in boxes_to_draw:
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            bx = int((x1 + x2) // 2)
            by = int((y1 + y2) // 2)
            cv2.circle(annotated, (bx, by), 3, (0, 255, 255), -1)
            cv2.putText(
                annotated, f"{conf:.2f}",
                (x1, max(0, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (0, 255, 0), 1, cv2.LINE_AA
            )

        # Draw cluster centroids
        for (size, _, cx, cy) in cluster_infos:
            cx_i = int(cx)
            cy_i = int(cy)
            cv2.circle(annotated, (cx_i, cy_i), 10, (255, 255, 0), 2)
            cv2.putText(
                annotated, f"C{size}",
                (max(0, cx_i - 10), max(0, cy_i - 12)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 0), 2, cv2.LINE_AA
            )

        # Highlight major centroid
        if major is not None:
            _, _, mcx, mcy = major
            cv2.circle(annotated, (int(mcx), int(mcy)), 14, (255, 0, 0), 2)
            cv2.putText(
                annotated, "MAJOR",
                (max(0, int(mcx) - 30), max(0, int(mcy) - 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 0, 0), 2, cv2.LINE_AA
            )

        # Overlay status text
        cv2.putText(
            annotated,
            f"Infer: {inf_fps:.1f} FPS  balls={len(centers)} clusters={len(cluster_infos)} thr={dist_thresh:.0f}px",
            (8, 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            (255, 255, 255), 2, cv2.LINE_AA
        )

        if self.ann_pub is not None:
            try:
                out = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
                out.header.stamp = self.get_clock().now().to_msg()
                out.header.frame_id = self.frame_id
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
    node = YoloClusterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
