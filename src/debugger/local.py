"""
Local display frame sink using OpenCV.
"""

import cv2
import numpy as np

from debugger.base import FrameSink


class LocalDisplaySink(FrameSink):
    """Show annotated frame in local cv2 window. send() returns True on 'q'."""

    def __init__(self, window_name: str):
        self._window_name = window_name

    def start(self) -> None:
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)

    def send(self, frame: np.ndarray) -> bool:
        h, w = frame.shape[:2]
        cv2.resizeWindow(self._window_name, w, h)
        cv2.imshow(self._window_name, frame)
        return (cv2.waitKey(1) & 0xFF) == ord("q")

    def close(self) -> None:
        cv2.destroyAllWindows()
