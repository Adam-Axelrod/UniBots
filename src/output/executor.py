"""
Executor: executes Command from brain on hardware.
"""

from brain.command import Command


class Executor:
    """Dispatches Command to motor, speaker, (and drop_mechanism when available)."""

    def __init__(
        self,
        motor,
        speaker,
        drop_mechanism=None,
    ):
        self._motor = motor
        self._speaker = speaker
        self._drop = drop_mechanism

    def execute(self, cmd: Command) -> None:
        self._motor.drive(cmd.motor_left, cmd.motor_right)
        if cmd.beep:
            self._speaker.beep()
        if cmd.drop and self._drop:
            self._drop.drop_all()
