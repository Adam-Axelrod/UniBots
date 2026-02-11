"""
Placeholder camera (black frame) when a stream is not yet available.
"""

import numpy as np

from input.base import Sensor


class PlaceholderCamera(Sensor):
    """Returns black frames. Used for rear camera until Unity supports dual streams."""

    def __init__(self, width: int = 256, height: int = 256, name: str = "camera"):
        self._width = width
        self._height = height
        self._name = name

    def init(self) -> None:
        pass

    def get_data(self) -> np.ndarray:
        return np.zeros((self._height, self._width, 3), dtype=np.uint8)

    def stop(self) -> None:
        pass
