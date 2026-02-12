"""
Command: brain's decision, executed by output layer.
"""

from dataclasses import dataclass


@dataclass
class Command:
    """Output command from brain."""

    motor_left: float = 0.0
    motor_right: float = 0.0
    beep: bool = False
    drop: bool = False
