"""
Ultrasonic sensor (real) — hardware stub.
"""

from input.base import Sensor


class UltrasonicReal(Sensor):
    """Placeholder for real ultrasonic hardware."""

    def init(self) -> None:
        pass

    def get_data(self) -> float:
        raise NotImplementedError("UltrasonicReal.get_data() not implemented yet")

    def stop(self) -> None:
        pass
