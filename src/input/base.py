"""
Input interface for sensor data sources.
"""

from abc import ABC, abstractmethod
from typing import Any


class Sensor(ABC):
    """
    Common sensor interface: init() -> get_data() in loop -> stop().

    get_data() return types by sensor:
      - camera: np.ndarray | None  (HxWx3 BGR, or None if no frame)
      - ultrasonic: float          (distance in cm)
      - encoders: tuple[int, int]  (left, right counts)
      - imu: float | None          (heading radians, or None)
    """

    @abstractmethod
    def init(self) -> None:
        """Initialize the sensor. Call before get_data()."""
        ...

    @abstractmethod
    def get_data(self) -> Any:
        """Get latest sensor reading. Return type varies by sensor (see class docstring)."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Release resources. Call when done."""
        ...


