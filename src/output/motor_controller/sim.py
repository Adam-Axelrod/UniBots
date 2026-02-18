"""
Motor controller (sim) — no-op set_direction.
"""

from brain.command import MotorDirection
from output.base import Actuator


class MotorControllerSim(Actuator):
    """Sim motor controller. set_direction() is a no-op."""

    def init(self) -> None:
        pass

    def set_direction(self, direction: MotorDirection) -> None:
        pass

    def stop(self) -> None:
        pass
