"""
Ultrasonic sensor. Creator branches on INPUT_MODE internally.
"""

from brain.config import Config
from input.base import Sensor

from input.ultrasonic.real import UltrasonicReal
from input.ultrasonic.sim import UltrasonicSim


def create_ultrasonic(cfg: Config) -> Sensor:
    if cfg.INPUT_MODE == "sim":
        return UltrasonicSim(default_cm=0.0)
    return UltrasonicReal()
