"""
Ultrasonic sensor (sim) — mock readings.
"""

from input.base import Sensor


class UltrasonicSim(Sensor):
    """Mock ultrasonic returning constant distance."""

    def __init__(self, default_cm: float = 0.0):
        self._default_cm = default_cm

    def init(self) -> None:
        pass

    def get_data(self) -> float:
        return self._default_cm

    def stop(self) -> None:
        pass
