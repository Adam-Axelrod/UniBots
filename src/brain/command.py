"""
Command: brain's decision, executed by output layer.
"""

from dataclasses import dataclass
from enum import Enum, auto


class MotorDirection(Enum):
    """Switch-based motor control. Only one active at a time, or STOP."""

    STOP = auto()
    FORWARD = auto()
    REVERSE = auto()
    LEFT = auto()
    RIGHT = auto()


def motor_direction_to_sim_str(d: MotorDirection) -> str:
    """Map MotorDirection to Unity protocol strings: STOP, FORWARD, REVERSE, LEFT, RIGHT."""
    return d.name


@dataclass
class Command:
    """Output command from brain."""

    motor: MotorDirection = MotorDirection.STOP
    beep: bool = False
    drop: bool = False
