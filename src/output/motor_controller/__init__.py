"""
Motor controller. Creator branches on ACTUATOR_MODE internally.
"""

from brain.config import Config
from output.base import Actuator

from output.motor_controller.real import MotorControllerReal
from output.motor_controller.sim import MotorControllerSim


def create_motor_controller(cfg: Config) -> Actuator:
    if cfg.ACTUATOR_MODE == "sim":
        return MotorControllerSim()
    return MotorControllerReal()
