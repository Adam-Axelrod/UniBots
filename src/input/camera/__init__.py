"""
Camera sensors. Creators branch on INPUT_MODE internally.
"""

from brain.config import Config
from input.base import Sensor

from input.camera.mjpeg import PiMJPEGCamera
from input.camera.placeholder import PlaceholderCamera
from input.camera.unity import UnityTCPCamera


def create_front_camera(cfg: Config) -> Sensor:
    if cfg.INPUT_MODE == "sim":
        return UnityTCPCamera(
            cfg.UNITY_FRONT_HOST,
            cfg.UNITY_FRONT_PORT,
            cfg.UNITY_WIDTH,
            cfg.UNITY_HEIGHT,
            cfg.UNITY_FRAME_QUEUE_MAXSIZE,
            name="camera_front",
        )
    return PiMJPEGCamera(cfg.PI_FRONT_URL, name="camera_front")


def create_rear_camera(cfg: Config) -> Sensor:
    if cfg.INPUT_MODE == "sim":
        # Placeholder until Unity supports dual streams
        return PlaceholderCamera(cfg.UNITY_WIDTH, cfg.UNITY_HEIGHT, name="camera_rear")
    return PiMJPEGCamera(cfg.PI_REAR_URL, name="camera_rear")
