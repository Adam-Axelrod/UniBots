"""
Ultrasonic sensor (sim) — mock readings and Unity connection.
"""

from input.base import Sensor
from input.unity_sim_connection import UnitySimConnection


class UltrasonicSimFromConnection(Sensor):
    """Ultrasonic reading from Unity sim (distance sent before each frame)."""

    def __init__(self, connection: UnitySimConnection):
        self._conn = connection

    def init(self) -> None:
        pass

    def get_data(self) -> float:
        return self._conn.get_distance_cm()

    def stop(self) -> None:
        pass


class UltrasonicSim(Sensor):
    """Mock ultrasonic returning constant distance."""

    def __init__(self, default_cm: float = 0.0):
        self._default_cm = default_cm

    def init(self) -> None:
        pass

    def get_data(self) -> float:
        return self._default_cm

    def stop(self) -> None:
        pass
