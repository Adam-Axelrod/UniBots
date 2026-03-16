"""
Motor controller. Creator branches on ACTUATOR_MODE internally.
"""

from brain.config import Config
from input.unity_sim_connection import UnitySimConnection
from output.base import Actuator

from output.motor_controller.real import MotorControllerReal
from output.motor_controller.sim import MotorControllerSim


def create_motor_controller(
    cfg: Config,
    unity_conn: UnitySimConnection | None = None,
) -> Actuator:
    if cfg.ACTUATOR_MODE == "sim":
        return MotorControllerSim(unity_conn=unity_conn)
    return MotorControllerReal()
