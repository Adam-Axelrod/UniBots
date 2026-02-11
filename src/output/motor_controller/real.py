"""
Motor controller (real) — hardware stub.
"""

from output.base import Actuator


class MotorControllerReal(Actuator):
    """Placeholder for real motor hardware."""

    def init(self) -> None:
        pass

    def drive(self, left_speed: float, right_speed: float) -> None:
        raise NotImplementedError("MotorControllerReal.drive() not implemented yet")

    def stop(self) -> None:
        pass
