"""
IMU sensor. Creator branches on INPUT_MODE internally. Returns None if USE_IMU is False.
"""

from brain.config import Config
from input.base import Sensor

from input.imu.real import IMUReal
from input.imu.sim import IMUSim


def create_imu(cfg: Config) -> Sensor | None:
    if not cfg.USE_IMU:
        return None
    if cfg.INPUT_MODE == "sim":
        return IMUSim(default_heading=0.0)
    return IMUReal()
