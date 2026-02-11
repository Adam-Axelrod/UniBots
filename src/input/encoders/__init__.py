"""
Encoder sensors. Creator branches on INPUT_MODE internally.
"""

from brain.config import Config
from input.base import Sensor

from input.encoders.real import EncodersReal
from input.encoders.sim import EncodersSim


def create_encoders(cfg: Config) -> Sensor:
    if cfg.INPUT_MODE == "sim":
        return EncodersSim()
    return EncodersReal()
