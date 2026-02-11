"""
Motor controller (sim) — no-op drive.
"""

from output.base import Actuator


class MotorControllerSim(Actuator):
    """Sim motor controller. drive() is a no-op."""

    def init(self) -> None:
        pass

    def drive(self, left_speed: float, right_speed: float) -> None:
        pass

    def stop(self) -> None:
        pass
