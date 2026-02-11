"""
Process layer: YOLO + path logic. No I/O, same for sim and real.
"""

import math

import cv2
import numpy as np
import torch
from ultralytics import YOLO


class ProcessPipeline:
    """Takes a frame, runs YOLO, draws path and annotations. Pure logic."""

    def __init__(self, model_path: str, conf_threshold: float, device: str | None = None):
        print("[Process] Loading YOLO model...")
        self._model = YOLO(model_path)
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(self._device)
        self._conf = conf_threshold
        print(f"[Process] Model loaded (device: {self._device})")

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        """Run inference and return annotated frame (boxes + path)."""
        h, w = frame.shape[:2]
        camera_point = (w // 2, h)

        results = self._model(frame, conf=self._conf, verbose=False)
        annotated = results[0].plot()

        centers = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            centers.append((cx, cy))

        for cx, cy in centers:
            cv2.circle(annotated, (cx, cy), 4, (0, 0, 255), -1)

        if len(centers) >= 1:
            remaining = centers.copy()
            path = []
            start = min(
                remaining,
                key=lambda p: math.hypot(p[0] - camera_point[0], p[1] - camera_point[1]),
            )
            path.append(start)
            remaining.remove(start)
            while remaining:
                last = path[-1]
                next_ball = min(
                    remaining,
                    key=lambda p: math.hypot(p[0] - last[0], p[1] - last[1]),
                )
                path.append(next_ball)
                remaining.remove(next_ball)
            for i in range(len(path) - 1):
                cv2.line(annotated, path[i], path[i + 1], (0, 255, 0), 2)
            cv2.circle(annotated, path[0], 7, (255, 0, 0), -1)
            cv2.circle(annotated, camera_point, 6, (255, 255, 255), -1)

        return annotated
