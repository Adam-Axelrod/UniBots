"""
Motor controller (real) — hardware stub.
"""

from brain.command import MotorDirection
from output.base import Actuator


class MotorControllerReal(Actuator):
    """Placeholder for real motor hardware. Wiring TBD."""

    def init(self) -> None:
        pass

    def set_direction(self, direction: MotorDirection) -> None:
        # Stub: actual GPIO/relay wiring TBD
        # FORWARD: both motors forward
        # REVERSE: both motors reverse
        # LEFT: left reverse, right forward
        # RIGHT: left forward, right reverse
        pass

    def stop(self) -> None:
        pass
