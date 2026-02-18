"""
Camera sensors. Creators branch on INPUT_MODE internally.
"""

from brain.config import Config
from input.base import Sensor
from input.unity_sim_connection import UnitySimConnection

from input.camera.mjpeg import PiMJPEGCamera
from input.camera.placeholder import PlaceholderCamera
from input.camera.sim import UnityTCPCamera


def create_front_camera(
    cfg: Config,
    unity_conn: UnitySimConnection | None = None,
) -> Sensor:
    if cfg.INPUT_MODE == "sim":
        if unity_conn is None:
            raise ValueError("unity_conn required when INPUT_MODE is sim")
        return UnityTCPCamera(
            unity_conn,
            cfg.FRAME_WIDTH,
            cfg.FRAME_HEIGHT,
            cfg.UNITY_FRAME_QUEUE_MAXSIZE,
            name="camera_front",
        )
    return PiMJPEGCamera(cfg.PI_FRONT_URL, name="camera_front")


def create_rear_camera(cfg: Config) -> Sensor:
    if cfg.INPUT_MODE == "sim":
        # Placeholder until Unity supports dual streams
        return PlaceholderCamera(cfg.FRAME_WIDTH, cfg.FRAME_HEIGHT, name="camera_rear")
    return PiMJPEGCamera(cfg.PI_REAR_URL, name="camera_rear")
