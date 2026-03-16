"""
Ultrasonic sensor. Creator branches on INPUT_MODE internally.
"""

from brain.config import Config
from input.base import Sensor
from input.unity_sim_connection import UnitySimConnection

from input.ultrasonic.real import UltrasonicReal
from input.ultrasonic.sim import UltrasonicSim, UltrasonicSimFromConnection


def create_ultrasonic(
    cfg: Config, unity_conn: UnitySimConnection | None = None
) -> Sensor:
    if cfg.INPUT_MODE == "sim":
        if unity_conn is not None:
            return UltrasonicSimFromConnection(unity_conn)
        return UltrasonicSim(default_cm=0.0)
    return UltrasonicReal()
