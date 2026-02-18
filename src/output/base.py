"""
Output interface for actuators (motor, speaker).
"""

from abc import ABC, abstractmethod


class Actuator(ABC):
    """
    Base for motor, speaker. init() -> commands in loop -> stop().

    Method return types by actuator:
      - motor: set_direction(direction: MotorDirection) -> None
      - speaker: beep() -> None
    """

    @abstractmethod
    def init(self) -> None:
        """Initialize the actuator. Call before set_direction/beep."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Release resources. Call when done."""
        ...
