"""
Motor controller (sim) — sends commands to Unity over TCP when unity_conn provided.
"""

from brain.command import MotorDirection, motor_direction_to_sim_str
from input.unity_sim_connection import UnitySimConnection
from output.base import Actuator


class MotorControllerSim(Actuator):
    """Sim motor controller. Sends STOP/FORWARD/REVERSE/LEFT/RIGHT to Unity when unity_conn set."""

    def __init__(self, unity_conn: UnitySimConnection | None = None):
        self._unity_conn = unity_conn

    def init(self) -> None:
        pass

    def set_direction(self, direction: MotorDirection) -> None:
        if self._unity_conn is not None:
            cmd_str = motor_direction_to_sim_str(direction)
            self._unity_conn.send_command(cmd_str)

    def stop(self) -> None:
        pass
