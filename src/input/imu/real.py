"""
IMU sensor (real) — hardware stub.
"""

from input.base import Sensor


class IMUReal(Sensor):
    """Placeholder for real IMU hardware."""

    def init(self) -> None:
        pass

    def get_data(self) -> float | None:
        raise NotImplementedError("IMUReal.get_data() not implemented yet")

    def stop(self) -> None:
        pass
