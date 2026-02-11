"""
Pi MJPEG camera (real).
"""

import cv2
import numpy as np

from input.base import Sensor


class PiMJPEGCamera(Sensor):
    """Frames from Pi (or any) MJPEG stream over HTTP."""

    def __init__(self, stream_url: str, name: str = "camera"):
        self._stream_url = stream_url
        self._name = name
        self._cap: cv2.VideoCapture | None = None

    def init(self) -> None:
        self._cap = cv2.VideoCapture(self._stream_url)
        if not self._cap.isOpened():
            raise RuntimeError(f"Failed to open video stream: {self._stream_url}")
        print(f"[Camera] Pi video stream opened: {self._stream_url}")

    def get_data(self) -> np.ndarray | None:
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        return frame if ret else None

    def stop(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None
