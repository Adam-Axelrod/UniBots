"""
Loads configuration from src/config.yaml.
"""

import os
from dataclasses import dataclass

import yaml

_BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.abspath(os.path.join(_BRAIN_DIR, ".."))
_ROOT_DIR = os.path.abspath(os.path.join(_SRC_DIR, ".."))
_DEFAULT_CONFIG_PATH = os.path.join(_SRC_DIR, "config.yaml")


def _resolve_model_path(raw_path: str) -> str:
    """Resolve model path: if relative, check brain dir, src dir, then project root."""
    if os.path.isabs(raw_path):
        return raw_path
    candidates = [
        os.path.join(_BRAIN_DIR, raw_path),
        os.path.join(_SRC_DIR, raw_path),
        os.path.join(_ROOT_DIR, raw_path),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


@dataclass
class Config:
    """Runtime configuration loaded from YAML."""

    # Input
    INPUT_MODE: str = "sim"  # "sim" or "real"; used by sensor creators
    PI_IP: str = "127.0.0.1"
    STREAM_URL: str = ""

    # Frame (model input size; both sim and real resize to this)
    FRAME_WIDTH: int = 256
    FRAME_HEIGHT: int = 256

    # Unity (sim cameras)
    UNITY_PORT: int = 6000
    UNITY_FRONT_HOST: str = "127.0.0.1"
    UNITY_FRONT_PORT: int = 6000
    UNITY_REAR_PORT: int = 6002
    UNITY_FRAME_QUEUE_MAXSIZE: int = 3

    # Cameras (real)
    PI_FRONT_URL: str = ""
    PI_REAR_URL: str = ""

    # IMU
    USE_IMU: bool = False

    # Model
    MODEL_PATH: str = "model/yolo11n_ncnn_model"
    CONF_THRESHOLD: float = 0.5

    # Actuators (motor, speaker)
    ACTUATOR_MODE: str = "sim"  # "sim" or "real"; used by actuator creators

    # Output / Debug (frame sink)
    HEADLESS: bool = True
    STREAM_VIEWER_PORT: int = 6001
    STREAM_SEND_EVERY_N_FRAMES: int = 2
    JPEG_QUALITY: int = 85
    WINDOW_NAME: str = "YOLO Ping Pong Greedy Path"

    def __post_init__(self):
        self.STREAM_URL = self.STREAM_URL or f"http://{self.PI_IP}:8080/?action=stream"
        self.PI_FRONT_URL = self.PI_FRONT_URL or self.STREAM_URL
        self.PI_REAR_URL = (
            self.PI_REAR_URL or f"http://{self.PI_IP}:8081/?action=stream"
        )
        self.MODEL_PATH = _resolve_model_path(self.MODEL_PATH)


def load_config(path: str | None = None) -> Config:
    """Load Config from YAML file. Falls back to defaults if file not found."""
    config_path = path or _DEFAULT_CONFIG_PATH

    if not os.path.exists(config_path):
        print(f"[Config] {config_path} not found, using defaults")
        return Config()

    with open(config_path, "r") as f:
        raw = yaml.safe_load(f) or {}

    print(f"[Config] Loaded from {config_path}")

    return Config(
        INPUT_MODE=raw.get("input_mode", "sim"),
        FRAME_WIDTH=raw.get("frame_width", 256),
        FRAME_HEIGHT=raw.get("frame_height", 256),
        PI_IP=raw.get("pi_ip", "127.0.0.1"),
        STREAM_URL=raw.get("stream_url", ""),
        UNITY_PORT=raw.get("unity_port", 6000),
        UNITY_FRONT_HOST=raw.get("unity_front_host")
        or raw.get("unity_host", "127.0.0.1"),
        UNITY_FRONT_PORT=raw.get("unity_front_port", raw.get("unity_port", 6000)),
        UNITY_REAR_PORT=raw.get("unity_rear_port", 6002),
        UNITY_FRAME_QUEUE_MAXSIZE=raw.get("unity_frame_queue_maxsize", 3),
        PI_FRONT_URL=raw.get("pi_front_url", ""),
        PI_REAR_URL=raw.get("pi_rear_url", ""),
        USE_IMU=raw.get("use_imu", False),
        MODEL_PATH=raw.get("model_path", "model/yolo11n_ncnn_model"),
        CONF_THRESHOLD=raw.get("conf_threshold", 0.5),
        ACTUATOR_MODE=raw.get("actuator_mode", "sim"),
        HEADLESS=raw.get("headless", True),
        STREAM_VIEWER_PORT=raw.get("stream_viewer_port", 6001),
        STREAM_SEND_EVERY_N_FRAMES=raw.get("stream_send_every_n_frames", 2),
        JPEG_QUALITY=raw.get("jpeg_quality", 85),
        WINDOW_NAME=raw.get("window_name", "YOLO Ping Pong Greedy Path"),
    )
