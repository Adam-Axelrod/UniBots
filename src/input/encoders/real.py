"""
Encoder sensor (real) — hardware stub.
"""

from input.base import Sensor


class EncodersReal(Sensor):
    """Placeholder for real encoder hardware."""

    def init(self) -> None:
        pass

    def get_data(self) -> tuple[int, int]:
        raise NotImplementedError("EncodersReal.get_data() not implemented yet")

    def stop(self) -> None:
        pass
