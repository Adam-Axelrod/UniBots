"""
Encoder sensor (sim) — mock readings.
"""

from input.base import Sensor


class EncodersSim(Sensor):
    """Mock encoders returning zeros."""

    def init(self) -> None:
        pass

    def get_data(self) -> tuple[int, int]:
        return (0, 0)

    def stop(self) -> None:
        pass
