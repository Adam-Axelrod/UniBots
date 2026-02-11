"""
IMU sensor (sim) — mock heading.
"""

from input.base import Sensor


class IMUSim(Sensor):
    """Mock IMU returning constant heading."""

    def __init__(self, default_heading: float = 0.0):
        self._default_heading = default_heading

    def init(self) -> None:
        pass

    def get_data(self) -> float | None:
        return self._default_heading

    def stop(self) -> None:
        pass
