"""
Process layer: VisionModule (YOLO ball detection, PyTorch or NCNN).
No I/O, same for sim and real.
"""

import math
from pathlib import Path

import numpy as np
import torch
from ultralytics import YOLO


class VisionModule:
    """Runs YOLO on frame, returns ball centers for world model."""

    def __init__(
        self, model_path: str, conf_threshold: float, device: str | None = None
    ):
        print("[Vision] Loading YOLO model...")
        self._model = YOLO(model_path, task="detect")
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._conf = conf_threshold
        p = Path(model_path)
        is_pt = p.suffix == ".pt"
        if is_pt:
            self._model.to(self._device)
        # Eager warmup: trigger lazy backend load now so main loop doesn't block on first frame
        dummy = np.zeros((64, 64, 3), dtype=np.uint8)
        self._model(
            dummy, imgsz=320, conf=self._conf, device=self._device, verbose=False
        )
        print(f"[Vision] Model loaded ({'PyTorch' if is_pt else 'NCNN'}, device: {self._device})")

    def get_detections(
        self, frame: np.ndarray
    ) -> tuple[list[tuple[int, int]], np.ndarray]:
        """Run inference once. Returns (ball_centers, yolo_annotated_frame)."""
        results = self._model(
            frame,
            imgsz=320,
            conf=self._conf,
            device=self._device,
            verbose=False,
        )
        centers = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            centers.append((cx, cy))
        annotated = results[0].plot()
        return centers, annotated


def compute_path(
    ball_centers: list[tuple[int, int]],
    camera_point: tuple[int, int],
) -> list[tuple[int, int]]:
    """Greedy path: nearest to camera first, then nearest-neighbor. Called once per frame."""
    if not ball_centers:
        return []
    remaining = ball_centers.copy()
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
    return path


def format_cmd(motor, beep: bool, drop: bool) -> str:
    """Compact command string for overlay. motor is MotorDirection."""
    parts = []
    if beep:
        parts.append("BEEP")
    if drop:
        parts.append("DROP")
    if not parts:
        short = {"STOP": "STOP", "FORWARD": "FWD", "REVERSE": "REV", "LEFT": "L", "RIGHT": "R"}
        parts.append(short.get(motor.name, motor.name))
    return " ".join(parts)
