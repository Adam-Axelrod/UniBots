"""
Process layer: VisionModule (YOLO ball detection, PyTorch or NCNN) + Annotator (debug drawings).
No I/O, same for sim and real.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class DebugInfo:
    """Debug overlay data. Cheap to construct, no heavy compute."""

    state_name: str
    cmd_str: str
    fps: float
    loop_time_ms: float
    ball_count: int = 0
    time_remaining: float = 0.0


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


def format_cmd(motor_left: float, motor_right: float, beep: bool, drop: bool) -> str:
    """Compact command string for overlay."""
    parts = []
    if beep:
        parts.append("BEEP")
    if drop:
        parts.append("DROP")
    if not parts:
        parts.append(f"L:{motor_left:.2f} R:{motor_right:.2f}")
    return " ".join(parts)


class Annotator:
    """Draws path, markers, and debug overlay on frame."""

    def __call__(
        self,
        frame: np.ndarray,
        path: list[tuple[int, int]],
        camera_point: tuple[int, int],
        debug: DebugInfo,
    ) -> np.ndarray:
        """Draw path, target highlight, and debug overlay."""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        target = path[0] if path else None

        # Balls: red circles; target ball: thick cyan ring + label
        for i, (cx, cy) in enumerate(path):
            is_target = (cx, cy) == target
            if is_target:
                cv2.circle(annotated, (cx, cy), 12, (255, 255, 0), 3)  # cyan ring
                cv2.circle(annotated, (cx, cy), 6, (255, 255, 0), -1)
                cv2.putText(
                    annotated,
                    "TARGET",
                    (cx - 28, cy - 18),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 255, 0),
                    1,
                )
            else:
                cv2.circle(annotated, (cx, cy), 4, (0, 0, 255), -1)

        if len(path) >= 2:
            for i in range(len(path) - 1):
                cv2.line(annotated, path[i], path[i + 1], (0, 255, 0), 2)
        cv2.circle(annotated, camera_point, 6, (255, 255, 255), -1)

        # Top-left: state, command
        y0, dy = 22, 20
        cv2.putText(
            annotated,
            f"State: {debug.state_name}",
            (8, y0),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
        )
        cv2.putText(
            annotated,
            f"Cmd: {debug.cmd_str}",
            (8, y0 + dy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 200),
            1,
        )

        # Top-right: FPS, loop time
        fps_text = f"FPS: {debug.fps:.1f}"
        loop_text = f"Loop: {debug.loop_time_ms:.0f}ms"
        cv2.putText(
            annotated,
            fps_text,
            (w - 95, y0),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
        )
        cv2.putText(
            annotated,
            loop_text,
            (w - 95, y0 + dy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
        )

        # Bottom-left: balls, time remaining
        if debug.ball_count > 0 or debug.time_remaining > 0:
            cv2.putText(
                annotated,
                f"Balls: {debug.ball_count} | t: {debug.time_remaining:.0f}s",
                (8, h - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (180, 180, 180),
                1,
            )

        return annotated
