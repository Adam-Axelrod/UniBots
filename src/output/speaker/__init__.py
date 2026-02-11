"""
Speaker. Creator branches on ACTUATOR_MODE internally.
"""

from brain.config import Config
from output.base import Actuator

from output.speaker.real import SpeakerReal
from output.speaker.sim import SpeakerSim


def create_speaker(cfg: Config) -> Actuator:
    if cfg.ACTUATOR_MODE == "sim":
        return SpeakerSim()
    return SpeakerReal()
