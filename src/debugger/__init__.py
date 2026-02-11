"""
Debugger: annotated frame viewing for development.
"""

from brain.config import Config
from debugger.base import FrameSink

from debugger.local import LocalDisplaySink
from debugger.tcp import TCPStreamSink


def create_frame_sink(cfg: Config) -> FrameSink:
    """Create frame sink. Branches on HEADLESS internally."""
    if cfg.HEADLESS:
        return TCPStreamSink(
            cfg.STREAM_VIEWER_PORT,
            cfg.STREAM_SEND_EVERY_N_FRAMES,
            cfg.JPEG_QUALITY,
        )
    return LocalDisplaySink(cfg.WINDOW_NAME)
